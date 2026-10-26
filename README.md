# nikostack

nikostack は、複数のプロダクト開発で使うエージェントの共通手順です。v0.1 の最初の段階として、開発依頼の入口と小さな機能変更の手順を置いています。製品固有の操作・期待結果・検証方法は各プロジェクトで管理します。

## スキルを確認する

Codex または Claude Code をこのディレクトリで開くと、`$nikostack`（Codex）または `/nikostack`（Claude Code）で入口を明示的に呼び出せる構成です。依頼に応じた自動選択も想定しています。入口は [skills/nikostack/SKILL.md](skills/nikostack/SKILL.md)、小さな機能変更の手順は [small-feature.md](skills/nikostack/references/small-feature.md) です。実際の製品開発で使うには、その製品のリポジトリへの導入が必要です。

スキルの原本は `skills/nikostack/` に一つだけあります。`.agents/skills/nikostack` と `.claude/skills/nikostack` は、その原本への相対シンボリックリンクです。変更時は原本だけを編集してください。他のプロジェクトへの導入スクリプトは次段階で作ります。

## 今回確認した範囲

- スキルの構文と相対リンク、両ツールの発見場所からの参照を確認する。
- 実際の開発依頼で手順が守られるか、Codex と Claude Code の双方での起動確認は次段階の課題とする。

構成を選んだ理由と適用範囲は [設計判断](docs/decisions/0001-入口スキルと小さな機能変更.md) に記録しています。
