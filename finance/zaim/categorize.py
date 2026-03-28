#!/usr/bin/env python3
"""Categorize uncategorized Zaim transactions."""

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session

load_dotenv(Path(__file__).parent.parent.parent / ".env")

CONSUMER_KEY = os.environ["ZAIM_CONSUMER_KEY"]
CONSUMER_SECRET = os.environ["ZAIM_CONSUMER_SECRET"]

# Category/Genre mapping
# (category_id, genre_id)
CAT_FOOD = (101, 35738172)          # 食費 > 食費
CAT_EATING_OUT = (101, 35738175)    # 食費 > 外食
CAT_CAFE = (101, 10102)             # 食費 > カフェ
CAT_GROCERY = (101, 10101)          # 食費 > 食料品
CAT_CONVENIENCE = (101, 10199)      # 食費 > その他食費
CAT_DAILY = (65832134, 35738148)    # 日用品 > 日用品
CAT_DRUGSTORE = (65832134, 35738182)# 日用品 > ドラッグストア
CAT_TELECOM = (65832136, 35738150)  # 通信費 > 情報サービス
CAT_INTERNET = (65832136, 35738159) # 通信費 > インターネット
CAT_MOBILE = (65832136, 35738166)   # 通信費 > その他通信費
CAT_BOOKS = (65832137, 35738151)    # 教養・教育 > 書籍
CAT_TRANSPORT = (65832139, 35738154)# 交通費 > 電車
CAT_TRANSPORT_OTHER = (65832139, 35738158) # 交通費 > 交通費
CAT_TAXI = (65832139, 35738171)     # 交通費 > タクシー
CAT_HOBBY = (65832140, 35738163)    # 趣味・娯楽 > その他趣味・娯楽
CAT_GAME = (65832140, 35738164)     # 趣味・娯楽 > 映画・音楽・ゲーム
CAT_MATCHING = (65832140, 35738174) # 趣味・娯楽 > マッチングアプリ
CAT_GADGET = (65832140, 35738156)   # 趣味・娯楽 > ガジェット
CAT_MANGA = (108, 10805)            # エンタメ > 漫画
CAT_CLOTHING = (65832142, 35738183) # 衣服・美容 > 衣服
CAT_BEAUTY = (65832142, 35738161)   # 衣服・美容 > 美容院・理髪
CAT_SPECIAL = (65832146, 35738196)  # 特別な支出 > その他特別な支出
CAT_FURNITURE = (65832146, 35738179)# 特別な支出 > 家具・家電
CAT_CARD = (65832144, 35738167)     # 現金・カード > カード引き落とし
CAT_EMONEY = (65832144, 35738198)   # 現金・カード > 電子マネー
CAT_SOCIAL = (107, 35738152)        # 交際費
CAT_MEDICAL = (65832145, 35738169)  # 健康・医療 > 医療費
CAT_PHARMACY = (65832145, 35738177) # 健康・医療 > 薬
CAT_OTHER = (199, 35738160)         # その他 > 雑費


def classify(name):
    """Classify a transaction by its name field."""
    n = name.upper()

    # === 書籍・漫画 ===
    manga_kw = ['コミックス', 'コミック', 'ジャンプ', 'マガジン', 'チャンピオン',
                'まんがタイム', 'ゼノンコミックス', 'メテオCOMICS', 'バンチコミックス',
                'ヤングアニマル', 'モーニング', 'アフタヌーン', 'ビッグコミック']
    if any(k in name for k in manga_kw):
        return CAT_MANGA

    # Kindle/電子書籍 (Amazon販売で書名っぽいもの)
    if '販売:' in name and any(k in name for k in ['株式会社集英社', '株式会社 講談社',
            'Amazon Services International LLC', 'スクウェア・エニックス',
            '株式会社KADOKAWA']):
        # 書名判定: 巻数っぽいもの
        if any(k in name for k in ['巻', '（', '】']):
            return CAT_MANGA
        return CAT_BOOKS

    # === 外食 ===
    eat_kw = ['トリキ', 'MARUGAME', 'ROYAL HO', 'MCDONALD', 'マクドナルド',
              'MATSUNOYA', 'SUKIYA', 'GYUUKAKU', 'YOSHINOY', 'HAMAZUSH',
              'DENIーZU', 'IKINARIS', 'スシロー', 'COCO', 'ココイチ',
              'HOTPEPPE', 'PESHAWAR', 'TORYU GI']
    if any(k in n for k in eat_kw):
        return CAT_EATING_OUT

    # カフェ
    cafe_kw = ['KAFUE DO', 'MORI BUI', 'スターバックス', 'STARBUCKS', 'TULLYS',
               'ドトール', 'KOMEDA', 'コメダ']
    if any(k in n for k in cafe_kw):
        return CAT_CAFE

    # コンビニ
    if any(k in n for k in ['SEVENーEL', 'SEVEN-EL', 'FAMILYMA', 'LAWSON', 'ローソン']):
        return CAT_CONVENIENCE

    # スーパー・食料品
    grocery_kw = ['YORK MAR', 'MYBASKET', 'MARUETSU', 'SOUDAISE', 'SEIYU',
                  'SUMMIT', 'LIFE', 'イオン', 'AEON', 'ザバス', 'SAVAS']
    if any(k in n for k in grocery_kw):
        return CAT_GROCERY

    # Uber Eats
    if 'UBERJP_EATS' in n or 'UBER EATS' in n:
        return CAT_EATING_OUT

    # === 交通 ===
    if 'PASMO' in n:
        return CAT_TRANSPORT
    if 'ウーバートリツプ' in name or 'UBER TRIP' in n:
        return CAT_TAXI
    if any(k in n for k in ['NAGOYAEK', 'ODAKIYU', 'JR ', 'WASEDA U']):
        return CAT_TRANSPORT

    # === 通信費 ===
    if 'ラクテンモバイル' in name or 'RAKUTEN MOBILE' in n:
        return CAT_MOBILE
    if any(k in n for k in ['CLOUDFLARE', 'FLY.IO', 'ANTHROPIC', 'GOOGLE',
                             'OPENAI', 'VERCEL', 'HEROKU', 'AWS', 'GITHUB']):
        return CAT_INTERNET
    if 'X CORP' in n or 'TWITTER' in n:
        return CAT_TELECOM
    if 'COKE ON' in name or 'Coke ON' in name:
        return CAT_CONVENIENCE  # 自販機

    # === マッチングアプリ ===
    if 'BUMBLE' in n or 'TINDER' in n or 'PAIRS' in n:
        return CAT_MATCHING

    # === ドラッグストア ===
    if any(k in n for k in ['SUGI PHA', 'DAIKOKU', 'マツモトキヨシ', 'WELCIA']):
        return CAT_DRUGSTORE

    # === 100均・日用品 ===
    if 'DAISO' in n or 'ダイソー' in n or 'SERIA' in n:
        return CAT_DAILY

    # Amazon物販 (販売: Amazon.co.jp or 他の販売者)
    if '販売:' in name and 'Amazon' in name:
        return CAT_DAILY  # Amazonの雑貨はデフォルト日用品

    # === 楽天 ===
    if 'RAKUTENT' in n or 'RAKUTEN ' in n:
        return CAT_DAILY  # 楽天通販はデフォルト日用品

    # === メルカリ ===
    if 'MERCARI' in n:
        return CAT_DAILY

    # === ディズニー ===
    if 'DISNEY' in n:
        return CAT_HOBBY

    # === AliExpress ===
    if 'ALIEXPRE' in n:
        return CAT_DAILY

    # === 口座振替 (カード引き落とし) ===
    if '口座振替' in name:
        return CAT_CARD

    # === QUICPay / AP/QP/ ===
    # QUICPay は場所名から推定
    if 'AP/QP/' in name:
        qp_name = name.replace('AP/QP/', '')
        if any(k in qp_name for k in ['プラスタ', 'ジエイアールプラス', 'JR']):
            return CAT_TRANSPORT
        if any(k in qp_name for k in ['ココロニ']):
            return CAT_MEDICAL  # こころに○○ → 心療内科？いや、ドラッグストアっぽい
        return CAT_OTHER

    # テレビ東京
    if 'テレビ' in name:
        return CAT_GAME

    # 印刷
    if 'アクセア' in name:
        return CAT_OTHER

    # INFORICH = モバイルバッテリー
    if 'INFORICH' in n:
        return CAT_OTHER

    # PayPay
    if 'PAYPAY' in n or 'ペイペイ' in name:
        return CAT_EMONEY

    # PRIME MEMBER
    if 'PRIME ME' in n:
        return CAT_INTERNET

    # 物販 (generic)
    if name == '物販':
        return CAT_OTHER

    return None  # 分類不能


def main():
    with open('zaim_tokens.json') as f:
        tokens = json.load(f)

    session = OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=tokens['oauth_token'],
        resource_owner_secret=tokens['oauth_token_secret'],
    )

    with open('zaim_data.json') as f:
        data = json.load(f)

    money = data.get('money', [])
    uncat = [m for m in money if m.get('category_id') == 65832135 and m.get('mode') == 'payment']

    classified = 0
    skipped = 0
    errors = 0
    results = {}

    for m in uncat:
        name = m.get('name', '')
        result = classify(name)
        if result is None:
            skipped += 1
            continue

        cat_id, genre_id = result
        mid = m['id']

        # カテゴリ名でカウント
        cat_name = f"{cat_id}/{genre_id}"
        results[cat_name] = results.get(cat_name, 0) + 1

        # API で更新
        url = f"https://api.zaim.net/v2/home/money/payment/{mid}"
        params = {
            'category_id': cat_id,
            'genre_id': genre_id,
            'mapping': 1,
        }
        resp = session.put(url, data=params)
        if resp.status_code == 200:
            classified += 1
        else:
            errors += 1
            if errors <= 3:
                print(f"ERROR {resp.status_code}: {resp.text[:200]}")
            if errors == 1 and resp.status_code == 401:
                print("認証エラー: トークンの再取得が必要かもしれません")
                break

        # Rate limit対策
        if classified % 50 == 0:
            print(f"  進捗: {classified}件更新済み...")
            time.sleep(1)

    print(f"\n=== 仕分け結果 ===")
    print(f"更新成功: {classified}件")
    print(f"分類不能（スキップ）: {skipped}件")
    print(f"エラー: {errors}件")
    print(f"\n=== カテゴリ別件数 ===")
    for k, v in sorted(results.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}件")


if __name__ == "__main__":
    main()
