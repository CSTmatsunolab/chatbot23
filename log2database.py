import os
import json
import glob
from datetime import datetime
from util import vector_db
import configparser
import time
from tqdm import tqdm
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
# now = datetime.now().strftime(r"%Y-%m-%d")
# target_dir = os.path.join(os.getcwd(),  "logs", now)

def json_to_database_from_day(day, cfg=cfg): # ベクトル化にopenai apiを使ってるためcfg
    """ 
    dayディレクトリに対象のjsonファイルが入っていることを想定
    既存のデータベース（data/all_data.pkl.gz）に追記する
    userがチャットボットの場合データベースに入れない
    """
    base_data_path = os.path.join(os.getcwd(), "data", "all_data.pkl.gz")
    db = vector_db(cfg=cfg, target="text")
    db.load(base_data_path)
    target_dir = os.path.join(os.getcwd(),  "logs", day)
    file_list = glob.glob(target_dir + "/*.json")
    for dir in file_list: # フォルダ内のjsonを一つずつ取り出す
        if dir != "channel_list.json": # channel_list.jsonは参照しない
            path = os.path.join(target_dir, dir) # ディレクトリ内のpathを取得
            with open(path) as f:
                data = json.load(f)
            for block in data: # json内の発言を一つずつ取得
                if block["user"] != "U0550LX2NG0": # userがチャットボットの時の発言は飛ばす
                    db.add_document(block)
    db.save(base_data_path) # データベースの内容を更新

    
# target = os.listdir(os.path.join(os.getcwd(), "aaa"))
# file_list = [glob.glob(os.path.join(os.getcwd(), "aaa", i)+"/*.json") for i in target]
# file_list = sum(file_list, [])

def db_from_file_list(file_lists,cfg=cfg):
    """ 
    file_listsはデータベース化したい対象のfileをリストにしたもの
    それらを逐次的に取り出し既存のデータベースに加える
    """
    base_data_path = os.path.join(os.getcwd(), "data", "all_data.pkl.gz")
    db = vector_db(cfg=cfg, target="text")
    # db.loadをすると上書きをするようになる
    #db.load(base_data_path)
    for path in tqdm(file_lists):
        if not "channel_list" in path:
            with open(path) as f:
                data = json.load(f)
            for block in data: # json内の発言を一つずつ取得
                if  "user" in block: # userがチャットボットの時の発言は飛ばす
                    if block["user"] == "U0550LX2NG0":
                        pass
                    else:
                        db.add_document(block)
                        time.sleep(0.1)
    db.save(base_data_path)

if __name__ == "__main__":
    from pprint import pprint
    target = os.listdir(os.path.join(os.getcwd(), "sample_folder"))
    file_list = [glob.glob(os.path.join(os.getcwd(), "sample_folder", i)+"/*.json") for i in target]
    file_list = sum(file_list, [])
    now = datetime.now().strftime(r"%Y-%m-%d")
    target_dir = os.path.join(os.getcwd(),  "logs", now)
    db_from_file_list(file_list)


