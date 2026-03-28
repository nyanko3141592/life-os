#!/usr/bin/env python3
"""
Amazon注文履歴とZaim取引データを照合して、
Amazonの「Amazon」一括取引を商品名レベルで詳細化する。

【使い方】
1. Zaimデータを取得:
   python ../zaim/auth.py  # データを data.json に保存

2. Amazon注文を取得（どちらか）:
   python parse_orders.py --csv ~/Downloads/order_history.csv
   python scrape_orders.py --cookies ~/cookies.txt --year 2025

3. 照合実行:
   python match_zaim.py --zaim ../zaim/data.json --amazon amazon_orders.json

4. 結果確認:
   cat matched_report.md
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


def load_zaim_payments(zaim_json_path: str) -> list[dict]:
    """Zaimのmoney APIレスポンスから支払い(payment)を抽出"""
    with open(zaim_json_path, encoding="utf-8") as f:
        data = json.load(f)

    payments = []
    for record in data.get("money", []):
        if record.get("type") != "payment":
            continue
        payments.append({
            "id": record["id"],
            "date": record["date"],
            "amount": abs(record.get("amount", 0)),
            "name": record.get("name", ""),
            "place": record.get("place", ""),
            "category_id": record.get("category_id"),
            "genre_id": record.get("genre_id"),
            "comment": record.get("comment", ""),
        })
    return payments


def load_amazon_orders(amazon_json_path: str) -> list[dict]:
    with open(amazon_json_path, encoding="utf-8") as f:
        return json.load(f)


def is_amazon_transaction(payment: dict) -> bool:
    """ZaimレコードがAmazon関連かどうか判定"""
    name = (payment.get("name") or "").upper()
    place = (payment.get("place") or "").upper()
    return any(k in name or k in place for k in [
        "AMAZON", "アマゾン", "マーケットプレイス"
    ])


def parse_date(date_str: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%m/%d/%Y",
                "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(date_str[:10], fmt[:8] if len(fmt) > 8 else fmt)
        except ValueError:
            continue
    # 日本語の日付パース
    import re
    m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", date_str)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def match_transactions(zaim_payments: list[dict],
                       amazon_orders: list[dict],
                       date_tolerance_days: int = 5,
                       amount_tolerance: int = 100) -> list[dict]:
    """
    ZaimのAmazon取引とAmazon注文を照合する。
    日付（前後N日）と金額（±X円）で一致を判定。
    """
    amazon_payments = [p for p in zaim_payments if is_amazon_transaction(p)]
    print(f"ZaimのAmazon取引: {len(amazon_payments)} 件")
    print(f"Amazon注文: {len(amazon_orders)} 件")

    matches = []
    unmatched_zaim = []
    unmatched_amazon = list(amazon_orders)

    for payment in amazon_payments:
        zaim_date = parse_date(payment["date"])
        if not zaim_date:
            unmatched_zaim.append(payment)
            continue

        best_match = None
        best_date_diff = float("inf")

        for order in unmatched_amazon:
            order_date = parse_date(order.get("date", ""))
            if not order_date:
                continue

            date_diff = abs((zaim_date - order_date).days)
            if date_diff > date_tolerance_days:
                continue

            order_amount = order.get("amount", 0)
            zaim_amount = payment["amount"]
            amount_diff = abs(zaim_amount - order_amount)

            if amount_diff <= amount_tolerance:
                if date_diff < best_date_diff:
                    best_match = order
                    best_date_diff = date_diff

        if best_match:
            matches.append({
                "zaim": payment,
                "amazon": best_match,
                "date_diff_days": best_date_diff,
            })
            unmatched_amazon.remove(best_match)
        else:
            unmatched_zaim.append(payment)

    return matches, unmatched_zaim, unmatched_amazon


def generate_report(matches, unmatched_zaim, unmatched_amazon) -> str:
    lines = ["# Amazon × Zaim 照合レポート\n"]
    lines.append(f"- 照合成功: **{len(matches)} 件**")
    lines.append(f"- Zaim側で未照合: {len(unmatched_zaim)} 件")
    lines.append(f"- Amazon側で未照合: {len(unmatched_amazon)} 件\n")

    lines.append("---\n")
    lines.append("## 照合済み取引\n")
    lines.append("| Zaim日付 | Zaim金額 | Amazon注文日 | 商品名 | 推測カテゴリ |")
    lines.append("|---|---|---|---|---|")

    for m in sorted(matches, key=lambda x: x["zaim"]["date"], reverse=True):
        zaim = m["zaim"]
        amazon = m["amazon"]
        # 商品名（複数アイテムなら最初の1件）
        if isinstance(amazon.get("items"), list) and amazon["items"]:
            title = amazon["items"][0].get("title", "")[:40]
        else:
            title = amazon.get("title", "")[:40]
        category = amazon.get("inferred_category", "")
        lines.append(
            f"| {zaim['date']} | ¥{zaim['amount']:,} | {amazon['date']} "
            f"| {title} | {category} |"
        )

    if unmatched_zaim:
        lines.append("\n---\n")
        lines.append("## Zaim側で未照合のAmazon取引\n")
        lines.append("| 日付 | 金額 | Zaim名称 |")
        lines.append("|---|---|---|")
        for p in unmatched_zaim:
            lines.append(f"| {p['date']} | ¥{p['amount']:,} | {p['name']} |")

    if unmatched_amazon:
        lines.append("\n---\n")
        lines.append("## Amazon側で未照合の注文\n")
        lines.append("| 日付 | 金額 | 商品 |")
        lines.append("|---|---|---|")
        for o in unmatched_amazon[:20]:  # 最大20件
            if isinstance(o.get("items"), list) and o["items"]:
                title = o["items"][0].get("title", "")[:40]
            else:
                title = o.get("title", "")[:40]
            lines.append(f"| {o['date']} | ¥{o.get('amount', 0):,} | {title} |")

    return "\n".join(lines)


def generate_category_breakdown(matches) -> str:
    """照合済み取引をカテゴリ別に集計"""
    by_category: dict[str, list] = {}

    for m in matches:
        amazon = m["amazon"]
        cat = amazon.get("inferred_category", "その他")
        if cat not in by_category:
            by_category[cat] = []
        if isinstance(amazon.get("items"), list) and amazon["items"]:
            title = amazon["items"][0].get("title", "")[:35]
        else:
            title = amazon.get("title", "")[:35]
        by_category[cat].append({
            "title": title,
            "amount": m["zaim"]["amount"],
            "date": m["zaim"]["date"],
        })

    lines = ["\n---\n", "## カテゴリ別Amazon支出\n"]
    total = sum(m["zaim"]["amount"] for m in matches)

    for cat, items in sorted(by_category.items(),
                              key=lambda x: sum(i["amount"] for i in x[1]),
                              reverse=True):
        cat_total = sum(i["amount"] for i in items)
        pct = cat_total / total * 100 if total else 0
        lines.append(f"\n### {cat}  ¥{cat_total:,} ({pct:.1f}%)\n")
        for item in sorted(items, key=lambda x: -x["amount"])[:5]:
            lines.append(f"- {item['date']} ¥{item['amount']:,}  {item['title']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Amazon × Zaim 照合ツール")
    parser.add_argument("--zaim", required=True, help="Zaimデータ JSON (data.json)")
    parser.add_argument("--amazon", required=True, help="Amazon注文 JSON")
    parser.add_argument("--output", default="matched_report.md")
    parser.add_argument("--date-tolerance", type=int, default=5,
                        help="日付の照合許容日数（デフォルト5日）")
    parser.add_argument("--amount-tolerance", type=int, default=100,
                        help="金額の照合許容誤差円（デフォルト100円）")
    args = parser.parse_args()

    for path in [args.zaim, args.amazon]:
        if not Path(path).exists():
            print(f"Error: {path} が見つかりません", file=sys.stderr)
            sys.exit(1)

    zaim_payments = load_zaim_payments(args.zaim)
    amazon_orders = load_amazon_orders(args.amazon)

    matches, unmatched_zaim, unmatched_amazon = match_transactions(
        zaim_payments, amazon_orders,
        date_tolerance_days=args.date_tolerance,
        amount_tolerance=args.amount_tolerance,
    )

    report = generate_report(matches, unmatched_zaim, unmatched_amazon)
    report += generate_category_breakdown(matches)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✓ レポートを {args.output} に保存しました")
    print(f"  照合率: {len(matches)}/{len([p for p in zaim_payments if is_amazon_transaction(p)])} 件")


if __name__ == "__main__":
    main()
