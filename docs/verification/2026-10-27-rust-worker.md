# Rust worker verification, 2026-10-27

This record separates local contract tests from live connections. It does
not establish that a product feature, a Niko integration, or unattended
Issue-to-PR processing is ready.

## Local verification

`./.agents/validate rust` runs format checking, Clippy with warnings denied,
and 25 tests. The suite uses real local Git repositories with fake GitHub
and AI boundaries. It covers successful draft publication, one repair,
repeated failure, unauthorized actors, duplicate PRs, protected edits and
renames, scope drift, review mutation, process-group cancellation, private
receipts, local locking, and add-only label preparation.

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
Both trials used isolated checkouts, an explicit `haiku` model, subscription
authentication, and child-only telemetry opt-outs. No API-key fallback,
merge, application update, or daemon installation was performed.

| Trial | Observed result | Stop |
| --- | --- | --- |
| First | Implementation and all nine literal checks passed. A separate read-only review returned pass with positive observations in findings. | The controller rejected the contradictory result before commit or push. |
| Second | Implementation passed eight checks. The case-sensitive human-review literal check failed without output. One repair made no change, and the same check failed. | The controller stopped before review or publication and left the issue blocked. |

The usage reports identified `claude-haiku-5-5` for all four calls:
two implementations, one review, and one repair. There were 33 reported
turns in total. The sum of reported API-equivalent costs was approximately
USD 0.012; this is not a subscription billing statement.

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

The final changes passed the local suite. No further external AI calls were
made after the second trial. Successful automatic draft-PR publication and
the revised live repair/review contracts remain unverified. Inspect Issue #4
and its retained evidence before explicitly requeueing; do not activate a
background worker on the basis of these trials.
