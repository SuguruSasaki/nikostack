use crate::error::{Error, Result};
use nix::sys::signal::{Signal, killpg};
use nix::unistd::Pid;
use std::ffi::OsString;
use std::io::{Read, Write};
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::{
    Arc,
    atomic::{AtomicBool, Ordering},
    mpsc,
};
use std::thread;
use std::time::{Duration, Instant};

const OUTPUT_LIMIT: u64 = 8 * 1024 * 1024;

#[derive(Clone, Copy, Default)]
pub(crate) enum Environment {
    #[default]
    Inherited,
    ClaudeSubscription,
}
pub(crate) struct Request<'a> {
    pub program: &'a str,
    pub args: Vec<OsString>,
    pub cwd: &'a Path,
    pub input: Option<String>,
    pub timeout: Duration,
    pub log: Option<PathBuf>,
    pub environment: Environment,
}
impl<'a> Request<'a> {
    pub(crate) fn new(
        program: &'a str,
        cwd: &'a Path,
        args: impl IntoIterator<Item = impl Into<OsString>>,
    ) -> Self {
        Self {
            program,
            args: args.into_iter().map(Into::into).collect(),
            cwd,
            input: None,
            timeout: Duration::from_secs(60),
            log: None,
            environment: Environment::Inherited,
        }
    }
}

#[derive(Clone, Default)]
pub(crate) struct Runner {
    pub stop: Arc<AtomicBool>,
}
impl Runner {
    pub(crate) fn command(&self, request: &Request<'_>) -> Command {
        let mut command = Command::new(request.program);
        command
            .args(&request.args)
            .current_dir(request.cwd)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .process_group(0);
        if matches!(request.environment, Environment::ClaudeSubscription) {
            for (name, _) in std::env::vars_os() {
                let text = name.to_string_lossy();
                if ["ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDECODE"]
                    .contains(&text.as_ref())
                    || text.starts_with("CLAUDE_CODE_USE_")
                {
                    command.env_remove(name);
                }
            }
            for (name, value) in [
                ("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "1"),
                ("DISABLE_TELEMETRY", "1"),
                ("DISABLE_ERROR_REPORTING", "1"),
                ("DO_NOT_TRACK", "1"),
                ("CLAUDE_CODE_ENABLE_TELEMETRY", "0"),
                ("CLAUDE_CODE_ENABLE_FEEDBACK_SURVEY_FOR_OTEL", "0"),
                ("ENABLE_BETA_TRACING_DETAILED", "0"),
                ("ENABLE_CLAUDEAI_MCP_SERVERS", "false"),
                ("CLAUDE_CODE_DISABLE_FAST_MODE", "1"),
            ] {
                command.env(name, value);
            }
        }
        command
    }

    pub(crate) fn run(&self, request: Request<'_>) -> Result<String> {
        if self.stop.load(Ordering::Relaxed) {
            return Err(Error::Interrupted);
        }
        let mut child = self.command(&request).spawn()?;
        let pid = i32::try_from(child.id())
            .map_err(|_| Error::blocked("Child process ID is out of range."))?;
        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| Error::blocked("Missing stdout pipe."))?;
        let stderr = child
            .stderr
            .take()
            .ok_or_else(|| Error::blocked("Missing stderr pipe."))?;
        let (out_tx, out_rx) = mpsc::channel();
        let (err_tx, err_rx) = mpsc::channel();
        for (pipe, sender) in [
            (Box::new(stdout) as Box<dyn Read + Send>, out_tx),
            (Box::new(stderr) as Box<dyn Read + Send>, err_tx),
        ] {
            thread::spawn(move || {
                let mut bytes = Vec::new();
                let result = pipe
                    .take(OUTPUT_LIMIT)
                    .read_to_end(&mut bytes)
                    .map(|_| bytes);
                let _ = sender.send(result);
            });
        }
        let stdin = child.stdin.take();
        let (in_tx, in_rx) = mpsc::channel();
        if let (Some(mut pipe), Some(input)) = (stdin, request.input.as_deref()) {
            let input = input.to_owned();
            thread::spawn(move || {
                let _ = in_tx.send(pipe.write_all(input.as_bytes()));
            });
        } else {
            let _ = in_tx.send(Ok(()));
        }
        let started = Instant::now();
        let (mut status, mut out, mut err, mut input) = (None, None, None, None);
        let mut stopped = false;
        loop {
            if status.is_none() {
                status = child.try_wait()?;
            }
            if out.is_none() {
                out = out_rx.try_recv().ok();
            }
            if err.is_none() {
                err = err_rx.try_recv().ok();
            }
            if input.is_none() {
                input = in_rx.try_recv().ok();
            }
            if status.is_some() && out.is_some() && err.is_some() && input.is_some() {
                break;
            }
            if self.stop.load(Ordering::Relaxed) || started.elapsed() >= request.timeout {
                stopped = true;
                // The group was created for this request; no shell or caller-supplied PID.
                let _ = killpg(Pid::from_raw(pid), Signal::SIGTERM);
                thread::sleep(Duration::from_millis(150));
                let _ = killpg(Pid::from_raw(pid), Signal::SIGKILL);
                let _ = child.kill();
                status = Some(child.wait()?);
                if out.is_none() {
                    out = out_rx.recv_timeout(Duration::from_millis(300)).ok();
                }
                if err.is_none() {
                    err = err_rx.recv_timeout(Duration::from_millis(300)).ok();
                }
                break;
            }
            thread::sleep(Duration::from_millis(20));
        }
        let out = out.transpose()?.unwrap_or_default();
        let err = err.transpose()?.unwrap_or_default();
        let stdout = String::from_utf8_lossy(&out).into_owned();
        if let Some(path) = request.log {
            crate::state::write_private(
                &path,
                format!(
                    "{stdout}\n--- stderr ---\n{}",
                    String::from_utf8_lossy(&err)
                )
                .as_bytes(),
            )?;
        }
        if stopped {
            return Err(if self.stop.load(Ordering::Relaxed) {
                Error::Interrupted
            } else {
                Error::blocked(format!(
                    "Command timed out: {}",
                    program_name(request.program)
                ))
            });
        }
        input.transpose()?;
        if out.len() as u64 >= OUTPUT_LIMIT || err.len() as u64 >= OUTPUT_LIMIT {
            return Err(Error::blocked(
                "Command output exceeded the evidence budget.",
            ));
        }
        if !status.is_some_and(|status| status.success()) {
            return Err(Error::blocked(format!(
                "Command failed: {}",
                program_name(request.program)
            )));
        }
        Ok(stdout)
    }
}

fn program_name(program: &str) -> String {
    Path::new(program)
        .file_name()
        .unwrap_or_default()
        .to_string_lossy()
        .into_owned()
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn child_telemetry_controls_do_not_change_parent_environment() {
        let runner = Runner::default();
        let before = std::env::var_os("DISABLE_TELEMETRY");
        let mut request = Request::new("claude", Path::new("."), ["--help"]);
        request.environment = Environment::ClaudeSubscription;
        let command = runner.command(&request);
        let env: std::collections::BTreeMap<_, _> = command.get_envs().collect();
        assert_eq!(
            env.get(std::ffi::OsStr::new("DISABLE_TELEMETRY")),
            Some(&Some(std::ffi::OsStr::new("1")))
        );
        assert_eq!(std::env::var_os("DISABLE_TELEMETRY"), before);
    }
    #[test]
    fn timeout_keeps_output_and_is_bounded() {
        let dir = tempfile::tempdir().expect("temp");
        let log = dir.path().join("log");
        let mut request = Request::new("sh", dir.path(), ["-c", "printf started; sleep 20"]);
        request.timeout = Duration::from_millis(100);
        request.log = Some(log.clone());
        let start = Instant::now();
        assert!(Runner::default().run(request).is_err());
        assert!(start.elapsed() < Duration::from_secs(3));
        assert!(
            std::fs::read_to_string(log)
                .expect("log")
                .contains("started")
        );
    }
    #[test]
    fn text_is_passed_to_stdin_without_shell_interpolation() {
        let dir = tempfile::tempdir().expect("temp");
        let input = "$(touch unexpected); quoted text";
        let mut request = Request::new("cat", dir.path(), std::iter::empty::<&str>());
        request.input = Some(input.to_owned());
        assert_eq!(Runner::default().run(request).expect("cat"), input);
        assert!(!dir.path().join("unexpected").exists());
    }

    #[test]
    fn cancellation_stops_descendants_and_preserves_an_interrupted_result() {
        let dir = tempfile::tempdir().expect("temp");
        let runner = Runner::default();
        let stop = runner.stop.clone();
        let setter = thread::spawn(move || {
            thread::sleep(Duration::from_millis(100));
            stop.store(true, Ordering::Relaxed);
        });
        let request = Request::new(
            "sh",
            dir.path(),
            ["-c", "(sleep 0.6; printf orphan > orphaned) & wait"],
        );
        assert!(matches!(runner.run(request), Err(Error::Interrupted)));
        setter.join().expect("setter");
        thread::sleep(Duration::from_millis(700));
        assert!(
            !dir.path().join("orphaned").exists(),
            "descendant outlived cancellation"
        );
    }
}
