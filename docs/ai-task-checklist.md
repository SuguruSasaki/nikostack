# AI task checklist

Use this checklist before asking an AI agent to work on an issue. A clear issue
lets a reviewer confirm the intent and lets the agent stop at the right boundary.

## Labels

- `ai-ready`: a human has approved work on the scope described in the issue.
  Do not start work without this label.
- `ai-review`: the agent has reported back or opened a Draft PR, and a human
  must check the result before anything else happens.

## Before starting

Prepare these five items in the issue body.

### Purpose

- State why the change is needed, in one or two sentences.
- Name the user or maintainer who benefits.

### Scope

- List the files, directories, or surfaces that may change.
- List what must not change (for example, unrelated code, config, or docs).
- Name protected paths the agent must not edit.

### Expected behavior

- Describe what should be observable after the change, from the user's view.
- Give one concrete example input and output where practical.

### Acceptance criteria

- Write checks that a reviewer can confirm as yes or no.
- Keep the list short. Each item should be independently testable.

### Verification method

- Name the commands or steps the controller will run, such as `grep`,
  `git diff --check`, or the project's test suite.
- State what is out of scope for verification, such as live product or
  external service behavior.

## Before marking `ai-ready`

- [ ] Purpose, Scope, Expected behavior, Acceptance criteria, and
      Verification method are all filled in.
- [ ] The scope is small enough to review in one Draft PR.
- [ ] Protected paths and secrets are not part of the requested change.
- [ ] Someone with authority has approved the scope.

## After the agent reports

- Read the report and the Draft PR diff; do not rely on passing checks alone.
- Confirm each acceptance criterion against the evidence.
- Record any check that was not run or was blocked.

## Human decisions

Merging a PR and updating an installed app are separate decisions. Both need
human review. Automated merge and automated installation are not performed by
this workflow.
