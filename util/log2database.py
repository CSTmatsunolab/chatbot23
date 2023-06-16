import os
import json
import glob
from datetime import datetime
import vector_db
import configparser

class my_cfg:
    openai_key = None
    openai_org_id = None


def setup_cfg(cfg=my_cfg):
    tmp = configparser.ConfigParser()
    tmp.read("data/config.ini")
    cfg.openai_key = tmp["OPEN_AI"]["key"]
    cfg.openai_org_id = tmp["OPEN_AI"]["organization_ID"]
    return cfg
cfg = setup_cfg()


now = datetime.now().strftime(r"%Y-%m-%d")
target_dir = os.path.join(os.getcwd(),  "logs", now)
file_list = glob.glob(target_dir + "/*.json")
base_data_path = os.path.join(os.getcwd(), "data", "all_data.pkl.gz")
def json_to_database(cfg=cfg): # ベクトル化にopenai apiを使ってるためcfg
    db = vector_db.vector_db(cfg=cfg, target="text")
    db.load(base_data_path)
    for dir in file_list: # フォルダ内のjsonを一つずつ取り出す
        if dir != "channel_list.json": # channel_list.jsonは参照しない
            path = os.path.join(target_dir, dir) # ディレクトリ内のpathを取得
            with open(path) as f:
                data = json.load(f)
            
            for block in data: # json内の発言を一つずつ取得
                if block["user"] != "U0550LX2NG0": # userがチャットボットの時の発言は飛ばす
                    db.add_document(block)
    db.save(base_data_path) # データベースの内容を更新

if __name__ == "__main__":
    json_to_database()