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

## Activate it in a product repository

Install the plugin once with the commands above. Then start the agent from the product repository you want to change:

```sh
cd /path/to/product-repository
claude  # or: codex
```

At the start of a Claude Code message, invoke `/nikostack:nikostack` followed by a concrete feature, bug fix, or review request. [Claude Code qualifies plugin skills with the plugin name](https://code.claude.com/docs/en/plugins), so this is the plugin command corresponding to a direct command such as [pstack's `/poteto-mode`](https://github.com/cursor/plugins/blob/main/pstack/README.md):

```text
/nikostack:nikostack Fix the failing login test and verify the affected behavior.
```

In Codex, open `/skills` and select `nikostack`, or start the request with `$nikostack`:

```text
$nikostack Fix the failing login test and verify the affected behavior.
```

Invoke the skill when you want its workflow for the current request. It does not toggle a persistent mode or replace the agent's system message. The skill is configured for manual invocation; it does not require a standing instruction in each product repository. The product's own instructions, specifications, and verification commands still govern the work. Check that the agent reports the code state, checks it ran, observed results, and any unverified areas.

See the [OpenAI Docs packaging guide](https://developers.openai.com/plugins/build/plugins) and the [Claude Code marketplace guide](https://code.claude.com/docs/en/plugin-marketplaces) for installation details.

## Use the skill in this repository

When you open this directory in Codex or Claude Code, you can invoke the entry skill as `$nikostack` or `/nikostack`, respectively. After installing the plugin in another repository, Claude Code uses the qualified name `/nikostack:nikostack`. The entry point is [SKILL.md](skills/nikostack/SKILL.md); the [small feature procedure](skills/nikostack/references/small-feature.md) provides more detail.

`.agents/skills/nikostack` and `.claude/skills/nikostack` are relative symbolic links to the one source at `skills/nikostack/`. Edit the source only. Keep product-specific settings in the product repository.

## Verification status

- The skill metadata, relative links, and local discovery paths were checked. The Claude Code manifest and marketplace passed validation.
- Codex CLI 0.164.0 and Claude Code 2.1.310 installed version 0.1.2 from the local marketplace and discovered the skill. Version 0.1.0 was also installed from GitHub in both CLIs. Temporary installations and registrations were removed.
- Invoking the current version in a product session and applying it to a real product change remain untested.

The [initial design decision](docs/decisions/0001-entry-skill-and-small-feature.md) explains the entry skill and scope. The [plugin distribution decision](docs/decisions/0002-plugin-distribution.md) records the packaging choice. The [reliable software engineering reference](docs/references/jane-street-reliable-software.md) covers shared principles and gaps; it does not replace product-specific rules or verification procedures.
