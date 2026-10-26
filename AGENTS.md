# nikostack の保守

`skills/nikostack/` が Codex と Claude Code の共通原本です。入口を変更するときは [SKILL.md](skills/nikostack/SKILL.md) と必要な参照だけを編集し、`.agents/skills/` と `.claude/skills/` に内容を複製しないでください。

このリポジトリには共通の開発手順だけを置きます。製品固有の仕様、検証コマンド、Feature Map、個人情報や認証情報は利用先のプロジェクトで管理してください。

変更では、対象リポジトリの既存設計に沿って不正な状態を防ぎ、観測できる振る舞いを適切な方法で検証してください。小さく説明可能な差分を保ち、検証で確認できた範囲と未確認の範囲を人間に伝えてください。手段は言語・対象・リスクに応じて選びます。判断の背景と適用例は[信頼できるソフトウェア開発の参考資料](docs/references/jane-street-reliable-software.md)を参照してください。
