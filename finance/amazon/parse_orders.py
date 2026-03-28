#!/usr/bin/env python3
"""
Amazon注文履歴CSVをパースして構造化JSONに変換する。

【CSVの取得方法】
1. amazon.co.jp にログイン
2. アカウント → 注文履歴 → 注文履歴レポートをリクエスト
3. 期間を選択してダウンロード
4. python parse_orders.py --csv ~/Downloads/order_history.csv
"""

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path


# Amazon CSVのカラム名マッピング（日本語 / 英語 両対応）
COLUMN_MAP = {
    "order_date": ["注文日", "Order Date"],
    "order_id": ["注文番号", "Order ID"],
    "title": ["商品名", "Title"],
    "category": ["カテゴリ", "Category"],
    "asin": ["ASIN/ISBN", "ASIN/ISBN"],
    "quantity": ["数量", "Quantity"],
    "amount": ["支払い合計", "Item Total"],
    "shipment_date": ["出荷日", "Shipment Date"],
    "status": ["状態", "Order Status"],
}


def detect_column(header: list[str], keys: list[str]) -> str | None:
    for key in keys:
        if key in header:
            return key
    return None


def parse_amount(value: str) -> int:
    """'¥1,234' → 1234"""
    cleaned = re.sub(r"[¥,$\s,]", "", value)
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        return 0


def categorize_by_name(title: str) -> str:
    """商品名からカテゴリを推測する"""
    t = title.lower()

    # 食品・飲料
    if any(k in t for k in ["プロテイン", "protein", "サプリ", "supplement", "ビタミン",
                              "コーヒー", "お茶", "飲料", "食品", "栄養"]):
        return "サプリ・健康食品"

    # 電子機器・ガジェット
    if any(k in t for k in ["ケーブル", "充電", "usb", "hdmi", "キーボード", "マウス",
                              "イヤホン", "スピーカー", "カメラ", "レンズ", "三脚",
                              "ssd", "hdd", "メモリ", "ルーター", "hub"]):
        return "ガジェット・電子機器"

    # 書籍
    if any(k in t for k in ["【本】", "book", "文庫", "新書", "全集", "辞典",
                              "テキスト", "入門", "実践", "プログラミング"]):
        return "書籍"

    # 衣類
    if any(k in t for k in ["tシャツ", "シャツ", "パンツ", "ジャケット", "スニーカー",
                              "靴", "ソックス", "下着", "ユニクロ"]):
        return "衣類"

    # 日用品・生活用品
    if any(k in t for k in ["洗剤", "シャンプー", "ティッシュ", "トイレ", "掃除",
                              "収納", "電球", "乾電池", "ハンガー"]):
        return "日用品"

    # フィットネス
    if any(k in t for k in ["ダンベル", "バーベル", "プレート", "トレーニング",
                              "ヨガ", "ストレッチ", "筋トレ"]):
        return "フィットネス"

    # ゲーム・エンタメ
    if any(k in t for k in ["ゲーム", "game", "playstation", "nintendo", "xbox",
                              "アニメ", "dvd", "blu-ray"]):
        return "ゲーム・エンタメ"

    # 文具・オフィス
    if any(k in t for k in ["ノート", "ペン", "ファイル", "バインダー", "付箋"]):
        return "文具・オフィス"

    return "その他"


def parse_csv(csv_path: str) -> list[dict]:
    orders = []
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []

        # カラム名を解決
        col = {}
        for key, candidates in COLUMN_MAP.items():
            col[key] = detect_column(header, candidates)

        for row in reader:
            title = row.get(col["title"], "").strip()
            if not title:
                continue

            amount = parse_amount(row.get(col["amount"], "0"))
            order_date = row.get(col["order_date"], "")

            orders.append({
                "date": order_date,
                "order_id": row.get(col["order_id"], "").strip(),
                "title": title,
                "asin": row.get(col["asin"], "").strip(),
                "quantity": int(row.get(col["quantity"], "1") or 1),
                "amount": amount,
                "amazon_category": row.get(col["category"], "").strip(),
                "inferred_category": categorize_by_name(title),
                "status": row.get(col["status"], "").strip(),
            })

    return orders


def summarize(orders: list[dict]) -> dict:
    """カテゴリ別・月別の集計"""
    by_category: dict[str, int] = {}
    by_month: dict[str, int] = {}
    total = 0

    for o in orders:
        cat = o["inferred_category"]
        by_category[cat] = by_category.get(cat, 0) + o["amount"]

        # 日付パース（複数フォーマット対応）
        date_str = o["date"]
        for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%m/%d/%Y", "%Y年%m月%d日"):
            try:
                dt = datetime.strptime(date_str, fmt)
                month_key = dt.strftime("%Y-%m")
                by_month[month_key] = by_month.get(month_key, 0) + o["amount"]
                break
            except ValueError:
                continue

        total += o["amount"]

    return {
        "total": total,
        "count": len(orders),
        "by_category": dict(sorted(by_category.items(), key=lambda x: -x[1])),
        "by_month": dict(sorted(by_month.items())),
    }


def main():
    parser = argparse.ArgumentParser(description="Amazon注文履歴CSVをパース")
    parser.add_argument("--csv", required=True, help="注文履歴CSVのパス")
    parser.add_argument("--output", default="amazon_orders.json", help="出力JSONファイル名")
    parser.add_argument("--summary", action="store_true", help="集計サマリーを表示")
    args = parser.parse_args()

    if not Path(args.csv).exists():
        print(f"Error: {args.csv} が見つかりません", file=sys.stderr)
        sys.exit(1)

    orders = parse_csv(args.csv)
    print(f"✓ {len(orders)} 件の注文を読み込みました")

    output_path = Path(args.csv).parent / args.output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)
    print(f"✓ {output_path} に保存しました")

    if args.summary:
        summary = summarize(orders)
        print(f"\n=== Amazon購入サマリー ===")
        print(f"合計: ¥{summary['total']:,}  ({summary['count']}件)")
        print(f"\n【カテゴリ別】")
        for cat, amount in summary["by_category"].items():
            print(f"  {cat:<20} ¥{amount:>8,}")
        print(f"\n【月別】")
        for month, amount in summary["by_month"].items():
            print(f"  {month}  ¥{amount:>8,}")

    return output_path


if __name__ == "__main__":
    main()
