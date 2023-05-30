from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
import re
import configparser
from util import vector_db, summrize_from_url
from langchain.chat_models import ChatOpenAI
from langchain import LLMChain, PromptTemplate
import math
from datetime import datetime
import json
from pprint import pprint

class my_cfg:
    openai_key = None
    openai_org_id = None
    SLACK_APP_TOKEN = None
    SLACK_BOT_TOKEN = None
    SLACK_API_TOKEN = None
    SLACK_SIGNING = None

def setup_cfg(cfg=my_cfg):
    tmp = configparser.ConfigParser()
    tmp.read("data/config.ini")
    cfg.openai_key = tmp["OPEN_AI"]["key"]
    cfg.openai_org_id = tmp["OPEN_AI"]["organization_ID"]
    cfg.SLACK_APP_TOKEN = tmp["chatbot"]["SLACK_APP_TOKEN"]
    cfg.SLACK_BOT_TOKEN = tmp["chatbot"]["SLACK_BOT_TOKEN"]
    cfg.SLACK_API_TOKEN = tmp["chatbot"]["SLACK_API_TOKEN"]
    cfg.SLACK_SIGNING = tmp["chatbot"]["SLACK_SIGNING"]
    return cfg

cfg = setup_cfg()
app = App(token=cfg.SLACK_BOT_TOKEN,signing_secret=cfg.SLACK_SIGNING)
client = WebClient(token=cfg.SLACK_BOT_TOKEN)

template = """
#命令文
あなたは、Slackのチャット履歴を参考して質問に回答します。質問内容に口調の指示がある場合、絶対に指示通りの口調で回答してください。
質問を投稿した時間と、Slackのチャット履歴の投稿時間を考慮して、新しい情報を中心に回答してください。


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

回答:
"""

cfg.template = template

llm = ChatOpenAI(temperature=0, openai_api_key=cfg.openai_key, openai_organization=cfg.openai_org_id, model_name="gpt-3.5-turbo")
prompt = PromptTemplate(template=cfg.template, input_variables=["context", "question"], )
qa_model = LLMChain(prompt=prompt, llm=llm, verbose=True)
db = vector_db(cfg=cfg) 
db.load("sample/全体ゼミ.pkl.gz")

@app.message("hello")  # 送信されたメッセージ内に"hello"が含まれていたときのハンドラ
def ask_who(say):
    say("can I help you?")

@app.event({"type": "message", "subtype": "file_share"}) # ファイルが送られてきた場合
def pdf_summery(event, say):
    # 拡張子がpdfの場合処理をする
    if event["files"][0]["filetype"] == "pdf": 
        say("処理に時間かかるよ～")

        # pdfのダウンロードのURLを取得
        url = event["files"][0]['url_private_download'] 

        # urlから要約までする
        res = summrize_from_url(pdf_url=url, llm=llm, cfg=cfg) 
        say(res, thread_ts=event["event_ts"]) # チャンネルに発言
    else:# pdfじゃないのが来た場合
        say("pdfじゃないよ～")
        
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
    neri = []
    user="不明"
    # ユーザーからのテキストを正規表現できれいにして取り出し
    message = re.sub(r'^<.*>', '', event['text']) 
    message = str(datetime.fromtimestamp(math.floor(float(event['ts']))))+':'+message
    # データベースから類似したテキストの問い合わせ（ｋ個）
    data_from_db = db.query(message, k=5)

    for m in range(5):
        # [投稿時間,発言者: 本文],
        input_id = data_from_db[m]['user']
        # input_idのreal_nameをlist_user.jsonから取得
        with open('slack_data/list_user.json') as f:
            j = json.load(f)
        for i in range(len(j['members'])):
            if j['members'][i]['id']==input_id:
                # real_nameがある場合、real_nameをuserに代入
                if 'real_name' in j['members'][i]:
                    user = j['members'][i]['real_name']
                    break
                # real_nameがない場合、たぶんdeleteされてるからreal_nameをほりかえす
                else:
                    user = j['members'][i]['profile']['real_name']
                    break
            else:
                # list_users.jsonにない場合はリストを再取得する # あとで
                pass
        # UNIX時間変換（小数点以下切り捨て）
        ts = datetime.fromtimestamp(math.floor(float(data_from_db[m]['ts'])))

        test = f"[{ts},{user}: {data_from_db[m]['text']}],"
        neri.append(test)
    neri = "".join(neri)

    # GPT君に質問
    res = qa_model.predict(question=message, context="".join(neri))

    # GPT君への質問をテキストファイルに送る
    today = '{:%Y-%m-%d}.txt'.format(datetime.now())
    with open("log/"+today, "a", encoding="utf-8") as f: 
        f.write("---------\n>" + message+": \n"+neri+"\n"+ "bot:" + res)
    # Slackに発言する
    say(res) 
    print(res)
    print(ts)
    # say(message[::-1]) # 文字列を逆順 これは練習でやったやつ

@app.event("message") # ロギング
def handle_message_events(body, logger):
    logger.info(body)

if __name__ == "__main__":
    channel_id = "C05487CDMJ9"  # チャンネルIDを指定(chatbot23_test)
    msg_running = "⚡️ Bolt is running!"
    msg_closed = "おやすみ〜"
    client.chat_postMessage(channel=channel_id, text=msg_running)
    try:   
        SocketModeHandler(app, cfg.SLACK_APP_TOKEN).start()
    finally:
        client.chat_postMessage(channel=channel_id, text=msg_closed)

