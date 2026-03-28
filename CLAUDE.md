# Life OS — AIとともに生きる統合環境

このリポジトリはあなたの**人生の統合開発環境**です。

## 毎回の起動時に読むファイル（必須）

1. `context/now.md` — **今この瞬間の状態**（最優先。ここを読むだけで現在地がわかる）
2. `me/profile.md` — あなた自身のすべて

## ディレクトリ構造

```
life-os/
├── context/
│   └── now.md           # 今週のフォーカス・悩み・状態（毎週更新）
├── me/
│   ├── profile.md       # 基本プロフィール・ライフスタイル・スキル
│   ├── assessments.md   # StrengthsFinder・MBTI・Big5等の診断結果
│   └── principles.md    # 意思決定の原則・価値観
├── goals/
│   └── 2026.md          # 年次OKR
├── finance/
│   ├── review.md        # 資産・家計の現状
│   ├── zaim/            # Zaim API連携スクリプト
│   └── amazon/          # Amazon注文履歴取得・Zaim照合スクリプト
├── health/
│   ├── goals.md         # 健康・筋トレの目標
│   └── log.md           # トレーニングログ
├── relationships/
│   └── key-people.md    # 大切な人たち・誕生日
├── learning/
│   └── books.md         # 読書・学習ログ
└── decisions/
    └── log.md           # 重要な意思決定の記録
```

## 話題別の参照ファイル

| 話題 | 参照するファイル |
|---|---|
| 人生・キャリア・意思決定 | `me/profile.md`, `me/principles.md`, `goals/2026.md`, `decisions/log.md` |
| 強み・自己理解 | `me/assessments.md`, `me/profile.md` |
| お金・資産・投資 | `finance/review.md`, `me/profile.md` |
| Amazon支出分析 | `finance/amazon/matched_report.md`, `finance/amazon/amazon_orders.json` |
| 健康・筋トレ | `health/goals.md`, `health/log.md` |
| 人間関係 | `relationships/key-people.md`, `me/profile.md` |
| 学習・読書 | `learning/books.md` |
| 今週の振り返り | `context/now.md`, `goals/2026.md` |

## Claudeへの指示

- **まず `context/now.md` を読む**。今週何に集中しているかを把握してから回答する
- 「一般論」より「この人の状況に合った具体的なアドバイス」を優先する
- 逆質問を積極的に使って、より深い文脈を引き出す
- `me/principles.md` の原則を尊重した上でアドバイスする
- 重要な意思決定は `decisions/log.md` への記録を提案する

## スキル一覧

| スキル | 起動キーワード | 概要 |
|---|---|---|
| `setup-life-os` | 「セットアップ」「使い方」 | 初回セットアップガイド |
| `life-advisor` | 「相談」「悩み」「どうすれば」 | 人生・キャリア相談 |
| `zaim-advisor` | 「お金」「資産」「投資」「家計」 | 財務アドバイス |
| `zaim-categorize` | 「仕分け」「未分類」 | Zaim未分類の一括処理 |
| `amazon-analyzer` | 「Amazon」「購入履歴」「何買ってる」 | Amazon支出分析・Zaim照合 |
| `fitness-advisor` | 「筋トレ」「健康」「ダイエット」 | 健康・運動アドバイス |
| `self-discovery` | 「自己分析」「プロフィール更新」 | インタビュー形式で自己理解 |
| `weekly-review` | 「週次レビュー」「今週の振り返り」 | 週次振り返り |
| `monthly-review` | 「月次レビュー」「今月の振り返り」 | 月次振り返り |
| `ingest-document` | 「PDFを読んで」「診断結果を取り込んで」 | PDF等をMarkdownに構造化 |
