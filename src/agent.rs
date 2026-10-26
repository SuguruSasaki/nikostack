use std::path::Path;
use std::time::Duration;

use serde::Deserialize;
use serde_json::{Value, json};

use crate::domain::Model;
use crate::error::{Error, Result};
use crate::process::{Environment, Request, Runner};
use crate::state::atomic_json;

#[derive(Clone, Copy)]
pub(crate) enum Role {
    Implement,
    Repair,
    Review,
}
impl Role {
    fn name(self) -> &'static str {
        match self {
            Self::Implement => "implement",
            Self::Repair => "repair",
            Self::Review => "review",
        }
    }
    fn reviewer(self) -> bool {
        matches!(self, Self::Review)
    }
}

pub(crate) struct Task<'a> {
    pub work: &'a Path,
    pub evidence: &'a Path,
    pub prompt: &'a str,
    pub role: Role,
    pub model: Model,
}

pub(crate) trait Agent {
    fn ask(&self, task: Task<'_>) -> Result<Value>;
}

pub(crate) struct Claude<'a> {
    pub runner: &'a Runner,
}
impl Claude<'_> {
    pub(crate) fn check_subscription(&self, cwd: &Path) -> Result<()> {
        let mut request = Request::new("claude", cwd, ["auth", "status"]);
        request.environment = Environment::ClaudeSubscription;
        let status: Value = serde_json::from_str(&self.runner.run(request)?)?;
        if status["loggedIn"] != true || status["authMethod"] != "claude.ai" {
            return Err(Error::blocked(
                "Claude subscription login is required; no API-key fallback.",
            ));
        }
        Ok(())
    }
}
impl Agent for Claude<'_> {
    fn ask(&self, task: Task<'_>) -> Result<Value> {
        let reviewer = task.role.reviewer();
        let tools = if reviewer {
            "Read,Glob,Grep"
        } else {
            "Read,Glob,Grep,Edit,Write"
        };
        let schema = schema(reviewer).to_string();
        let mut request = Request::new(
            "claude",
            task.work,
            [
                "-p",
                "--model",
                task.model.name(),
                "--effort",
                if reviewer || task.model == Model::Haiku {
                    "low"
                } else {
                    "medium"
                },
                "--restricted",
                "--tools",
                tools,
                "--allowedTools",
                tools,
                "--permission-mode",
                if reviewer { "dontAsk" } else { "acceptEdits" },
                "--permission-prompts",
                "none",
                "--strict-mcp-config",
                "--mcp-config",
                "{\"mcpServers\":{}}",
                "--setting-sources",
                "",
                "--no-chrome",
                "--no-session-persistence",
                "--output-format",
                "json",
                "--max-turns",
                if reviewer { "12" } else { "24" },
                "--json-schema",
                &schema,
            ],
        );
        request.environment = Environment::ClaudeSubscription;
        request.timeout = Duration::from_secs(if reviewer { 600 } else { 1200 });
        request.input = Some(task.prompt.to_owned());
        request.log = Some(task.evidence.join(format!("{}.log", task.role.name())));
        let result: Value = serde_json::from_str(&self.runner.run(request)?)?;
        atomic_json(
            &task
                .evidence
                .join(format!("{}-usage.json", task.role.name())),
            &json!({
                "requested_model":task.model.name(),"model_usage":result["modelUsage"],
                "num_turns":result["num_turns"],"duration_ms":result["duration_ms"],
                "reported_api_equivalent_cost_usd":result["total_cost_usd"],
            }),
        )?;
        validate_result(&result, task.model, reviewer)
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct Build {
    pub status: BuildStatus,
    pub summary: String,
    pub manual_checks: Vec<String>,
}
#[derive(Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub(crate) enum BuildStatus {
    Ready,
    Blocked,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct Review {
    pub verdict: Verdict,
    pub summary: String,
    pub findings: Vec<String>,
}
#[derive(Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub(crate) enum Verdict {
    Pass,
    Fail,
    Blocked,
}

fn schema(reviewer: bool) -> Value {
    if reviewer {
        json!({
            "type":"object",
            "properties":{
                "verdict":{"type":"string","enum":["pass","fail","blocked"]},
                "summary":{"type":"string","description":"Overall review, positive observations, limitations, and remaining human checks."},
                "findings":{
                    "type":"array",
                    "description":"Only unresolved blocking defects. For verdict pass this MUST be an empty array. Do not list passed checks, positive observations, or non-blocking notes here.",
                    "items":{"type":"string"}
                }
            },
            "required":["verdict","summary","findings"],"additionalProperties":false
        })
    } else {
        json!({
            "type":"object","properties":{"status":{"type":"string","enum":["ready","blocked"]},"summary":{"type":"string"},"manual_checks":{"type":"array","items":{"type":"string"}}},
            "required":["status","summary","manual_checks"],"additionalProperties":false
        })
    }
}

fn validate_result(result: &Value, model: Model, reviewer: bool) -> Result<Value> {
    if result["is_error"] == true
        || result["permission_denials"]
            .as_array()
            .is_some_and(|items| !items.is_empty())
    {
        return Err(Error::blocked(
            "Claude failed or requested an unavailable permission.",
        ));
    }
    let usage = result["modelUsage"]
        .as_object()
        .filter(|usage| !usage.is_empty())
        .ok_or_else(|| {
            Error::blocked("Claude did not identify the model used; inspect the private log.")
        })?;
    if usage
        .keys()
        .any(|name| !name.to_ascii_lowercase().contains(model.name()))
    {
        return Err(Error::blocked(
            "Claude used an unexpected model; no further calls will be made.",
        ));
    }
    let data = result["structured_output"].clone();
    if reviewer {
        let review: Review = serde_json::from_value(data.clone())?;
        if review.verdict == Verdict::Pass && !review.findings.is_empty() {
            return Err(Error::blocked(
                "Review passed while listing unresolved findings.",
            ));
        }
    } else {
        let _: Build = serde_json::from_value(data.clone())?;
    }
    Ok(data)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn unexpected_model_and_contradictory_review_are_rejected() {
        let mut result = json!({"modelUsage":{"claude-sonnet":{}},"structured_output":{"verdict":"pass","summary":"ok","findings":[]}});
        assert!(validate_result(&result, Model::Haiku, true).is_err());
        assert!(validate_result(&result, Model::Sonnet, true).is_ok());
        result["structured_output"]["findings"] = json!(["unresolved"]);
        assert!(validate_result(&result, Model::Sonnet, true).is_err());
        result["structured_output"] =
            json!({"verdict":"pass","summary":"ok","findings":[],"extra":true});
        assert!(validate_result(&result, Model::Sonnet, true).is_err());
    }
}
