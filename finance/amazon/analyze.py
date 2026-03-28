#!/usr/bin/env python3
"""
Amazon + Zaim の統合分析。
照合レポートJSONと追加のZaimデータから総合的な支出分析を行う。

【使い方】
python analyze.py --amazon amazon_orders.json [--year 2025]
"""

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def load_orders(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_date(s: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"):
        try:
            return datetime.strptime(s[:10], fmt[:10])
        except (ValueError, AttributeError):
            continue
    return None


def analyze(orders: list[dict], year: int | None = None) -> dict:
    if year:
        orders = [
            o for o in orders
            if (d := parse_date(o.get("date", ""))) and d.year == year
        ]

    total = sum(o.get("amount", 0) for o in orders)
    by_category: dict[str, int] = defaultdict(int)
    by_month: dict[str, int] = defaultdict(int)
    by_month_category: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    large_purchases = []

    for o in orders:
        cat = o.get("inferred_category", "その他")
        amount = o.get("amount", 0)
        by_category[cat] += amount

        dt = parse_date(o.get("date", ""))
        if dt:
            month = dt.strftime("%Y-%m")
            by_month[month] += amount
            by_month_category[month][cat] += amount

        if amount >= 5000:
            large_purchases.append(o)

    large_purchases.sort(key=lambda x: -x.get("amount", 0))

    return {
        "year": year,
        "total": total,
        "count": len(orders),
        "monthly_avg": total // max(len(by_month), 1),
        "by_category": dict(sorted(by_category.items(), key=lambda x: -x[1])),
        "by_month": dict(sorted(by_month.items())),
        "large_purchases": large_purchases[:20],
    }


def print_report(result: dict):
    year_str = str(result["year"]) + "年 " if result["year"] else ""
    print(f"\n{'='*50}")
    print(f"  Amazon購入分析 {year_str}({result['count']}件)")
    print(f"{'='*50}")
    print(f"  合計:       ¥{result['total']:>10,}")
    print(f"  月平均:     ¥{result['monthly_avg']:>10,}")

    print(f"\n【カテゴリ別支出】")
    for cat, amount in result["by_category"].items():
        bar = "█" * (amount * 20 // max(result["total"], 1))
        pct = amount * 100 // max(result["total"], 1)
        print(f"  {cat:<20} ¥{amount:>8,}  {pct:>3}%  {bar}")

    print(f"\n【月別推移】")
    max_month_amt = max(result["by_month"].values(), default=1)
    for month, amount in result["by_month"].items():
        bar = "█" * (amount * 25 // max_month_amt)
        print(f"  {month}  ¥{amount:>8,}  {bar}")

    if result["large_purchases"]:
        print(f"\n【高額購入 TOP10】")
        for i, o in enumerate(result["large_purchases"][:10], 1):
            if isinstance(o.get("items"), list) and o["items"]:
                title = o["items"][0].get("title", "")[:35]
            else:
                title = o.get("title", "")[:35]
            print(f"  {i:>2}. {o['date']}  ¥{o.get('amount', 0):>8,}  {title}")


def export_markdown(result: dict, output_path: str):
    lines = [f"# Amazon購入分析\n"]
    year_str = f"{result['year']}年 " if result["year"] else ""
    lines.append(f"**{year_str}合計: ¥{result['total']:,}** / {result['count']}件 / 月平均 ¥{result['monthly_avg']:,}\n")

    lines.append("## カテゴリ別\n")
    lines.append("| カテゴリ | 金額 | 割合 |")
    lines.append("|---|---|---|")
    for cat, amount in result["by_category"].items():
        pct = amount * 100 // max(result["total"], 1)
        lines.append(f"| {cat} | ¥{amount:,} | {pct}% |")

    lines.append("\n## 月別推移\n")
    lines.append("| 月 | 金額 |")
    lines.append("|---|---|")
    for month, amount in result["by_month"].items():
        lines.append(f"| {month} | ¥{amount:,} |")

    if result["large_purchases"]:
        lines.append("\n## 高額購入 TOP10\n")
        lines.append("| 日付 | 金額 | 商品名 |")
        lines.append("|---|---|---|")
        for o in result["large_purchases"][:10]:
            if isinstance(o.get("items"), list) and o["items"]:
                title = o["items"][0].get("title", "")[:40]
            else:
                title = o.get("title", "")[:40]
            lines.append(f"| {o['date']} | ¥{o.get('amount', 0):,} | {title} |")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n✓ Markdownレポートを {output_path} に保存しました")


def main():
    parser = argparse.ArgumentParser(description="Amazon購入分析")
    parser.add_argument("--amazon", required=True, help="amazon_orders.json")
    parser.add_argument("--year", type=int, help="対象年（省略時は全期間）")
    parser.add_argument("--export-md", help="Markdownレポートの出力先")
    args = parser.parse_args()

    orders = load_orders(args.amazon)
    result = analyze(orders, args.year)
    print_report(result)

    if args.export_md:
        export_markdown(result, args.export_md)


if __name__ == "__main__":
    main()
