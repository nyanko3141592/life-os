# Amazon注文履歴 × Zaim 連携

AmazonでのZaim取引を「Amazon」の一括記録から商品名レベルに詳細化するツール群。

## スクリプト一覧

| スクリプト | 役割 |
|---|---|
| `parse_orders.py` | AmazonからダウンロードしたCSVをJSONに変換 |
| `scrape_orders.py` | Cookieを使ってAmazon注文履歴をスクレイピング |
| `match_zaim.py` | Amazon注文 × Zaim取引を日付・金額で照合 |
| `analyze.py` | カテゴリ別・月別の購入分析 |

## 典型的なワークフロー

### ① CSV取得（推奨・確実）

```bash
# 1. amazon.co.jp → アカウント → 注文履歴 → 注文履歴レポートをリクエスト
# 2. CSVをダウンロード

python parse_orders.py --csv ~/Downloads/order_history.csv --summary
```

### ② スクレイピング（自動化したい場合）

```bash
# Chromeで amazon.co.jp にログイン後、Cookie拡張でエクスポート
python scrape_orders.py --cookies ~/cookies.txt --year 2025
```

### ③ Zaimと照合

```bash
# Zaimデータを取得（まだなければ）
python ../zaim/auth.py

# 照合
python match_zaim.py \
  --zaim ../zaim/data.json \
  --amazon amazon_orders.json

# レポートを確認
cat matched_report.md
```

### ④ 分析

```bash
python analyze.py --amazon amazon_orders.json --year 2025 --export-md analysis_2025.md
```

## 依存パッケージ

```bash
pip install requests beautifulsoup4 lxml
```

## 注意事項

- `cookies.txt` はgitignoreされています（個人情報を含むため）
- AmazonのCSVは `finance/amazon/*.csv` もgitignoreされています
- スクレイピングはAmazonの利用規約に注意してください
