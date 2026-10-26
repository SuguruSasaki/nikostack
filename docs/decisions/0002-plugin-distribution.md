# 0002 Plugin distribution

- Date: 2026-10-26
- Status: Adopted (verified with local marketplaces)

## Problem

The original relative symbolic links exposed the skill to Codex and Claude Code inside this repository. Using it in another product repository required the user to place the skill manually.

## Decision

Treat the repository root as the plugin package and keep `skills/nikostack/` as the single skill source. The root `plugin.json` is the portable manifest for Codex; `.claude-plugin/plugin.json` is the Claude Code compatibility manifest. Both marketplaces point to the repository root. Neither duplicates the skill content.

Users install the plugin explicitly. It provides only the shared workflow. Product-specific specifications, verification commands, credentials, and MCP servers stay out of the package. The target product's instructions remain authoritative for its work.

## Verification and remaining work

Codex CLI 0.164.0 and Claude Code 2.1.310 installed `nikostack@nikostack` from local marketplaces. The skill in the Codex cache matched the source, and Claude Code reported one skill. The temporary installations and marketplace registrations were removed.

Applying the plugin to a real product change and installing from the remote GitHub repository remain untested. Submission to a public plugin directory would require meeting its separate publication requirements, including a license.
