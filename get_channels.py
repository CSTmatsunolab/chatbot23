import requests
import json
import os
import configparser
import codecs

class my_cfg:
    openai_key = None
    openai_org_id = None
    SLACK_APP_TOKEN = None
    SLACK_BOT_TOKEN = None

# アドレス取得 チャンネルリスト
url_converlist = "https://slack.com/api/conversations.list"
# アドレス取得 各チャンネルの履歴
url_converhist = "https://slack.com/api/conversations.history"
# トークン
def setup_cfg(cfg=my_cfg):
    tmp = configparser.ConfigParser()
    tmp.read("data/config.ini")
    cfg.openai_key = tmp["OPEN_AI"]["key"]
    cfg.openai_org_id = tmp["OPEN_AI"]["organization_ID"]
    cfg.SLACK_APP_TOKEN = tmp["chatbot"]["SLACK_APP_TOKEN"]
    cfg.SLACK_BOT_TOKEN = tmp["chatbot"]["SLACK_BOT_TOKEN"]
    cfg.SLACK_API_TOKEN = tmp["chatbot"]["SLACK_API_TOKEN"]
    return cfg
cfg = setup_cfg()
token = cfg.SLACK_API_TOKEN
headers = {"Authorization": "Bearer " + cfg.SLACK_API_TOKEN}


# 作業フォルダ
work_dir = "slack_data/"

# レスポンスのtextにchannelsを取得。そしてjson形式に持ち替えて取得
response_json = requests.get(
                    url_converlist, 
                    headers=headers).json()
# 例 ： {'ok': True, 'channels': [{...}, {...},

# 見やすさのindentを指定した変換
# indent : 半角スペースの数
channel_json = json.dumps(
                    response_json, 
                    indent = 2)
# 取得内容をチラ見
#print(channel_json)
# 例 ： 
# {
#   "ok": true,
#   "channels": [
#     {
#       "id": "AAAAA",
#       "name": "general",
# ・・・・

# チャンネルごとの特定データを辞書型でコレクション
channeldict = {}

# チャンネル履歴向けの辞書型コレクション
channelhist_dict = {}

# チャンネルごとにイテレートして、下記内容を取得
# channel_iterator ：各チャンネル
# name      : チャンネル名
# id        : 識別子
# topic     : トピック　～ヘッダ向けの記載、作業内容、スケジュールなど
# purpose   : 説明　～その他詳細な内容
for channel_iterator in response_json["channels"]:
    # チャンネル名ごとに生成
    channeldict[channel_iterator["name"]] = {
                        "id"     : channel_iterator["id"], 
                        "topic"  : channel_iterator["topic"], 
                        "purpose": channel_iterator["purpose"]
                    }
    # チャンネル履歴取得向けに生成
    channelhist_dict[channel_iterator["id"]] = channel_iterator["name"]
                    
# 辞書キーでソートして日本語表記をそのまま出力、indentを見やすく整形
# sort_keys    : True 出力が辞書のキーでソートされる
# ensure_ascii : False　非ASCII文字をそのまま出力
# indent       : 半角スペースの数
channel_json_out = json.dumps(
                    channeldict, 
                    sort_keys   = True, 
                    ensure_ascii= False, 
                    indent      = 2)
# 出力内容をチラ見
print(channel_json_out)

# 取得したチャンネルを指定ファイルに書き込むます
path = os.path.join(work_dir, "channels.json")
with open(path, "w") as f:
    f.write(channel_json_out)
# 例 ： channels.json
# {
#   "general": {
#     "id": "AAAAA",
#     "purpose": {
#  ・・・・
# },
# "topic": {
#   ・・・・
# }
#  ・・・・

# 取得したチャンネル名のフォルダ名を生成するます
# channel_name : 各チャンネル
for channel_name in channeldict:
    channel_path = os.path.join(work_dir, channel_name)
    if not os.path.isdir(channel_path):
        os.mkdir(channel_path)
# 例 ：
#  general/
#  random/
#  チャンネル名１/
#  チャンネル名２/
#  ・・・

# チャンネル履歴取得向け処理
for channelhist_itr in channelhist_dict:
    # 各チャンネルごとのペイロード
    # 履歴数は最大値 1000件
    # 履歴の開始日時は指定しない 0
    payload = {
        "channel" : str(channelhist_itr),
        "limit"   : "1000",
        "oldest"  : "0"
    }
    headersAuth = {
    'Authorization': 'Bearer '+ str(token),
    }  
    # レスポンスのtextにchannelsを取得。そしてjson形式に持ち替えて取得
    response_json = requests.get(
                        url_converhist,
                        headers = headersAuth, 
                        params  = payload).json()

    # チャンネルの履歴をmessagesから取得
    messages = response_json["messages"]

    # メッセージ内容をチラ見
    print(messages)

    # 辞書キーでソートして日本語表記をそのまま出力、indentを見やすく整形
    # sort_keys    : True 出力が辞書のキーでソートされる
    # ensure_ascii : False　非ASCII文字をそのまま出力
    # indent       : 半角スペースの数
    channelhist_json = json.dumps(
                        messages, 
                        sort_keys   = True,
                        ensure_ascii= False, 
                        indent      = 2)

    # 各チャンネル履歴をチラ見
    print(channelhist_json)

    # 各チャンネルフォルダに履歴用を記載するjsonを定義
    # 誤操作でファイル名を上書き防止するのため、チャンネルidも付与
    path = os.path.join(
                work_dir, 
                channelhist_dict[channelhist_itr], 
                channelhist_itr + "_channel_hist.json")

    # 取得した各チャンネル履歴を指定ファイルに書き込むます
    with open(path, "w", encoding="utf-8") as f:
        f.write(channelhist_json)

    # 各チャンネルにアップロードしたファイルのアドレスを取得
    url_private_download_list = []
    url_download = "url_private_download"
    files = [file_data.get("files") for file_data in messages if file_data.get("files") is not None]
    for file_ids_list in files:
        for file_id in file_ids_list:
            if url_download in file_id:
                url_private_download_list.append(file_id[url_download])

    # 各チャンネルにアップロードしたファイルを、それぞれのアドレスごとに取得
    for url_private_download in url_private_download_list:
        content = requests.get(
            url_private_download,
            allow_redirects = True,
            headers         = {'Authorization': 'Bearer %s' % token},
            stream          = True
        ).content
        # フォルダを生成してその先にファイルを保存する
        strlist = url_private_download.replace('https://files.slack.com/files-pri/', '').split("/")

        # 各チャンネル以下に、次の3区分に分かれているので踏襲
        # strlist[0] : Slack上で管理されたフォルダパス名
        # strlist[1] : 次のパス名（通常[download]）
        # strlist[2] : 保存するファイル名
        if len(strlist) == 3:
            download_dir = os.path.join(
                                work_dir,
                                channelhist_dict[channelhist_itr], 
                                strlist[0],
                                strlist[1])
            # Slackで管理されたフォルダ名で作成
            if not os.path.isdir(download_dir):
                os.makedirs(download_dir)
            # ローカルの保存先名を決定
            save_path = os.path.join(
                        download_dir,
                        strlist[2])
            # ファイルの保存処理
            with codecs.open(save_path, 'wb') as target_file:
                target_file.write(content)
