# バージョンを指定
FROM python:3.10
# サーバーの中でbotを動かす作業ディレクトリを指定
WORKDIR /bot
# 使用ライブラリ一覧を作業ディレクトリにコピー
COPY requirements.txt /bot/
# ライブラリをダウンロード
RUN pip install -r requirements.txt
# `flyctl deploy`を実行したディレクトリの中身とライブラリを作業ディレクトリにコピー
COPY . /bot
# 作業ディレクトリでbotを実行
CMD python chatbot.py