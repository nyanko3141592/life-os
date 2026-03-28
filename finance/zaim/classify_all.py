#!/usr/bin/env python3
"""Classify all uncategorized Zaim transactions."""

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session

load_dotenv(Path(__file__).parent.parent.parent / ".env")

CONSUMER_KEY = os.environ["ZAIM_CONSUMER_KEY"]
CONSUMER_SECRET = os.environ["ZAIM_CONSUMER_SECRET"]

# Category/Genre mapping (category_id, genre_id)
CAT_FOOD = (101, 35738172)
CAT_EATING_OUT = (101, 35738175)
CAT_CAFE = (101, 10102)
CAT_GROCERY = (101, 10101)
CAT_CONVENIENCE = (101, 10199)
CAT_DAILY = (65832134, 35738148)
CAT_DRUGSTORE = (65832134, 35738182)
CAT_TELECOM = (65832136, 35738150)
CAT_INTERNET = (65832136, 35738159)
CAT_MOBILE = (65832136, 35738166)
CAT_BOOKS = (65832137, 35738151)
CAT_TRANSPORT = (65832139, 35738154)
CAT_TRANSPORT_OTHER = (65832139, 35738158)
CAT_TAXI = (65832139, 35738171)
CAT_HOBBY = (65832140, 35738163)
CAT_GAME = (65832140, 35738164)
CAT_MATCHING = (65832140, 35738174)
CAT_GADGET = (65832140, 35738156)
CAT_MANGA = (108, 10805)
CAT_CLOTHING = (65832142, 35738183)
CAT_BEAUTY = (65832142, 35738161)
CAT_SPECIAL = (65832146, 35738196)
CAT_FURNITURE = (65832146, 35738179)
CAT_CARD = (65832144, 35738167)
CAT_EMONEY = (65832144, 35738198)
CAT_SOCIAL = (107, 35738152)
CAT_MEDICAL = (65832145, 35738169)
CAT_PHARMACY = (65832145, 35738177)
CAT_OTHER = (199, 35738160)
CAT_RENT = (65832133, 35738146)   # 住居・住宅 > 家賃


def classify_debit_store(store_code):
    """Classify by debit store code (from 'デビット1 XXXXXX STORECODE' pattern)."""
    s = store_code.upper()

    # 外食
    eat_stores = [
        'SAIZERIY', 'SAIZERIA',  # サイゼリヤ
        'MOS BURG', 'MOSBURG',   # モスバーガー
        'YAYOIKEN',              # やよい軒
        'HANAMARU',              # はなまるうどん
        'STARBUCK',              # スタバ
        'EXCELSIO',              # エクセルシオール
        'KENTUCKY',              # KFC
        'DOMINO S', 'DOMINOS',   # ドミノピザ
        'SUBWAY T', 'SUBWAY W',  # サブウェイ
        'PIZZERIA',              # ピッツェリア
        'HIDAKAYA',              # 日高屋
        'GENKAYAT',              # 玄海? or 元気寿司?
        'TORIKIZO',              # 鳥貴族
        'KANTIPUR',              # カンティプール（ネパール料理）
        'DINII*GR',              # Dinii（レストラン決済）
        'JMS THAL',              # ターリー屋
        'SOREYUKE',              # それゆけ！
        'KAIKATSU',              # 快活CLUB？ or 外食
        'ROKKATEI',              # 六花亭（スイーツ）
        'TOMAKOMA',              # 飲食
        'SANTOKU',               # さんとく（スーパー）→ 食料品
        'TSUKIJIG',              # 築地市場系
        'MATUOKA',               # 松岡
        'HAKODATE',              # 函館朝市系
        'MISTER D', 'MISTERD',   # ミスタードーナツ
        '7594 GYO',              # 餃子系？
        'BAR LEGE',              # バー
        'OMIYA GA',              # 大宮ガレリア（外食ゾーン）
    ]
    for k in eat_stores:
        if k in s:
            return CAT_EATING_OUT

    # さんとく → スーパー（食料品）
    if 'SANTOKU' in s:
        return CAT_GROCERY

    # カフェ
    if 'STARBUCK' in s or 'EXCELSIO' in s or 'KAFUE' in s:
        return CAT_CAFE

    # コンビニ
    if 'MINISTOP' in s or 'SEICOMAR' in s:
        return CAT_CONVENIENCE

    # 映画
    if 'TOHO CIN' in s:
        return CAT_GAME

    # 家具・インテリア
    if 'NITORI' in s or 'HONDEPOC' in s:
        return CAT_FURNITURE

    # Amazon
    if 'AMAZON D' in s or 'AMAZON R' in s or 'AMAZON.C' in s or 'AMAZON C' in s:
        return CAT_DAILY

    # 楽天
    if 'RAKUTENP' in s or 'RAKUTEN' in s:
        return CAT_DAILY

    # ドン・キホーテ
    if 'DONQUIJO' in s:
        return CAT_DAILY

    # ドラッグストア
    if 'CREATE S' in s:
        return CAT_DRUGSTORE

    # 交通・フェリー
    if 'SEIKANFE' in s or 'NIHONKUR' in s:
        return CAT_TRANSPORT_OTHER

    # 旅行（じゃらん）
    if 'JALAN NE' in s:
        return CAT_SPECIAL

    # メルカリ
    if 'MERUKARI' in s:
        return CAT_DAILY

    # フリュー（クレーンゲーム・プリクラ）
    if 'FURYU SH' in s:
        return CAT_HOBBY

    # 早稲田（大学関連）
    if 'WASEDADA' in s or 'WASEDA C' in s or 'WASEDA U' in s or 'NISHIWAS' in s:
        return CAT_OTHER

    # 印刷
    if 'ACCEA TA' in s:
        return CAT_OTHER

    # 靴・衣服
    if 'SHOEPLAZ' in s or 'OKADAYA' in s or 'ISHINNDO' in s:
        return CAT_CLOTHING

    # SKY LARK（ガスト等）
    if 'SUKAIRA' in s or 'SKAYRAー' in s or 'SUKAIRAー' in s:
        return CAT_EATING_OUT

    # BIGBOX（東急ハンズ等）
    if 'BIGBOX T' in s:
        return CAT_DAILY

    # PAYMENT（電子マネー等）
    if 'PAYMENTー' in s or 'PAYMENT-' in s:
        return CAT_EMONEY

    # KINSHICH（錦糸町？）→ 不明なのでその他
    if 'KINSHICH' in s:
        return CAT_OTHER

    # 慶應病院？
    if 'KEIOGIJU' in s:
        return CAT_MEDICAL

    # ZIP（クラブ？）
    if ' ZIP' in s:
        return CAT_HOBBY

    # JUNE COR（飲食？）
    if 'JUNE COR' in s:
        return CAT_EATING_OUT

    # ニジュウヨン（24時間系スーパー？）
    if 'NIJUYOMM' in s:
        return CAT_GROCERY

    # HONATSUG（本厚木）
    if 'HONATSUG' in s:
        return CAT_OTHER

    # EKUBODO（絵具堂？美術用品）
    if 'EKUBODO' in s:
        return CAT_HOBBY

    # ATOREYOT（店名不明）
    if 'ATOREYOT' in s:
        return CAT_OTHER

    # SHIBUYA（渋谷の何か）
    if 'SHIBUYA' in s:
        return CAT_OTHER

    # MACHIDA
    if 'MACHIDA' in s:
        return CAT_OTHER

    # MOHEJI（もへじ→食品）
    if 'MOHEJI H' in s:
        return CAT_GROCERY

    return None


def classify(name):
    """Classify a transaction by its name."""
    n = name.upper()

    # === デビット取引 ===
    if name.startswith('デビット1') or name.startswith('デビット2'):
        parts = name.split(' ')
        if len(parts) >= 3:
            store = ' '.join(parts[2:])
            result = classify_debit_store(store)
            if result:
                return result
        # デビットのうちさんとく
        if 'SANTOKU' in n:
            return CAT_GROCERY
        return CAT_OTHER  # デビット未分類はその他

    # === 書籍・漫画 ===
    manga_kw = ['コミックス', 'コミック', 'ジャンプ', 'マガジン', 'チャンピオン',
                'まんがタイム', 'ゼノンコミックス', 'メテオCOMICS', 'バンチコミックス',
                'ヤングアニマル', 'モーニング', 'アフタヌーン', 'ビッグコミック',
                'kindle', 'Kindle']
    if any(k in name for k in manga_kw):
        return CAT_MANGA

    if '販売:' in name and any(k in name for k in ['株式会社集英社', '株式会社 講談社',
            'Amazon Services International LLC', 'スクウェア・エニックス',
            '株式会社KADOKAWA']):
        if any(k in name for k in ['巻', '（', '】']):
            return CAT_MANGA
        return CAT_BOOKS

    # 漫画（Kindle）無料
    if 'Kindle 版' in name and '温度差女子' in name:
        return CAT_MANGA

    # === 外食 ===
    eat_kw = ['トリキ', 'MARUGAME', 'ROYAL HO', 'MCDONALD', 'マクドナルド',
              'MATSUNOYA', 'SUKIYA', 'GYUUKAKU', 'YOSHINOY', 'HAMAZUSH',
              'DENIーZU', 'IKINARIS', 'スシロー', 'COCO', 'ココイチ',
              'HOTPEPPE', 'PESHAWAR', 'TORYU GI', 'サイゼリヤ', 'やよい軒',
              'ミスタードーナツ', 'ミスドーナツ']
    if any(k in n for k in eat_kw):
        return CAT_EATING_OUT

    # カフェ
    cafe_kw = ['KAFUE DO', 'MORI BUI', 'スターバックス', 'STARBUCKS', 'TULLYS',
               'ドトール', 'KOMEDA', 'コメダ']
    if any(k in n for k in cafe_kw):
        return CAT_CAFE

    # コンビニ
    if any(k in n for k in ['SEVENーEL', 'SEVEN-EL', 'FAMILYMA', 'LAWSON', 'ローソン', 'MINISTOP']):
        return CAT_CONVENIENCE

    # スーパー・食料品
    grocery_kw = ['YORK MAR', 'MYBASKET', 'MARUETSU', 'SOUDAISE', 'SEIYU',
                  'SUMMIT', 'マルエツ', 'イオン', 'AEON', 'ザバス', 'SAVAS',
                  'ROKKATEI', '六花亭', 'ロッテ', 'おせち', '越後製菓']
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
    if 'SEIKANFE' in n:
        return CAT_TRANSPORT_OTHER

    # === 通信費 ===
    if 'ラクテンモバイル' in name or 'RAKUTEN MOBILE' in n:
        return CAT_MOBILE
    if any(k in n for k in ['CLOUDFLARE', 'FLY.IO', 'ANTHROPIC', 'GOOGLE',
                             'OPENAI', 'VERCEL', 'HEROKU', 'AWS', 'GITHUB']):
        return CAT_INTERNET
    if 'X CORP' in n or 'TWITTER' in n:
        return CAT_TELECOM
    if 'XAI LLC' in n or 'X.AI' in n:
        return CAT_INTERNET  # Grok AI
    if 'DISCORD' in n:
        return CAT_INTERNET
    if 'PRIME ME' in n:
        return CAT_INTERNET
    if 'COKE ON' in name or 'Coke ON' in name:
        return CAT_CONVENIENCE

    # === マッチングアプリ ===
    if 'BUMBLE' in n or 'TINDER' in n or 'PAIRS' in n:
        return CAT_MATCHING

    # === ドラッグストア ===
    if any(k in n for k in ['SUGI PHA', 'DAIKOKU', 'マツモトキヨシ', 'WELCIA', 'CREATE S']):
        return CAT_DRUGSTORE

    # === 100均・日用品 ===
    if 'DAISO' in n or 'ダイソー' in n or 'SERIA' in n:
        return CAT_DAILY

    # NITORI
    if 'NITORI' in n or 'ニトリ' in name:
        return CAT_FURNITURE

    # === ガジェット・電子機器 ===
    gadget_kw = ['iPhone', 'iphone', 'スマホ', 'スマートウォッチ', 'ワイヤレス',
                 'USB', 'Type-C', 'TypeーC', 'Bluetooth', 'イヤホン', 'マウス',
                 'ヘッドホン', 'MagSafe', 'magsafe', 'ガラスフィルム', 'ELEGOO',
                 'フィラメント', '3Dプリンタ', '充電器', 'ケーブル', 'スピーカー',
                 'ロジクール', 'Anker', 'Xiaomi', 'INNOCN']
    if any(k in name for k in gadget_kw):
        return CAT_GADGET

    # === 家具・家電 ===
    furniture_kw = ['ベッド', 'すのこ', 'マットレス', 'シーツ', '掛けふとん', '布団',
                    '掃除機', 'ロボット掃除機', 'モップ', 'ゴミ箱', 'ダンボール',
                    'フロアタイル', 'パネルヒーター', 'ダンベル', 'クッション',
                    'ダンベル', '座布団', '浄水カートリッジ', '電球', 'ヒーター']
    if any(k in name for k in furniture_kw):
        return CAT_FURNITURE

    # === 衣類・美容 ===
    clothing_kw = ['セーター', 'ジャケット', 'ブレザー', 'カーディガン', 'シャツ',
                   'ポロシャツ', 'ワイドパンツ', 'スラックス', 'スリッポン', 'スニーカー',
                   '靴', 'リュック', 'バッグ', 'ショルダー', 'サンダル', 'ブーツ',
                   '帯', '浴衣', '着物', 'T シャツ', 'Tシャツ', '日傘', 'カバー',
                   'ケース', 'ストラップ', 'カチューシャ', 'ヘアバンド']
    if any(k in name for k in clothing_kw):
        return CAT_CLOTHING

    # === 化粧品・美容 ===
    beauty_kw = ['リップ', '口紅', 'ルージュ', 'ジェルネイル', 'ネイル', 'ボディ',
                 'スクラブ', 'ミルク', 'ニベア', 'rom&nd', 'ロムアンド', 'コスメ',
                 'MilleFee', 'ボディミルク']
    if any(k in name for k in beauty_kw):
        return CAT_BEAUTY

    # === ゲーム・趣味・娯楽 ===
    hobby_kw = ['ディズニープラス', 'ディズニー・プラス', 'Disney', 'DISNEY',
                'ゲーミング', 'マウスパッド', 'ゲーム', 'アニメ']
    if any(k in name for k in hobby_kw):
        return CAT_GAME

    # Amazon物販 (販売: Amazon.co.jp or 他の販売者)
    if '販売:' in name and 'Amazon' in name:
        return CAT_DAILY
    if '販売:' in name:
        return CAT_DAILY

    # === 楽天 ===
    if 'RAKUTENT' in n or 'RAKUTEN ' in n or 'RAKUTENP' in n:
        return CAT_DAILY

    # === メルカリ ===
    if 'MERCARI' in n or 'MERUKARI' in n:
        return CAT_DAILY

    # === ディズニー ===
    if 'DISNEY' in n:
        return CAT_HOBBY

    # === AliExpress ===
    if 'ALIEXPRE' in n:
        return CAT_DAILY

    # === AIRBNB ===
    if 'AIRBNB' in n:
        return CAT_SPECIAL

    # === ことら送金（個人送金）===
    if 'ことら送金' in name:
        return CAT_SOCIAL

    # === 口座振替 ===
    if '口座振替' in name:
        return CAT_CARD

    # === QUICPay ===
    if 'AP/QP/' in name:
        qp_name = name.replace('AP/QP/', '')
        if any(k in qp_name for k in ['プラスタ', 'ジエイアールプラス', 'JR']):
            return CAT_TRANSPORT
        return CAT_OTHER

    # テレビ
    if 'テレビ' in name:
        return CAT_GAME

    # 印刷
    if 'アクセア' in name:
        return CAT_OTHER

    # INFORICH
    if 'INFORICH' in n:
        return CAT_OTHER

    # PayPay
    if 'PAYPAY' in n or 'ペイペイ' in name:
        return CAT_EMONEY

    # 物販
    if name == '物販':
        return CAT_OTHER

    # 購入 プレフィックスのもの
    if name.startswith('購入 '):
        item = name[3:]
        if 'ディズニー' in item or 'Disney' in item:
            return CAT_GAME
        if 'DISCORD' in item.upper() or 'NITRO' in item.upper():
            return CAT_INTERNET
        if 'ノート' in item:
            return CAT_BOOKS
        if '弁護士' in item or '相談' in item:
            return CAT_SPECIAL
        return CAT_OTHER

    # 電池・消耗品
    if '電池' in name or 'バッテリー' in name:
        return CAT_DAILY

    # 撮影ボックス・照明
    if '撮影ボックス' in name or 'スタジオ' in name:
        return CAT_HOBBY

    # スケール・計量
    if 'スケール' in name or 'はかり' in name:
        return CAT_DAILY

    # POPスタンド
    if 'スタンド' in name:
        return CAT_OTHER

    # ピペット
    if 'ピペット' in name or 'スポイト' in name:
        return CAT_OTHER

    # 懐中電灯
    if '懐中電灯' in name or 'ライト' in name or 'フラッシュライト' in name:
        return CAT_DAILY

    # ヘッドホンスタンド
    if 'ヘッドホン スタンド' in name:
        return CAT_DAILY

    # 浄水カートリッジ
    if '浄水' in name:
        return CAT_DAILY

    return None


def cat_name(cat_id, genre_id):
    """Return human-readable category name."""
    mapping = {
        (101, 35738172): "食費",
        (101, 35738175): "外食",
        (101, 10102): "カフェ",
        (101, 10101): "食料品",
        (101, 10199): "コンビニ",
        (65832134, 35738148): "日用品",
        (65832134, 35738182): "ドラッグストア",
        (65832136, 35738150): "情報サービス",
        (65832136, 35738159): "インターネット",
        (65832136, 35738166): "携帯",
        (65832137, 35738151): "書籍",
        (65832139, 35738154): "電車",
        (65832139, 35738158): "交通費",
        (65832139, 35738171): "タクシー",
        (65832140, 35738163): "趣味・娯楽",
        (65832140, 35738164): "映画・音楽・ゲーム",
        (65832140, 35738174): "マッチング",
        (65832140, 35738156): "ガジェット",
        (108, 10805): "漫画",
        (65832142, 35738183): "衣服",
        (65832142, 35738161): "美容",
        (65832146, 35738196): "特別支出",
        (65832146, 35738179): "家具・家電",
        (65832144, 35738167): "カード引き落とし",
        (65832144, 35738198): "電子マネー",
        (107, 35738152): "交際費",
        (65832145, 35738169): "医療費",
        (65832145, 35738177): "薬",
        (199, 35738160): "雑費",
        (65832133, 35738146): "家賃",
    }
    return mapping.get((cat_id, genre_id), f"{cat_id}/{genre_id}")


def main():
    with open('tokens.json') as f:
        tokens = json.load(f)

    session = OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=tokens['oauth_token'],
        resource_owner_secret=tokens['oauth_token_secret'],
    )

    with open('data_full.json') as f:
        data = json.load(f)

    money = data.get('money', [])
    uncat = [m for m in money if m.get('category_id') == 65832135 and m.get('mode') == 'payment']
    print(f"未分類件数: {len(uncat)}")

    classified = 0
    skipped = 0
    errors = 0
    unknown = []

    for m in uncat:
        name = m.get('name', '')
        result = classify(name)
        if result is None:
            skipped += 1
            unknown.append((m['id'], name, m.get('amount', 0), m.get('date', '')))
            continue

        cat_id, genre_id = result
        mid = m['id']

        url = f"https://api.zaim.net/v2/home/money/payment/{mid}"
        params = {
            'category_id': cat_id,
            'genre_id': genre_id,
            'mapping': 1,
        }
        resp = session.put(url, data=params)
        if resp.status_code == 200:
            classified += 1
            print(f"OK  [{cat_name(cat_id, genre_id):12}] {m.get('date','')} {m.get('amount',0):>8}円 {name[:50]}")
        else:
            errors += 1
            print(f"ERR {resp.status_code}: {name[:50]} => {resp.text[:100]}")
            if errors == 1 and resp.status_code == 401:
                print("認証エラー: トークンの再取得が必要")
                break

        if classified % 30 == 0 and classified > 0:
            time.sleep(1)

    print(f"\n=== 結果 ===")
    print(f"更新: {classified}件 / スキップ: {skipped}件 / エラー: {errors}件")

    if unknown:
        print(f"\n=== 分類不能 ({len(unknown)}件) ===")
        for mid, name, amt, date in unknown:
            print(f"  {date} {amt:>8}円  {name[:60]}")


if __name__ == "__main__":
    main()
