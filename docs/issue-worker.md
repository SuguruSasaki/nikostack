# Local Issue worker

The Mac worker turns explicitly approved GitHub issues into an isolated
implementation, deterministic checks, a fresh read-only AI review, and a
draft PR. It uses the local Claude subscription login. It never merges,
updates the installed product, or installs a daemon.

## Requirements and trust

Use Python 3.10 or newer on macOS, Git, authenticated GitHub CLI, and a Claude
Code version supporting --restricted, --permission-prompts, and --json-schema.
The CLI flags were checked against the available local CLI; run the smoke
check before depending on another version. No API-key fallback is configured.

Run only on a private, trusted workstation for repositories you control.
Restricted file tools and absent shell/MCP tools constrain Claude, but project
builds and tests still execute trusted code as your Mac user. This is not an
OS sandbox for hostile repositories. The worker checks that both the issue
author and latest ai-ready approver are human collaborators with write,
maintain, or admin permission.

## Prepare

First follow [project setup](../skills/nikostack/references/setup-project.md).
The project owns .nikostack/worker.json. Set repository, base, checks, any
extra protected_paths, and optional hooks_path. Each check is a name and argv
array; optional paths selects affected files and timeout_seconds bounds the
command. Do not put credentials or personal data in the configuration.

From the nikostack checkout, with paths replaced for your machine:

```sh
python3 skills/nikostack/scripts/issue-worker.py --project /path/to/product --dry-run
python3 skills/nikostack/scripts/issue-worker.py --project /path/to/product
python3 skills/nikostack/scripts/issue-worker.py --project /path/to/product --watch
```

Default mode handles at most one task. --watch polls every 120 seconds and
drains eligible work serially. An empty queue invokes no AI. --dry-run reads
the queue without claiming issues or checking Claude authentication.
--state-dir changes the private local state root. Do not run a second worker
on another machine or with a different state root for the same repository:
the file lock coordinates one Mac and one state root, not a distributed fleet.

## Workflow and authority

1. A person writes a task using the product's issue form and applies ai-ready.
2. The worker verifies the approver, skips a task with an existing draft PR,
   adds ai-in-progress, removes ai-ready, and records a run and branch.
3. It clones to a private run directory and starts from the remote base.
   The original development checkout is not changed.
4. Claude reads the shared nikostack source plus product instructions and
   edits through file tools. Shell, GitHub, MCP, and subagent tools are absent.
   The controller runs the configured checks. One check-failure repair is
   allowed; repeated failure blocks the issue.
5. A fresh Claude session reviews the issue and exact staged diff with
   read-only file tools. Failed or unavailable review stops publication.
6. Before publication, the controller checks that the issue is still open,
   its scope has not changed, and it still has ai-in-progress. It commits
   with the authenticated GitHub user's public noreply identity and pushes
   only the dedicated ai/issue-N branch. Configured push hooks remain active.
7. It opens a draft PR with Closes #N, the head SHA, check statuses, and
   remaining live checks, then moves the issue to ai-review.

A review-only task uses read-only tools and reports findings without a PR.
The worker reports code-review feedback as an issue comment under the current
GitHub identity; it is not an independent human approval or GitHub review gate.

Both AI roles default to sonnet, with medium effort for implementation and
low for review. Implementation is capped at 24 turns and 20 minutes; review
at 12 turns and 10 minutes. One repair uses a fresh bounded call. These caps
do not constitute a fixed credit or dollar budget. The model is explicit,
with no fallback to a more expensive family. Prepare complex architecture
decisions before applying ai-ready.

## Stop and recover

Ctrl-C or SIGTERM stops the worker and its current child process group.
An interrupted task can remain ai-in-progress. Inspect its receipt, retained
checkout, remote branch, and PR before deciding whether to finish manually
or requeue. There is no automatic recovery that repeats an interrupted AI run.

Failures become ai-blocked with a reason. If GitHub cannot record that state,
the polling worker exits to avoid retrying the same task indefinitely.
Resolve the cause, inspect any retained remote branch, remove ai-blocked,
and explicitly add ai-ready. Existing PRs go back to ai-review instead of
creating a second PR. A pre-existing branch without a PR may require manual
recovery; force-push is not used.

Private state is under ~/.local/state/nikostack/OWNER__REPO unless overridden.
Each run retains its issue snapshot, base SHA, check logs for both attempts,
AI outputs, and receipt. Permissions are private on creation; do not share
the directory or commit it. Logs can contain project information.

## Verification and remaining limits

Run the contract tests:

```sh
python3 -m unittest discover -s tests -v
```

They use real local Git repositories and fake GitHub/AI, covering successful
publication, no-op queues, duplicate PRs, failed checks, protected instructions,
review mutation, scope drift, private error details, timeout, locks, and
idempotent label setup. Real Claude tool access and real GitHub interactions
need separate smoke checks; tests alone do not establish those connections.

Product behavior verification remains the product's responsibility. A draft
PR and passing code review do not establish that Slack, a Mac UI, external
writes, or actual user acceptance worked. Record unavailable checks explicitly.
The worker leaves final review, merge, and installed-product updates to the
operator. Unattended merge needs a separate head-bound approval and required
check design; it is not enabled here.
