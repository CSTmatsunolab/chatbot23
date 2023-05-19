import requests
import json
import os
import configparser
import codecs
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
class my_cfg:
    openai_key = None
    openai_org_id = None
    SLACK_APP_TOKEN = None
    SLACK_BOT_TOKEN = None

# アドレス取得　ユーザーリスト
url_userlist = "https://slack.com/api/users.list"
# 作業フォルダ
work_dir = "slack_data/"
# 出力ファイル名
file_user = "list_user.json"
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

# ユーザーリスト出力
response_json = requests.get(
                    url_userlist, 
                    headers=headers).json()
user_json_out = json.dumps(
                    response_json, 
                    sort_keys   = True, 
                    ensure_ascii= False, 
                    indent      = 2)
path = os.path.join(work_dir, file_user)
with open(path, "w") as f:
    f.write(user_json_out)
    print('* [usr_list] '+path)