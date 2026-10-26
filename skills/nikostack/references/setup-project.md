# Prepare a product project

Run this procedure on first adoption of nikostack or when asked to prepare
AI issue handling. Plugin installation distributes files; it does not execute
GitHub writes. Keep this setup separate from ordinary feature work.

## Identify the target

Read the product's instructions and confirm its GitHub OWNER/REPO. Use the
product repository, not the nikostack repository, for product development
issues. Verify that GitHub CLI is authenticated and Issues are enabled.

## Prepare shared labels

Use the script next to this skill. From a nikostack checkout:

```sh
python3 skills/nikostack/scripts/setup-project.py --repository OWNER/REPO
python3 skills/nikostack/scripts/setup-project.py --repository OWNER/REPO --apply
```

The first command previews. The second creates only missing labels and
verifies them. It preserves existing colors and descriptions, does not label
issues, and does not start Claude. Apply within an explicit project-setup
request; do not ask again when the user has already authorized this setup.
For an installed plugin, resolve this SKILL.md directory and use the script's
absolute path. Do not copy the shared script into each product.

The shared definitions are [issue-labels.json](../assets/issue-labels.json):

| Label | Meaning |
| --- | --- |
| ai-ready | A person authorized the issue's stated scope. |
| ai-in-progress | A worker claimed the task. Do not start another owner. |
| ai-blocked | Work stopped. Inspect the reason before explicitly requeueing. |
| ai-review | A report or draft PR awaits human review. |

Label names are the worker's protocol in this version. Existing same-name
labels are preserved, so check that their local meanings are compatible.

## Prepare the issue and checks

Use [the task form](../assets/ai-task.yml) as a starting point for a
product-owned issue template. Preserve an existing form. Review any addition
through the product's normal change process.

A ready task needs 作業種別 (feature, bug, or review), 目的, 対象範囲,
期待する動作, 完了条件, and 検証方法. A label is authorization for that stated
scope, not permission to merge or install software.

If enabling the optional Mac worker, use [worker.example.json](../assets/worker.example.json)
as the product's .nikostack/worker.json and configure actual argv-based checks.
The empty check list is deliberately invalid until project checks are chosen.
Commands, protected validator paths, and live-check requirements belong to the
product. Follow the [worker guide](../../../docs/issue-worker.md) for a source
checkout, or obtain that guide from the matching repository release.

## Confirm adoption

Preview again and check that no labels are missing. For the worker, run its
dry-run and inspect the queue before starting it. Record the target and what
was prepared. Label preparation alone does not install a background worker,
enable GitHub Actions, or verify a product feature.
