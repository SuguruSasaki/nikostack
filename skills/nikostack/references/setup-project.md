# Prepare AI task labels

Run this during first-time project adoption or an explicit request to prepare
AI issue handling. The target is the product's GitHub repository. Product
development issues belong there; shared nikostack changes belong in nikostack.

## Preview and apply

Confirm the target OWNER/REPO from the product's Git remote and instructions.
From a nikostack source checkout:

```sh
python3 skills/nikostack/scripts/setup-project.py --repository OWNER/REPO
python3 skills/nikostack/scripts/setup-project.py --repository OWNER/REPO --apply
```

The first command is a read-only preview. The second creates only missing
labels and verifies the result. GitHub CLI must be authenticated, Issues must
be enabled, and applying changes requires repository write permission.
Use the installed skill directory's absolute script path when working from
a plugin rather than a source checkout. Do not duplicate the script in products.

Apply within the user's authorized setup scope. An ordinary feature or review
request does not authorize repository setup. Plugin installation distributes
the helper but does not execute GitHub writes automatically.

## Shared labels

Definitions are maintained in [issue-labels.json](../assets/issue-labels.json).

| Label | Meaning |
| --- | --- |
| ai-ready | A person permits work within the issue's stated scope. |
| ai-in-progress | An agent claimed the task; avoid duplicate owners. |
| ai-blocked | Work stopped; inspect the reason before explicit requeueing. |
| ai-review | A report or draft PR is waiting for human review. |

Preserve existing colors and descriptions. If an existing same-name label has
a different meaning, report the conflict rather than overwriting it.

Before applying ai-ready to an issue, confirm its purpose, scope, expected
behavior, acceptance conditions, and verification method. Label setup does not
apply labels to issues, start an agent, grant merge permission, or install
software. The product defines its assignment and completion process.

## Confirm

Run the preview again and confirm the missing list is empty. Record the target
repository, created labels, and preserved labels. A failed partial setup can
be rerun: existing labels are not replaced.
