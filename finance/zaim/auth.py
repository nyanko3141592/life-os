#!/usr/bin/env python3
"""Zaim OAuth 1.0a authentication and data fetcher."""

import json
import os
import webbrowser
from pathlib import Path

from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session

load_dotenv(Path(__file__).parent.parent.parent / ".env")

CONSUMER_KEY = os.environ["ZAIM_CONSUMER_KEY"]
CONSUMER_SECRET = os.environ["ZAIM_CONSUMER_SECRET"]

REQUEST_TOKEN_URL = "https://api.zaim.net/v2/auth/request"
AUTHORIZE_URL = "https://auth.zaim.net/users/auth"
ACCESS_TOKEN_URL = "https://api.zaim.net/v2/auth/access"

TOKEN_FILE = "zaim_tokens.json"


def authenticate():
    """Perform OAuth 1.0a flow and save tokens."""
    # Step 1: Get request token
    oauth = OAuth1Session(CONSUMER_KEY, client_secret=CONSUMER_SECRET, callback_uri="http://localhost")
    fetch_response = oauth.fetch_request_token(REQUEST_TOKEN_URL)
    resource_owner_key = fetch_response.get("oauth_token")
    resource_owner_secret = fetch_response.get("oauth_token_secret")

    # Step 2: Authorize
    authorization_url = oauth.authorization_url(AUTHORIZE_URL)
    print(f"\n以下のURLをブラウザで開いて認証してください:\n{authorization_url}\n")
    webbrowser.open(authorization_url)

    # Step 3: Get verifier from callback
    redirect_response = input("リダイレクトされたURL全体を貼り付けてください: ")
    oauth_response = oauth.parse_authorization_response(redirect_response)
    verifier = oauth_response.get("oauth_verifier")

    # Step 4: Get access token
    oauth = OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier,
    )
    oauth_tokens = oauth.fetch_access_token(ACCESS_TOKEN_URL)

    # Save tokens
    with open(TOKEN_FILE, "w") as f:
        json.dump(oauth_tokens, f, indent=2)
    print(f"トークンを {TOKEN_FILE} に保存しました。")
    return oauth_tokens


def load_tokens():
    """Load saved tokens."""
    try:
        with open(TOKEN_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def get_session(tokens):
    """Create authenticated session."""
    return OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=tokens["oauth_token"],
        resource_owner_secret=tokens["oauth_token_secret"],
    )


def fetch_money_data(session):
    """Fetch recent money records."""
    url = "https://api.zaim.net/v2/home/money"
    params = {"mapping": 1, "limit": 100}
    resp = session.get(url, params=params)
    return resp.json()


def fetch_user(session):
    """Fetch user info."""
    url = "https://api.zaim.net/v2/home/user/verify"
    resp = session.get(url)
    return resp.json()


def main():
    tokens = load_tokens()
    if not tokens:
        print("初回認証を開始します...")
        tokens = authenticate()

    session = get_session(tokens)

    # ユーザー情報
    user = fetch_user(session)
    print(f"\n=== ユーザー情報 ===")
    print(json.dumps(user, indent=2, ensure_ascii=False))

    # 家計簿データ取得
    data = fetch_money_data(session)
    print(f"\n=== 最近の記録（最大100件） ===")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # データをファイルに保存
    with open("zaim_data.json", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("\nデータを zaim_data.json に保存しました。")


if __name__ == "__main__":
    main()
