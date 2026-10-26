# Rust worker verification, 2026-10-27

This record separates local contract tests from live connections. It does
not establish that a product feature, a Niko integration, or unattended
Issue-to-PR processing is ready.

## Local verification

`./.agents/validate rust` runs format checking, Clippy with warnings denied,
and 26 tests. The suite uses real local Git repositories with fake GitHub
and AI boundaries. It covers successful draft publication, one repair,
repeated failure, unauthorized actors, duplicate PRs, protected edits and
renames, scope drift, review mutation, process-group cancellation, private
receipts, local locking, add-only label preparation, and GitHub telemetry
opt-outs reaching nested children without changing the parent environment.

The source was also checked with `git diff --check`, local documentation
links were resolved, and shared Codex/Claude skill links were inspected.
The build used Rust 1.98.1; the declared minimum toolchain was not separately
tested.

## Live GitHub label setup

The Rust `setup` preview found four missing AI labels in
`SuguruSasaki/nikostack`. Applying created them. Reapplying returned no
missing labels and no creations, preserving the existing definitions.
No product issue was dispatched during label setup.

## Live Claude trials

The bounded documentation task was
[Issue #4](https://github.com/SuguruSasaki/nikostack/issues/4).
All model trials used isolated checkouts, an explicit `haiku` model, subscription
authentication, and child-only telemetry opt-outs. No API-key fallback,
merge, application update, or daemon installation was performed.

| Trial | Observed result | Outcome |
| --- | --- | --- |
| First | Implementation and all nine literal checks passed. A separate read-only review returned pass with positive observations in findings. | The controller rejected the contradictory result before commit or push. |
| Second | Implementation passed eight checks. The case-sensitive human-review literal check failed without output. One repair made no change, and the same check failed. | The controller stopped before review or publication and left the issue blocked. |
| Third | All nine unchanged checks passed. An independent read-only review returned pass with no unresolved findings. No repair was needed. | The worker committed, pushed its dedicated branch, created Draft PR #5, and moved Issue #4 to ai-review. |

For the first two trials, the usage reports identified `claude-haiku-5-5` for all four calls:
two implementations, one review, and one repair. There were 33 reported
turns in total. The sum of reported API-equivalent costs was approximately
USD 0.012; this is not a subscription billing statement.

The third trial used `claude-haiku-5-5` twice: implementation took seven
turns and review took five. The reported API-equivalent total was
USD 0.00604879, also not a subscription billing statement.

## Third-trial evidence

The controller source was `98af064`. Its run
`issue-4-1793033035048000000-30585` completed with stage `pr-created`.
[Draft PR #5](https://github.com/SuguruSasaki/nikostack/pull/5) contains only
`docs/ai-task-checklist.md`, with 63 added lines. Its head is
`72dd33786bb579332303c7181af86c05fada2d59`, matching the private receipt.
The automatic checks and independent review refer to this same proposed
change. No merge or installed-product update followed publication.

The PR quotes the implementation agent's report from before validation.
Some remaining-check notes repeat controller checks that are already
completed in the verification table. This wording needs a reporting
improvement; the receipt and table record the actual controller outcomes.

Before this successful run, automatic approval review rejected a startup
because it detected `cafe.github.com` with an unknown telemetry payload.
Read-only inspection found that hostname in the installed GitHub CLI and
in its [official send-telemetry implementation](https://github.com/cli/cli/blob/trunk/pkg/cmd/send-telemetry/send_telemetry.go).
The controller now gives all children `GH_TELEMETRY=false` and
`DO_NOT_TRACK=1`, using
[GitHub's documented opt-out](https://docs.github.com/en/github-cli/github-cli/github-cli-telemetry).
Subsequent API reads and the complete worker run succeeded. Global settings
and the approval controls were not changed.

## Changes informed by the trials

- Define findings as unresolved blocking defects only; passing reviews must
  have an empty findings array. Keep successful observations in the summary.
  The controller still rejects contradictory results.
- Give the implementation the approved check definitions. For a failed
  check, give the repair its name, argv, actual statuses, and bounded output,
  including an explicit indication that output may be empty.
- Do not spend a repair call when no configured check covers the changed paths.
- Encode receipt run IDs as JSON strings.
- Explicitly unlock the repository lock on drop. During local testing,
  concurrent child creation exposed transient lock retention after closing
  the parent's descriptor.

The current source passed the local suite and the third live trial completed
the normal Issue-to-Draft-PR path. The revised repair feedback has contract
test coverage; the third trial needed no repair, so that particular live
failure-and-repair path remains unverified.

This was a single bounded documentation task, not a throughput or unattended
operation test. Niko's product-specific checks, integrations, application
behavior, and deployment still need their own verification. No background
worker was started, and human review remains required before merging.
