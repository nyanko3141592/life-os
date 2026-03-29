.PHONY: help setup zaim amazon review now install

# デフォルト: ヘルプを表示
help:
	@echo ""
	@echo "  Life OS — よく使うコマンド"
	@echo ""
	@echo "  make setup     初期セットアップ（.envの準備）"
	@echo "  make install   Python依存パッケージをインストール"
	@echo "  make zaim      Zaim最新データを取得"
	@echo "  make amazon    Amazon注文履歴を解析"
	@echo "  make review    月次レビューのサマリーを表示"
	@echo "  make now       context/now.md を表示"
	@echo ""

# 初期セットアップ
setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ .env を作成しました。APIキーを設定してください: .env"; \
	else \
		echo "✅ .env は既に存在します"; \
	fi
	@echo ""
	@echo "次のステップ:"
	@echo "  1. .env を編集して Zaim API キーを設定"
	@echo "  2. make install で依存パッケージをインストール"
	@echo "  3. claude を起動して「セットアップ」と話しかける"

# Python依存パッケージのインストール
install:
	pip install requests requests-oauthlib python-dotenv beautifulsoup4 lxml

# Zaimデータの取得
zaim:
	@echo "📊 Zaimデータを取得中..."
	python finance/zaim/fetch.py
	@echo "✅ finance/zaim/data.json を更新しました"

# Amazon注文履歴の解析
amazon:
	@if [ -z "$(CSV)" ]; then \
		echo "使い方: make amazon CSV=~/Downloads/Your\\ Orders/Retail.OrderHistory.3/Retail.OrderHistory.csv"; \
		echo ""; \
		echo "Amazon注文履歴CSVの取得方法:"; \
		echo "  1. amazon.co.jp → アカウント → データを管理する"; \
		echo "  2. 「データをリクエストする」→「注文履歴」"; \
		echo "  3. 処理完了メールが届いたらダウンロード（1時間〜2日）"; \
	else \
		echo "📦 Amazon注文履歴を解析中..."; \
		python finance/amazon/parse_orders.py --csv $(CSV) --output finance/amazon/amazon_orders.json --summary; \
		echo "✅ finance/amazon/amazon_orders.json を作成しました"; \
	fi

# 最近の月次レビューを表示
review:
	@LATEST=$$(ls monthly/*.md 2>/dev/null | sort | tail -1); \
	if [ -z "$$LATEST" ]; then \
		echo "月次レビューがまだありません。Claude Codeで「月次レビュー」と話しかけてください。"; \
	else \
		cat "$$LATEST"; \
	fi

# context/now.md を表示
now:
	@if [ -f context/now.md ]; then \
		cat context/now.md; \
	else \
		echo "context/now.md がありません。Claude Codeで「セットアップ」と話しかけてください。"; \
	fi
