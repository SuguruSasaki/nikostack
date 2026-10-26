# nikostack

nikostack は、複数のプロダクト開発で使うエージェントの共通手順です。v0.1 の最初の段階として、開発依頼の入口と小さな機能変更の手順を置いています。製品固有の操作・期待結果・検証方法は各プロジェクトで管理します。

## プラグインとして利用する

このリポジトリ自体が `nikostack` プラグインです。`skills/nikostack/` を唯一のスキル原本とし、Codex 用の `plugin.json` と Claude Code 用の `.claude-plugin/plugin.json` が同じ原本を参照します。MCP サーバーや製品別の設定は含みません。

Codex CLI では、このリポジトリをマーケットプレイスとして追加し、プラグインをインストールします。

```text
codex plugin marketplace add SuguruSasaki/nikostack
codex plugin add nikostack@nikostack
```

Claude Code では、次のコマンドを実行します。

```text
claude plugin marketplace add SuguruSasaki/nikostack
claude plugin install nikostack@nikostack
```

インストール後は新しいセッションでスキルを利用してください。Claude Code のプラグインスキル名は `/nikostack:nikostack` です。各プラグインの発見やインストール方法は、[Codex の公式説明](https://developers.openai.com/plugins/build/plugins)と[Claude Code の公式説明](https://code.claude.com/docs/en/plugin-marketplaces)に従います。

## このリポジトリでスキルを確認する

Codex または Claude Code をこのディレクトリで開くと、`$nikostack`（Codex）または `/nikostack`（Claude Code）で入口を明示的に呼び出せる構成です。依頼に応じた自動選択も想定しています。入口は [skills/nikostack/SKILL.md](skills/nikostack/SKILL.md)、小さな機能変更の手順は [small-feature.md](skills/nikostack/references/small-feature.md) です。別の製品リポジトリで使う場合は上記のプラグインをインストールし、その製品の指示に従います。

スキルの原本は `skills/nikostack/` に一つだけあります。`.agents/skills/nikostack` と `.claude/skills/nikostack` は、その原本への相対シンボリックリンクです。変更時は原本だけを編集してください。利用先にはプラグインをインストールし、製品固有の設定はそのリポジトリで管理します。

## 確認した範囲

- スキルの構文と相対リンク、両ツールの発見場所からの参照を確認した。
- Claude Code のマニフェストとマーケットプレイスの検証、両 CLI でのローカル登録・インストール・スキル発見を確認した。検証用のインストールと登録は削除済み。
- 実際の製品リポジトリで手順が守られるか、Codex と Claude Code の双方での開発依頼への適用は次段階の課題とする。

構成を選んだ理由と適用範囲は [設計判断](docs/decisions/0001-入口スキルと小さな機能変更.md) に記録しています。

プラグインの配布方法は[設計判断 0002](docs/decisions/0002-プラグインとしての配布.md)に記録しています。

変更の正しさ、検証、レビューしやすさを考える際の共通原則と現状との差分は、[信頼できるソフトウェア開発の参考資料](docs/references/jane-street-reliable-software.md)にまとめています。これは製品ごとの規約や検証手順を置き換えるものではありません。
