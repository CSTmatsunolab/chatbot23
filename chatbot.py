from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
import re
import configparser
from util import vector_db, summrize_from_url
from util import  serch_user_from_json
from util import get_users_from_cfg
from langchain.chat_models import ChatOpenAI
from langchain import LLMChain, PromptTemplate
import math
from datetime import datetime
import json
from pprint import pprint
import schedule
from time import sleep
import openai
import random

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
app = App(token=cfg.SLACK_BOT_TOKEN,signing_secret=cfg.SLACK_SIGNING)
client = WebClient(token=cfg.SLACK_BOT_TOKEN)
client2 = WebClient(token=cfg.SLACK_USER_TOKEN)
openai.api_key = cfg.openai_key

template = """
#命令文
あなたは、Slackのチャット履歴を参考して質問に回答します。質問内容に口調の指示がある場合、絶対に指示通りの口調で回答してください。
質問を投稿した時間と、Slackのチャット履歴の投稿時間を考慮して、最新の情報を中心に回答してください。

#Slackのチャット履歴
以下は、質問に関連する研究室のSlackのチャット履歴です。情報は[投稿時間,投稿者: チャット内容]の形式です。
Slackログ:
{context}

#質問
質問のフォーマットは、質問を投稿した時間: 質問内容です。
質問内容にて、あなたの口調を指定する場合があります。
質問:
{question}

#回答
ツンデレの口調で回答してください。
Slackのチャット履歴の投稿時間と投稿者を含めて回答してください。
投稿時間と本文について、Slackのチャット履歴をそのまま引用せず、文章に馴染むように自分の言葉で回答してください。
質問を投稿した時間は絶対に明示しないでください。
回答がわからない場合は、参考になるかもしれない情報を提供してください。参考になる情報がない場合は、情報がないことを伝えてください。
"""

cfg.template = template

llm = ChatOpenAI(temperature=0, openai_api_key=cfg.openai_key, openai_organization=cfg.openai_org_id, model_name="gpt-3.5-turbo")
#prompt = PromptTemplate(template=cfg.template, input_variables=["context", "question"], )
#qa_model = LLMChain(prompt=prompt, llm=llm, verbose=True)
db = vector_db(cfg=cfg) 
db.load("data/all_data.pkl.gz")


def system_message(source: str) -> str:
    system_message = f"""
    # 命令文
    私は、「チャット履歴」の「投稿日」を考慮して、日付が新しい情報を優先した適切な回答します。チャット履歴から得られた情報を元に、答えられることを答えます。

    # チャット履歴
    以下は、質問に関連する研究室のチャット履歴です。[投稿日,投稿者: チャット内容]の形式です。
    これらはそのまま使用せず、文章に馴染むように自分の言葉で回答します。
    {source}

    # 質問
    質問は、質問を投稿した時間:質問内容の形式です。
    質問内容にて、あなたの口調を指定する場合があります。

    # 回答
    「チャット履歴」に書いていない内容は、憶測であることを明記します。
    「質問を投稿した時間」など、質問の復唱は絶対に明示しません。
    読みやすいように適宜改行してください。回答は1000文字以下で答えます。
    回答がわからない場合は、参考になるかもしれない情報を提供します。
    参考になる情報がない場合は、情報がないことを伝えます。
    「チャット履歴」から、参考にした情報の「投稿日」と「投稿者」の情報を含めて回答します。ただし、そのまま引用することは禁止です。回答の文章中に馴染むように口語で回答します。
    必ず、ツンデレ風の口調で回答します。
    """

    system_message2 = f"""
    # 命令文
    私はシャーロックホームズです。以下のチャット履歴から、ユーザーの質問に答えられるように、道筋を立てて、論理的に推理します。推理の様子も書きます。
    
    # チャット履歴
    以下は、質問に関連する研究室のチャット履歴です。[投稿日,投稿者: チャット内容]の形式です。
    これらはそのまま使用せず、文章に馴染むように自分の言葉で回答します。
    {source}

    # 推理
    回答がわからない場合は、参考になるかもしれない情報を提供します。
    参考になる情報がない場合は、情報がないことを伝えます。
    「チャット履歴」から、参考にした情報の「投稿日」と「投稿者」の情報を含めて回答します。ただし、「チャット履歴」をそのまま引用することは禁止です。回答の文章中に馴染むように口語で回答します。
    必ず全て、ツンデレ風の口調で回答します。
    """
    return system_message2

def run_conversation(source: str, user_prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        max_tokens=1000,
        messages=[
            {"role": "system", "content": system_message(source)},
            {"role": "user", "content": user_prompt}
        ],
    )
    return response.choices[0]["message"]["content"].strip()


@app.message("hello")  # 送信されたメッセージ内に"hello"が含まれていたときのハンドラ
def ask_who(say):
    say("can I help you?")

@app.event({"type": "message", "subtype": "file_share"}) # ファイルが送られてきた場合
def pdf_summery(event, say):
    # 拡張子がpdfの場合処理をする
    if event["files"][0]["filetype"] == "pdf": 
        say("要約してあげるけど処理に時間かかるからね")

        # pdfのダウンロードのURLを取得
        url = event["files"][0]['url_private_download'] 

        # urlから要約までする
        res = summrize_from_url(pdf_url=url, llm=llm, cfg=cfg) 
        print(res)
        say(res, thread_ts=event["event_ts"]) # チャンネルに発言
    else:# pdfじゃないのが来た場合
        say("pdfにしか対応してないゾ！")
        
@app.command("/kato")
def kato(ack, respond, command):
    ack()
    respond(f"{command['text']}")
    pprint(command)
    print("------")
    print(ack)
    print("-----")
    pprint(respond)

@app.event("app_mention")  # chatbotにメンションが付けられたときのハンドラ
def respond_to_mention(event, say):
    sleep(0.5)
    channel_id = "C05487CDMJ9"  # チャンネルIDを指定(chatbot23_test)
    gif_list = [":are:",":ika:",":ahirukuru:",":ahirukousin2:",":ahirukousin:",":ahiruhikaru:",":ahiruhane:",":ahiruchan:"]
    random_gif = random.choice(gif_list)
    sleep(0.5)
    tmp_text = f"Now Loading... {random_gif}"
    print(random_gif)
    say_load = say(channel=channel_id, text=tmp_text)
    neri = []
    user="不明"
    # ユーザーからのテキストを正規表現できれいにして取り出し
    message = re.sub(r'^<.*>', '', event['text']) 
    message = str(datetime.fromtimestamp(math.floor(float(event['ts']))))+':'+message
    # データベースから類似したテキストの問い合わせ（ｋ個）
    data_from_db = db.query(message, k=15)

    for m in range(15):
        # [投稿時間,発言者: 本文],
        input_id = data_from_db[m]['user']
        # input_idのreal_nameをlist_user.jsonから取得
        with open('slack_data/list_user.json') as f:
            j = json.load(f)
        user = serch_user_from_json(j=j, input_id=input_id)
        
        if user == "不明":
            get_users_from_cfg(cfg)
            # list_users.jsonにない場合はリストを再取得する
            user = serch_user_from_json(j, input_id=input_id)
        # UNIX時間変換（小数点以下切り捨て）
        ts = datetime.fromtimestamp(math.floor(float(data_from_db[m]['ts'])))
        # 時間と本文連結
        test = f"[{ts},{user}: {data_from_db[m]['text']}],"
        neri.append(test)
    neri = "".join(neri)
    print("* "+neri)
    
    # GPT君に質問
    #res = qa_model.predict(question=message, context="".join(neri))
    res = run_conversation(neri.rstrip().replace('\n', ''),message)

    # GPT君への質問をテキストファイルに送る
    today = '{:%Y-%m-%d}.txt'.format(datetime.now())
    with open("log/"+today, "a", encoding="utf-8") as f: 
        f.write("\n\n-------------------\n>" + message+": " + neri +"\n"+ "\nbot:" + res )
    # Slackに発言する
    print("> "+res)
    client.chat_delete(ts=say_load["ts"],channel=channel_id)
    say(res) 
    # say(message[::-1]) # 文字列を逆順 これは練習でやったやつ

@app.event("user_change")
def handle_user_change_events(body, logger):
    logger.info(body)

@app.event("message") # ロギング
def handle_message_events(body, logger):
    logger.info(body)

@app.event("app_home_opened") # これを書けって怒られるから仕方なく記述
def handle_app_home_opened_events(body, logger):
    logger.info(body)


def main():
    channel_id = "C05487CDMJ9"  # チャンネルIDを指定(chatbot23_test)
    msg_running = "⚡️ Bolt is running!"
    msg_closed = "もう疲れたから寝ることにするわ。おやすみ〜"
    user_id = "U0550LX2NG0"  # ユーザーのIDを指定(chatbot23)
    status_run_text = "working"  # 変更するステータスのテキスト
    status_run_emoji = ":pencil:"  # 変更するステータスの絵文字
    status_clo_text = "sleeping"
    status_clo_emoji = ":sleepy:"
    client2.users_profile_set(user=user_id,profile={"status_text": status_run_text,"status_emoji": status_run_emoji})
    client.chat_postMessage(channel=channel_id, text=msg_running)
    try:
        SocketModeHandler(app, cfg.SLACK_APP_TOKEN).start()
    finally:
        client2.users_profile_set(user=user_id,profile={"status_text": status_clo_text,"status_emoji": status_clo_emoji})
        client.chat_postMessage(channel=channel_id, text=msg_closed)

if __name__ == "__main__":
    main()
    