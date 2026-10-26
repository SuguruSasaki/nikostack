# Local approval queue and worker

- Date: 2026-10-27
- Status: proposed for adoption

## Problem

Passing issue URLs by hand repeats task selection and handoff. Projects also
need a consistent way to prepare the AI labels without replacing local labels.

## Decision

Package label definitions, an idempotent setup script, an issue form, and a
serial Mac worker with the shared skill. Keep validation argv, project scopes,
and operation recipes in each product.

The worker uses the existing subscription login and bounded fresh Claude
sessions. The controller owns checks, GitHub writes, commits, and publication;
the model receives file tools only. A passing independent code review permits
a draft PR, not merge or product installation.

## Tradeoffs

One Mac and a local lock are sufficient for this first version. Cross-machine
claims, automatic merge, daemon installation, and production verification are
separate changes. Human-authored, explicitly approved bounded issues are the
supported input. A stopped job keeps its evidence and requires explicit
requeueing. This costs an additional review call but separates authorship
from the review context.

## Verification

Use the contract suite and separate external smoke checks documented in
[the worker guide](../issue-worker.md). Do not equate those fixtures with
an actual product change or claim hosted-runner compatibility.
