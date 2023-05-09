from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import re
import configparser
from util import vector_db
from langchain.chat_models import ChatOpenAI
from langchain import LLMChain, PromptTemplate


class my_cfg:
    openai_key = None
    openai_org_id = None
    SLACK_APP_TOKEN = None
    SLACK_BOT_TOKEN = None

def setup_cfg(cfg=my_cfg):
    tmp = configparser.ConfigParser()
    tmp.read("data/config.ini")
    cfg.openai_key = tmp["OPEN_AI"]["key"]
    cfg.openai_org_id = tmp["OPEN_AI"]["organization_ID"]
    cfg.SLACK_APP_TOKEN = tmp["chatbot"]["SLACK_APP_TOKEN"]
    cfg.SLACK_BOT_TOKEN = tmp["chatbot"]["SLACK_BOT_TOKEN"]
    return cfg

cfg = setup_cfg()
app = App(token=cfg.SLACK_BOT_TOKEN)

template = """
命令文:
以下の情報は学生の質問に関連する情報をベクトルDBから抽出したものです。この情報を元に、秘書として、わかりやすく的を得た返答をしてください。
また、あなたは質問の答えを知らない場合、正直に「知らない」と答えます。

情報:
{context}

質問:
{question}

私の答え:
"""

cfg.template = template

llm = ChatOpenAI(temperature=0, openai_api_key=cfg.openai_key, openai_organization=cfg.openai_org_id, model_name="gpt-3.5-turbo")
prompt = PromptTemplate(template=cfg.template, input_variables=["context", "question"], )
qa_model = LLMChain(prompt=prompt, llm=llm, verbose=True)
db = vector_db(cfg=cfg) 
db.load("data/sample.pkl.gz")

@app.message("hello")  # 送信されたメッセージ内に"hello"が含まれていたときのハンドラ
def ask_who(say):
    say("can I help you?")


@app.event("app_mention")  # chatbotにメンションが付けられたときのハンドラ
def respond_to_mention(event, say):
    message = re.sub(r'^<.*>', '', event['text'])
    data_from_db = db.query(message, k=8)
    tmp = list(map(lambda x: list(x.values()), data_from_db))
    tmp = sum(tmp, [])
    tmp = "/n".join(tmp)
    res = qa_model.predict(question=message, context="".join(tmp))
    with open("log/past_log.txt", "a", encoding="utf-8") as f:
        f.write("\n\n" + message+": \n"+tmp+"\n"+ "bot:" + res)
    say(res)
    print(res)
    # say(message[::-1]) # 文字列を逆順

@app.event("message") # ロギング
def handle_message_events(body, logger):
    logger.info(body)


if __name__ == "__main__":
    SocketModeHandler(app, cfg.SLACK_APP_TOKEN).start()
