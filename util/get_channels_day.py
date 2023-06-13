import os
import json
import configparser
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import schedule
import time

class my_cfg:
    openai_key = None
    openai_org_id = None
    SLACK_APP_TOKEN = None
    SLACK_USER_TOKEN = None
    SLACK_BOT_TOKEN = None
    SLACK_API_TOKEN = None
    SLACK_SIGNING = None

def setup_cfg(cfg=my_cfg):
    tmp = configparser.ConfigParser()
    tmp.read("data/config.ini")
    cfg.openai_key = tmp["OPEN_AI"]["key"]
    cfg.openai_org_id = tmp["OPEN_AI"]["organization_ID"]
    cfg.SLACK_BOT_TOKEN = tmp["chatbot"]["SLACK_BOT_TOKEN"]
    cfg.SLACK_USER_TOKEN = tmp["chatbot"]["SLACK_USER_TOKEN"]
    cfg.SLACK_APP_TOKEN = tmp["chatbot"]["SLACK_APP_TOKEN"]
    cfg.SLACK_API_TOKEN = tmp["chatbot"]["SLACK_API_TOKEN"]
    cfg.SLACK_SIGNING = tmp["chatbot"]["SLACK_SIGNING"]
    return cfg
cfg = setup_cfg()

def get_channels_from_cfg():
    slack_token = cfg.SLACK_API_TOKEN
    # ログとチャンネルリストを保存するディレクトリのパスを指定
    log_directory = "logs/"
    channel_list_file = "channel_list.json"
    # 取得するログの期間を設定
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=1)
    start_date_dir = datetime.now().strftime(r"%Y-%m-%d")

    # Slackクライアントを初期化
    client = WebClient(token=slack_token)
    # ログを保存するディレクトリlogsが存在しない場合は作成
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # ログを取得するためのメソッド
    def get_channel_history(channel_id, oldest, latest):
        try:
            response = client.conversations_history(
                channel=channel_id,
                oldest=oldest.timestamp(),
                latest=latest.timestamp(),
                limit=1000  # 取得するログの最大数
            )
            return response['messages']
        except SlackApiError as e:
            print(f"Error fetching history: {e}")

    # チャンネルリストを取得
    try:
        channels_response = client.conversations_list(types="public_channel")
    except SlackApiError as e:
        print(f"Error fetching channels: {e}")
    ## パブリックチャンネルのリストを取得
    channel_list = channels_response['channels']
    ## チャンネルリストをjsonで保存
    with open(os.path.join(log_directory, channel_list_file), 'w', encoding='utf-8') as channel_list_file:
        json.dump(channel_list, channel_list_file, indent=2, ensure_ascii=False)

    # 各チャンネルのログを取得
    ## 取得日（年月日）のディレクトリを作る
    if not os.path.exists(log_directory+'/'+start_date_dir):
        os.makedirs(log_directory+'/'+start_date_dir)

    for channel in channel_list:
        channel_name = channel['name']
        channel_id = channel['id']
        ## チャンネルごとにログを取得し、JSON形式で保存
        channel_logs = get_channel_history(channel_id, start_date, end_date)
        ## チャンネルのログが空でないか確認
        if channel_logs:
            ### ファイル名に日付を追加
            log_file_name = f"{channel_name}_{start_date.strftime('%Y-%m-%d')}.json"
            log_file_path = os.path.join(log_directory, start_date_dir, log_file_name)
            with open(log_file_path, 'w', encoding='utf-8') as log_file:
                json.dump(channel_logs, log_file, indent=2, ensure_ascii=False)
            print(f"Downloading logs for channel: {log_directory}{start_date_dir}/{channel_name}.json")
        ### チャンネルのログが空の場合保存しない
        else:
            print(f"更新なし channel: {channel_name}")
    print("Logs downloaded successfully!")
if __name__ == "__main__":
    schedule.every().day.at("16:50").do(get_channels_from_cfg)
    while True:
        schedule.run_pending()
        time.sleep(1)  # 待ち
