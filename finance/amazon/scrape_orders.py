#!/usr/bin/env python3
"""
Amazon.co.jp 注文履歴をスクレイピングで取得する。

【使い方】
1. Chromeで amazon.co.jp にログイン済みの状態にする
2. ブラウザのCookieをエクスポートする:
   - Chrome拡張 "Get cookies.txt LOCALLY" 等でamazon.co.jpのcookies.txtをエクスポート
   - または --session-json でchrome cookiesのJSON形式も可
3. python scrape_orders.py --cookies ~/cookies.txt --year 2025

【依存パッケージ】
pip install requests beautifulsoup4 lxml
"""

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.amazon.co.jp"
ORDERS_URL = f"{BASE_URL}/gp/css/order-history"


def load_cookies_from_txt(cookies_txt_path: str) -> dict:
    """Netscape形式のcookies.txtをdictに変換"""
    cookies = {}
    with open(cookies_txt_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 7:
                cookies[parts[5]] = parts[6]
    return cookies


def load_cookies_from_json(json_path: str) -> dict:
    """JSON形式（Chrome DevToolsエクスポート）のcookiesをdictに変換"""
    with open(json_path) as f:
        cookie_list = json.load(f)
    return {c["name"]: c["value"] for c in cookie_list
            if "amazon.co.jp" in c.get("domain", "")}


def get_session(cookies: dict) -> requests.Session:
    session = requests.Session()
    session.cookies.update(cookies)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9",
    })
    return session


def parse_order_page(html: str) -> list[dict]:
    """注文一覧ページから注文情報を抽出"""
    soup = BeautifulSoup(html, "lxml")
    orders = []

    # 注文グループごとに処理
    order_cards = soup.select(".order, [data-component='orderCard'], .js-order-card")

    # フォールバック: テーブル形式
    if not order_cards:
        order_cards = soup.select(".order-info, .a-box-group")

    for card in order_cards:
        try:
            order = _parse_order_card(card)
            if order:
                orders.append(order)
        except Exception:
            continue

    return orders


def _parse_order_card(card) -> dict | None:
    """個別の注文カードをパース"""
    # 注文番号
    order_id_el = card.select_one(".order-id span:last-child, [data-value]")
    order_id = order_id_el.get_text(strip=True) if order_id_el else ""

    # 注文日
    date_el = card.select_one(".order-date span:last-child, .a-color-secondary")
    date_str = date_el.get_text(strip=True) if date_el else ""

    # 合計金額
    amount_el = card.select_one(".order-total span:last-child, .a-color-price")
    amount_str = amount_el.get_text(strip=True) if amount_el else "0"
    amount = int(re.sub(r"[^\d]", "", amount_str) or 0)

    # 商品名（複数ある場合はリスト）
    items = []
    item_links = card.select(".a-link-normal[href*='/dp/']")
    for link in item_links:
        title = link.get_text(strip=True)
        asin_match = re.search(r"/dp/([A-Z0-9]{10})", link.get("href", ""))
        asin = asin_match.group(1) if asin_match else ""
        if title:
            items.append({"title": title, "asin": asin})

    if not items and not order_id:
        return None

    return {
        "date": date_str,
        "order_id": order_id,
        "amount": amount,
        "items": items,
        "item_count": len(items),
    }


def fetch_orders(session: requests.Session, year: int, pages: int = 10) -> list[dict]:
    """指定年の注文を全ページ取得"""
    all_orders = []
    start_index = 0

    print(f"📦 {year}年の注文を取得中...")

    for page in range(pages):
        params = {
            "opt": "ab",
            "digitalOrders": "1",
            "unifiedOrders": "1",
            "returnTo": "",
            "orderFilter": f"year-{year}",
            "startIndex": start_index,
        }

        try:
            resp = session.get(ORDERS_URL, params=params, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  Error on page {page + 1}: {e}")
            break

        orders = parse_order_page(resp.text)
        if not orders:
            print(f"  ページ {page + 1}: 注文なし（終了）")
            break

        all_orders.extend(orders)
        print(f"  ページ {page + 1}: {len(orders)} 件取得（累計: {len(all_orders)} 件）")

        # 次ページがあるか確認
        soup = BeautifulSoup(resp.text, "lxml")
        next_btn = soup.select_one(".a-last:not(.a-disabled)")
        if not next_btn:
            break

        start_index += len(orders)
        time.sleep(1.5)  # レート制限対策

    return all_orders


def flatten_for_analysis(orders: list[dict]) -> list[dict]:
    """注文を商品単位にフラット化（parse_orders.pyと同じ形式に変換）"""
    from parse_orders import categorize_by_name
    flat = []
    for order in orders:
        if order["items"]:
            for item in order["items"]:
                flat.append({
                    "date": order["date"],
                    "order_id": order["order_id"],
                    "title": item["title"],
                    "asin": item["asin"],
                    "amount": order["amount"] // max(len(order["items"]), 1),  # 按分
                    "inferred_category": categorize_by_name(item["title"]),
                })
        else:
            flat.append({
                "date": order["date"],
                "order_id": order["order_id"],
                "title": f"注文 {order['order_id']}",
                "asin": "",
                "amount": order["amount"],
                "inferred_category": "その他",
            })
    return flat


def main():
    parser = argparse.ArgumentParser(description="Amazon注文履歴スクレイパー")
    parser.add_argument("--cookies", help="Netscape形式のcookies.txtパス")
    parser.add_argument("--cookies-json", help="JSON形式のcookiesパス")
    parser.add_argument("--year", type=int, default=datetime.now().year, help="取得する年")
    parser.add_argument("--pages", type=int, default=20, help="最大ページ数")
    parser.add_argument("--output", default="amazon_orders_scraped.json")
    args = parser.parse_args()

    if not args.cookies and not args.cookies_json:
        print("Error: --cookies または --cookies-json を指定してください")
        print("\n【Cookieの取得方法】")
        print("1. Chromeで amazon.co.jp にログイン")
        print("2. Chrome拡張 'Get cookies.txt LOCALLY' をインストール")
        print("3. amazon.co.jp で拡張のアイコンをクリック → Export")
        print("4. --cookies <保存先パス> で指定")
        return

    if args.cookies:
        cookies = load_cookies_from_txt(args.cookies)
    else:
        cookies = load_cookies_from_json(args.cookies_json)

    print(f"✓ {len(cookies)} 個のCookieを読み込みました")

    session = get_session(cookies)
    orders = fetch_orders(session, args.year, args.pages)

    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

    print(f"\n✓ {len(orders)} 件の注文を {output_path} に保存しました")


if __name__ == "__main__":
    main()
