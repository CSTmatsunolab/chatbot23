import os
import json
import configparser
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

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

def get_channels_from_cfg(cfg):
    slack_token = cfg.SLACK_API_TOKEN
    # ログとチャンネルリストを保存するディレクトリのパスを指定します
    log_directory = "logs/"
    channel_list_file = "channel_list.json"

    # 取得するログの期間を設定します
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=1)

    # Slackクライアントを初期化します
    client = WebClient(token=slack_token)

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

    # ログを保存するディレクトリが存在しない場合は作成します
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    try:
        channels_response = client.conversations_list(types="public_channel")
    except SlackApiError as e:
        print(f"Error fetching channels: {e}")

    # パブリックチャンネルのリストを取得します
    channel_list = channels_response['channels']

    # チャンネルリストを保存します
    with open(os.path.join(log_directory, channel_list_file), 'w', encoding='utf-8') as channel_list_file:
        json.dump(channel_list, channel_list_file, indent=2, ensure_ascii=False)

    # 各チャンネルのログを取得します
    for channel in channel_list:
        channel_name = channel['name']
        channel_id = channel['id']

        # チャンネルごとにログを取得し、JSON形式で保存します
        channel_logs = get_channel_history(channel_id, start_date, end_date)

        # チャンネルのログが空でないか確認
        if channel_logs:
            # ファイル名に日付を追加します
            log_file_name = f"{channel_name}_{start_date.strftime('%Y-%m-%d')}.json"
            log_file_path = os.path.join(log_directory, log_file_name)
            with open(log_file_path, 'w', encoding='utf-8') as log_file:
                json.dump(channel_logs, log_file, indent=2, ensure_ascii=False)
            print(f"Downloading logs for channel: {log_directory}/{channel_name}.json")
        # チャンネルのログがからの場合保存しない
        else:
            print(f"本日更新なし channel: {channel_name}")
    print("Logs downloaded successfully!")