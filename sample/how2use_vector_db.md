
# vector_db の使い方

---

・基本的にベクトル化する際はOpenAIの有料APIによってベクトル化される



## 基本


~~~python
from vector_db import vector_db

file_path = < db file path >

# ファイルをデータベースに追加

db = db.add_document( text: str )

# load 
db = vector_db()
db.load(file_path)

# 類似の文を検索して返す
responce = db.query("来週までにやることってなんだっけ？", k=5)
~~~
