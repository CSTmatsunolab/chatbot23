import requests
import json
import os

# アドレス取得　ユーザーリスト
url_userlist = "https://slack.com/api/users.list"
# 作業フォルダ
work_dir = "../slack_data/"
# 出力ファイル名
file_user = "list_user.json"

def get_users_from_cfg(cfg):
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