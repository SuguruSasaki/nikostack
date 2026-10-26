# nikostack

Nikostack provides a shared development workflow for coding agents across product repositories. Version 0.1 starts with an entry skill and a procedure for small feature changes. Each product project owns its operations, expected behavior, and verification methods.

## Install as a plugin

This repository is the `nikostack` plugin. `skills/nikostack/` is its single skill source. The root `plugin.json` packages it for Codex, and `.claude-plugin/plugin.json` provides Claude Code compatibility. The package contains no MCP server or product-specific settings.

For Codex CLI, add this repository as a marketplace and install the plugin:

```text
codex plugin marketplace add SuguruSasaki/nikostack
codex plugin add nikostack@nikostack
```

For Claude Code:

```text
claude plugin marketplace add SuguruSasaki/nikostack
claude plugin install nikostack@nikostack
```

Start a new session after installation. The Claude Code plugin skill is `/nikostack:nikostack`. See the [OpenAI Docs packaging guide](https://developers.openai.com/plugins/build/plugins) and the [Claude Code marketplace guide](https://code.claude.com/docs/en/plugin-marketplaces) for platform details.

## Use the skill in this repository

When you open this directory in Codex or Claude Code, you can invoke the entry skill as `$nikostack` or `/nikostack`, respectively. Agents may also select it when a request matches its description. The entry point is [SKILL.md](skills/nikostack/SKILL.md); the [small feature procedure](skills/nikostack/references/small-feature.md) provides more detail. To use Nikostack in another product repository, install the plugin and follow that project's instructions.

`.agents/skills/nikostack` and `.claude/skills/nikostack` are relative symbolic links to the one source at `skills/nikostack/`. Edit the source only. Keep product-specific settings in the product repository.

## Verification status

- The skill syntax, relative links, and local discovery paths were checked.
- The Claude Code manifest and marketplace passed validation. Both CLIs installed the plugin from a local marketplace and discovered the skill. The temporary installations and marketplace registrations were removed.
- Applying the installed skill to an actual product change in both tools remains untested.

The [initial design decision](docs/decisions/0001-entry-skill-and-small-feature.md) explains the entry skill and scope. The [plugin distribution decision](docs/decisions/0002-plugin-distribution.md) records the packaging choice. The [reliable software engineering reference](docs/references/jane-street-reliable-software.md) covers shared principles and gaps; it does not replace product-specific rules or verification procedures.
