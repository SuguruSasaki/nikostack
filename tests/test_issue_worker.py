"""Contracts: real isolated Git, fake GitHub and AI, no live user data."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/nikostack/scripts"


def module(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), SCRIPTS / (name + ".py"))
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


worker = module("issue-worker")
setup = module("setup-project")


def issue(number=1, kind="feature"):
    body = "### 作業種別\n\n" + kind + "\n\n"
    body += "\n\n".join("### " + name + "\n\nA bounded task."
                          for name in worker.REQUIRED_SECTIONS)
    return {"number": number, "title": "A bounded change", "body": body, "state": "open",
            "labels": [{"name": "ai-ready"}], "user": {"login": "fixture", "type": "User"}}


class GitHub:
    def __init__(self, items):
        self.items = {i["number"]: copy.deepcopy(i) for i in items}
        self.comments, self.prs = [], []
        self.change_issue = False
        self.report_fails = False

    def ready(self):
        return [copy.deepcopy(i) for i in self.items.values()
                if {x["name"] for x in i["labels"]} == {"ai-ready"}]

    def trusted(self, item):
        return item.get("approved", True)

    def existing_pr(self, branch):
        return self.prs

    def issue(self, number):
        value = copy.deepcopy(self.items[number])
        if self.change_issue:
            value["body"] += "\nChanged scope."
        return value

    def transition(self, number, target):
        if self.report_fails and target == "ai-blocked":
            raise worker.Blocked("Network unavailable")
        self.items[number]["labels"] = [{"name": target}]

    def comment(self, number, body):
        self.comments.append(body)

    def api(self, method, path):
        assert (method, path) == ("GET", "/user")
        return {"id": 123, "login": "fixture"}

    def create_pr(self, branch, base, title, body):
        self.prs.append({"branch": branch, "body": body})
        return "https://github.com/example/project/pull/2"


class LocalWorker(worker.Worker):
    def __init__(self, *args, remote, **kwargs):
        super().__init__(*args, **kwargs)
        self.remote = remote

    def clone(self, work, branch):
        self.git(["clone", "--quiet", "--no-hardlinks", str(self.project), str(work)])
        self.git(["remote", "set-url", "origin", str(self.remote)], work)
        self.git(["switch", "--quiet", "-c", branch], work)


class Agent:
    def __init__(self, value="ok", verdict="pass", mutate=False):
        self.calls, self.value, self.verdict, self.mutate = [], value, verdict, mutate

    def __call__(self, work, job, prompt, *, reviewer=False, **kwargs):
        self.calls.append("review" if reviewer else "implement")
        if reviewer:
            if self.mutate:
                (work / "value.txt").write_text("Reviewer changed it")
            return {"verdict": self.verdict, "summary": "Reviewed.",
                    "findings": [] if self.verdict == "pass" else ["A concrete problem."]}
        (work / "value.txt").write_text(self.value)
        return {"status": "ready", "summary": "Changed behavior.",
                "manual_checks": ["Check the real product surface."]}


class WorkerContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="worker-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.seed, self.remote, self.state = (
            self.root / "source with spaces", self.root / "origin.git", self.root / "state")
        self.state.mkdir()
        worker.run(["git", "init", "--quiet", "--bare", str(self.remote)])
        worker.run(["git", "init", "--quiet", "-b", "main", str(self.seed)])
        for key, value in (("user.name", "Fixture"),
                           ("user.email", "noreply@anthropic.com")):
            worker.run(["git", "config", key, value], cwd=self.seed)
        (self.seed / "value.txt").write_text("old")
        worker.run(["git", "add", "."], cwd=self.seed)
        worker.run(["git", "commit", "--quiet", "-m", "Fixture"], cwd=self.seed)
        worker.run(["git", "remote", "add", "origin", str(self.remote)], cwd=self.seed)
        worker.run(["git", "push", "--quiet", "origin", "main"], cwd=self.seed)
        self.config = {"repository": "example/project", "checks": [{
            "name": "Behavior", "argv": [
                sys.executable, "-c",
                "from pathlib import Path; assert Path('value.txt').read_text() == 'ok'"]}]}
        self.gh = GitHub([issue()])

    def make(self, agent):
        return LocalWorker(self.seed, self.config, self.state,
                           github=self.gh, agent=agent, remote=self.remote)

    def receipt(self):
        return json.loads(next(self.state.glob("issue-*/receipt.json")).read_text())

    def test_success_isolates_source_checks_reviews_and_publishes(self):
        agent = Agent()
        self.assertEqual(self.make(agent).once()["status"], "pr-created")
        self.assertEqual(agent.calls, ["implement", "review"])
        self.assertEqual((self.seed / "value.txt").read_text(), "old")
        self.assertEqual(worker.run(["git", "status", "--porcelain"], cwd=self.seed), "")
        self.assertIn("Closes #1", self.gh.prs[0]["body"])
        self.assertEqual(self.gh.items[1]["labels"], [{"name": "ai-review"}])
        self.assertEqual(self.receipt()["stage"], "pr-created")
        self.assertEqual(worker.run(
            ["git", "show", "refs/heads/ai/issue-1:value.txt"], cwd=self.remote), "ok")

    def test_dry_run_and_empty_queue_never_claim_or_call_ai(self):
        agent = Agent()
        self.assertEqual(self.make(agent).once(True)["ready"][0]["number"], 1)
        self.assertEqual(self.gh.comments, [])
        self.gh.items.clear()
        self.assertEqual(self.make(agent).once(), {"status": "idle"})
        self.assertEqual(agent.calls, [])

    def test_unapproved_issue_does_not_starve_approved_work(self):
        self.gh.items[1]["approved"] = False
        self.gh.items[2] = issue(2)
        result = self.make(Agent()).once()
        self.assertEqual((result["status"], result["issue"]), ("pr-created", 2))

    def test_existing_pr_is_not_implemented_twice(self):
        agent = Agent()
        self.gh.prs.append({"url": "existing"})
        self.assertEqual(self.make(agent).once()["status"], "existing-pr")
        self.assertEqual(agent.calls, [])

    def test_failed_checks_have_one_repair_and_no_push(self):
        agent = Agent(value="bad")
        self.assertEqual(self.make(agent).once()["status"], "blocked")
        self.assertEqual(agent.calls, ["implement", "implement"])
        self.assertEqual(self.gh.prs, [])
        job = next(self.state.glob("issue-*"))
        self.assertTrue((job / "check-1-0.log").exists())
        self.assertTrue((job / "check-2-0.log").exists())
        self.assertNotIn("ai/issue", worker.run(
            ["git", "for-each-ref", "--format=%(refname)"], cwd=self.remote))

    def test_protected_file_change_blocks_before_checks(self):
        def agent(work, *args, **kwargs):
            (work / "AGENTS.md").write_text("Weaken the checks.")
            return {"status": "ready", "summary": "No.", "manual_checks": []}
        self.assertEqual(self.make(agent).once()["status"], "blocked")
        self.assertIn("Protected", self.receipt()["reason"])

    def test_product_feature_map_can_change_but_validator_script_cannot(self):
        feature = self.seed / ".agents/skills/verify-product/features/new.md"
        feature.parent.mkdir(parents=True)
        feature.write_text("A user-visible feature and its expected result.")
        self.assertIn(str(feature.relative_to(self.seed)),
                      worker.stage_and_guard(self.seed, []))
        validator = self.seed / ".agents/skills/verify-product/scripts/check.sh"
        validator.parent.mkdir(parents=True)
        validator.write_text("#!/bin/sh\nexit 0\n")
        with self.assertRaises(worker.Blocked):
            worker.stage_and_guard(self.seed, [])

    def test_failed_independent_review_prevents_publication(self):
        self.assertEqual(self.make(Agent(verdict="fail")).once()["status"], "blocked")
        self.assertEqual(self.gh.prs, [])

    def test_readonly_reviewer_cannot_silently_change_the_diff(self):
        self.assertEqual(self.make(Agent(mutate=True)).once()["status"], "blocked")
        self.assertEqual(self.gh.prs, [])

    def test_scope_change_stops_publication(self):
        self.gh.change_issue = True
        agent = Agent()
        self.assertEqual(self.make(agent).once()["status"], "changed")
        self.assertEqual(agent.calls, [])
        self.assertEqual(self.gh.prs, [])

    def test_scope_changed_during_implementation_stops_publication(self):
        agent = Agent()
        def changes_scope(*args, **kwargs):
            result = agent(*args, **kwargs)
            if kwargs.get("reviewer"):
                self.gh.change_issue = True
            return result
        self.assertEqual(self.make(changes_scope).once()["status"], "blocked")
        self.assertEqual(self.gh.prs, [])

    def test_review_issue_is_reported_without_implementation(self):
        self.gh = GitHub([issue(kind="review")])
        agent = Agent()
        self.assertEqual(self.make(agent).once()["status"], "reported")
        self.assertEqual(agent.calls, ["review"])
        self.assertEqual(self.gh.prs, [])

    def test_incomplete_issue_blocks_before_ai(self):
        self.gh.items[1]["body"] = "Something vague"
        agent = Agent()
        self.assertEqual(self.make(agent).once()["status"], "blocked")
        self.assertEqual(agent.calls, [])

    def test_private_error_details_stay_local(self):
        def agent(*args, **kwargs):
            raise OSError("private operator location")
        self.make(agent).once()
        self.assertIn("private operator location", self.receipt()["reason"])
        self.assertFalse(any("private operator location" in x for x in self.gh.comments))

    def test_github_reporting_failure_is_distinct_and_stops_retries(self):
        self.gh.report_fails = True
        self.assertEqual(self.make(Agent(value="bad")).once()["status"], "report-failed")


class Boundaries(unittest.TestCase):
    def test_invalid_path_selectors_cannot_silently_skip_all_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            for paths in ("src/**", []):
                path.write_text(json.dumps({"repository": "example/project", "checks": [
                    {"name": "Check", "argv": ["true"], "paths": paths}]}))
                with self.assertRaises(worker.Blocked):
                    worker.load_config(path)

    def test_two_processes_cannot_claim_the_same_local_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            with worker.locked(Path(directory)):
                with self.assertRaises(worker.Busy):
                    with worker.locked(Path(directory)):
                        self.fail("Double lock")

    def test_timeout_is_bounded_and_keeps_output(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "timeout.log"
            start = time.monotonic()
            with self.assertRaises(worker.Blocked):
                worker.run([sys.executable, "-c",
                            "import time; print('started',flush=True); time.sleep(20)"],
                           timeout=0.2, log=log)
            self.assertLess(time.monotonic() - start, 4)
            self.assertIn("started", log.read_text())

    def test_issue_text_is_not_interpolated_into_a_shell_command(self):
        captured = []
        def fake(argv, **kwargs):
            captured.append((argv, kwargs))
            return json.dumps({"structured_output": {
                "status": "ready", "summary": "ok", "manual_checks": []}})
        with tempfile.TemporaryDirectory() as directory:
            text = '$(touch SHOULD_NOT_EXIST); "quoted"'
            with patch.object(worker, "run", side_effect=fake):
                worker.ask_agent(Path(directory), Path(directory), text)
        argv, kwargs = captured[0]
        self.assertEqual(kwargs["stdin"], text)
        self.assertNotIn(text, argv)
        self.assertNotIn("Bash", argv[argv.index("--tools") + 1])
        self.assertIn("--restricted", argv)

    def test_no_api_key_fallback(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fixture",
                                    "CLAUDE_CODE_USE_BEDROCK": "1"}):
            self.assertNotIn("ANTHROPIC_API_KEY", worker.claude_environment())
            self.assertNotIn("CLAUDE_CODE_USE_BEDROCK", worker.claude_environment())
        with patch.object(worker, "run",
                          return_value='{"loggedIn":true,"authMethod":"api_key"}'):
            with self.assertRaises(worker.Blocked):
                worker.check_subscription()

    def test_github_user_endpoint_is_global(self):
        with patch.object(worker, "run", return_value='{"id":123}') as call:
            worker.GitHub("example/project").api("GET", "/user")
        self.assertEqual(call.call_args.args[0][-1], "user")

    def test_latest_label_approver_needs_write_permission(self):
        gh = worker.GitHub("example/project")
        def api(method, path, *args, **kwargs):
            if "events?" in path:
                return [[{"event": "labeled", "label": {"name": "ai-ready"},
                          "actor": {"login": "triage", "type": "User"}}]]
            return {"permission": "triage"}
        with patch.object(gh, "api", side_effect=api):
            self.assertFalse(gh.trusted(issue()))

    def test_state_transition_preserves_unrelated_labels(self):
        gh, calls = worker.GitHub("example/project"), []
        def api(method, path, payload=None, **kwargs):
            calls.append((method, path))
        with patch.object(gh, "api", side_effect=api), patch.object(
                gh, "issue", return_value={"labels": [
                    {"name": "ai-ready"}, {"name": "bug"}, {"name": "enhancement"}]}):
            gh.transition(1, "ai-in-progress")
        self.assertEqual([p for m, p in calls if m == "DELETE"], ["issues/1/labels/ai-ready"])


class LabelSetup(unittest.TestCase):
    def setUp(self):
        self.labels = json.loads((ROOT / "skills/nikostack/assets/issue-labels.json").read_text())
        self.existing = [{"name": "ai-ready", "color": "abcdef", "description": "Keep mine"}]
        self.original = copy.deepcopy(self.existing)
        self.calls = []

    def api(self, method, path, payload=None, **kwargs):
        self.calls.append((method, path, payload))
        if path.endswith("/labels") and method == "POST":
            self.existing.append(copy.deepcopy(payload))
            return payload
        if "/labels?" in path:
            return [copy.deepcopy(self.existing)]
        return {"full_name": "example/project", "has_issues": True, "permissions": {"push": True}}

    def test_preview_does_not_mutate_and_apply_is_idempotent(self):
        preview = setup.prepare("example/project", self.labels, request=self.api)
        self.assertEqual(len(preview["missing"]), 3)
        self.assertEqual(self.existing, self.original)
        first = setup.prepare("example/project", self.labels, True, self.api)
        second = setup.prepare("example/project", self.labels, True, self.api)
        self.assertEqual(len(first["created"]), 3)
        self.assertEqual(second["created"], [])
        self.assertEqual(self.existing[0], self.original[0])
        self.assertFalse(any(m in ("PATCH", "PUT", "DELETE") for m, _, _ in self.calls))
        self.assertFalse(any("/issues/" in p for _, p, _ in self.calls))

    def test_disabled_issues_and_readonly_access_do_not_create_labels(self):
        def denied(method, path, payload=None, **kwargs):
            if "/labels?" in path:
                return [[]]
            return {"has_issues": True, "full_name": "example/project", "permissions": {}}
        with self.assertRaises(setup.SetupError):
            setup.prepare("example/project", self.labels, True, denied)
        with self.assertRaises(setup.SetupError):
            setup.prepare("example/project", self.labels, True,
                          lambda *a, **k: {"has_issues": False})


if __name__ == "__main__":
    unittest.main()
