# Amazon注文履歴 × Zaim 連携

AmazonでのZaim取引を「Amazon」の一括記録から商品名レベルに詳細化するツール群。

## スクリプト一覧

| スクリプト | 役割 |
|---|---|
| `parse_orders.py` | AmazonからダウンロードしたCSVをJSONに変換 |
| `match_zaim.py` | Amazon注文 × Zaim取引を日付・金額で照合 |
| `analyze.py` | カテゴリ別・月別の購入分析 |

---

## ① Amazon注文履歴CSVの取得

**所要時間: リクエスト送信5分 + Amazon処理1時間〜2日**

参考: https://aplos.jp/amazon-csv/

### 手順

1. [amazon.co.jp](https://www.amazon.co.jp) にログイン
2. 右上「アカウント＆リスト」→「アカウントサービス」
3. 「データを管理する」→「**データをリクエストする**」
4. 「**注文履歴**」を選択 → 「リクエストを送信」
5. Amazonから確認メールが届く → メール内のリンクをクリックして認証
6. 処理完了メール（件名: 「Amazonデータのダウンロード準備ができました」）を待つ
7. メール内「**データをダウンロード**」をクリック
8. `Your Orders.zip` をダウンロード・展開

### ZIPの中身

```
Your Orders/
├── Digital-Ordering.3/
│   └── Digital Items.csv        ← Kindle・デジタルコンテンツ
└── Retail.OrderHistory.3/
    └── Retail.OrderHistory.csv  ← 通常の通販注文 ← これがメイン
```

---

## ② CSVをパース

```bash
cd finance/amazon

# 通販注文
python parse_orders.py \
  --csv ~/Downloads/Your\ Orders/Retail.OrderHistory.3/Retail.OrderHistory.csv \
  --output amazon_orders.json \
  --summary

# Kindleなどデジタル注文も含める場合
python parse_orders.py \
  --csv ~/Downloads/Your\ Orders/Digital-Ordering.3/Digital\ Items.csv \
  --output amazon_digital_orders.json \
  --summary
```

---

## ③ Zaimと照合

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

---

## ④ 分析

```bash
python analyze.py \
  --amazon amazon_orders.json \
  --year 2025 \
  --export-md analysis_2025.md
```

---

## 依存パッケージ

```bash
pip install requests beautifulsoup4 lxml python-dotenv
```

## gitignore対象（コミットされません）

- `*.csv` — Amazon注文CSVファイル
- `*.json` — パース済みデータ
- `matched_report.md` — 照合レポート
- `cookies.txt` — ブラウザCookie
