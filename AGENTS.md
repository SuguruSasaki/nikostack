# Maintaining Nikostack

`skills/nikostack/` is the single source for Codex and Claude Code. When changing the entry point, edit [SKILL.md](skills/nikostack/SKILL.md) and only the necessary references. Do not copy its content into `.agents/skills/` or `.claude/skills/`.

Keep plugin manifests and marketplaces as thin distribution metadata. Do not duplicate the skill or product-specific instructions in them.

Keep only shared development procedures in this repository. Product-specific specifications, verification commands, Feature Maps, personal information, and credentials belong in the target project.

For a change, follow the target repository's existing design to prevent invalid states and verify observable behavior with an appropriate method. Keep the diff small and explainable. Tell human reviewers what was verified and what remains unverified. Choose techniques according to the language, target, and risk. See the [reliable software engineering reference](docs/references/jane-street-reliable-software.md) for rationale and examples.
