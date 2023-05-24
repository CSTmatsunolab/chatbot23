import os 
from llama_index import download_loader
import string
import random
from langchain.chains.summarize import load_summarize_chain
from langchain import PromptTemplate
import requests

summarize_prompt_template = """
以下の文章を要約してください。文章が短くならないようにお願いします。
また、日本語で回答してください:

{text}

要約:"""
CJKPDFReader = download_loader("CJKPDFReader")
loader = CJKPDFReader(concat_pages=False)

def doc_from_url(url, cfg): # urlからLangChain形式のドキュメントを返す
    tmp_path = ''.join(random.choices(string.ascii_letters + string.digits, k=8)) + ".pdf"
    
    if not os.path.exists("pdf_tmp"):
    # ディレクトリが存在しない場合、ディレクトリを作成する
        os.makedirs("pdf_tmp")
    tmp_path = os.path.join("pdf_tmp", tmp_path)
    
    # PDFを一時的に保存する
    res = requests.get(url, headers={"Authorization": f"Bearer {cfg.SLACK_BOT_TOKEN}"})
    with open(tmp_path, 'wb') as f: 
        f.write(res.content)

    documents = loader.load_data(file=tmp_path) # ドキュメントを読み込む
    langchain_documents = [d.to_langchain_format() for d in documents] # LangChain形式にする
    os.remove(tmp_path) # 保存したPDFを削除する
    return langchain_documents


def summrize(docs, llm): # ドキュメントから要約する
    summarize_template = PromptTemplate(
            template=summarize_prompt_template, input_variables=["text"])

    chain = load_summarize_chain(
        llm,
        chain_type="map_reduce",
        map_prompt=summarize_template,
        combine_prompt=summarize_template
    )

    summary = chain.run(docs)
    return summary

def summrize_from_url(pdf_url, llm, cfg): # PDFのURLから要約するように一つの関数にした
    doc = doc_from_url(pdf_url, cfg=cfg)
    res = summrize(doc, llm)
    return res # 要約されたもの