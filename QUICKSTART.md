# QUICKSTART — 5分でLife OSを動かす

## 1. リポジトリをクローン（1分）

```bash
# GitHubで "Use this template" → 自分のリポジトリを作成
# または:
git clone https://github.com/YOUR_USERNAME/life-os your-life-os
cd your-life-os
```

## 2. Claude Codeを起動（30秒）

```bash
claude
```

## 3. セットアップスキルを実行（2分）

Claude Codeに話しかけるだけ:

```
> セットアップ
```

`setup-life-os` スキルが起動し、次のことをガイドします:
- 必要なファイルの確認
- `me/profile.md` の初期化
- `context/now.md` の作成

## 4. まず自分のことを話す（2分）

```
> 自己分析したい
```

`self-discovery` スキルが対話形式で `me/profile.md` を埋めていきます。

---

## これで完了！

あとは普通に話しかけるだけ:

```
> 転職どうすればいいと思う？
> 今月の家計を振り返りたい
> 筋トレメニューを組んで
> 週次レビューしよう
```

---

## Zaim連携（オプション）

家計管理にZaimを使っている場合:

```bash
cp .env.example .env
# .env を編集して ZAIM_CONSUMER_KEY と ZAIM_CONSUMER_SECRET を設定
# 👉 https://dev.zaim.net/ でアプリを作成

pip install requests-oauthlib python-dotenv
python finance/zaim/auth.py  # 初回認証
```

---

## ファイル構造（最低限）

```
your-life-os/
├── me/
│   └── profile.md     ← ★ ここから始める
├── context/
│   └── now.md         ← 毎週更新（今週のフォーカス）
└── CLAUDE.md          ← Claudeへの設定（変更不要）
```

---

詳しい使い方 → [README.md](README.md)
