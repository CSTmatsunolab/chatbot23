import gzip
import pickle
import numpy as np
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from .math_algo import cosine_similarity, adams_similarity, derridaean_similarity, euclidean_metric, hyper_SVM_ranking_algorithm_sort


def get_embedding(docs, cfg=None, target: str=None, embedding_type="openai", model="text-embedding-ada-002"):
    """ 
    docs format: 
      list[dic[key:text]] (json format)
      list[text]
      text
    return np.array(np.array)

    target format:
      example -> sample.target
      target is text you want to embbeding

    if you want to use openai embedding, it need to define cfg
    """
    # データベース内のベクトルの次元数はそろえること

    if embedding_type == "openai":
        # dim size is 1536  and  paid
        
        if not cfg :
            raise Exception("cfgが定義されてないよん。ニヤリ。openai_keyとopenai_org_idを設定してねん")
        # cfg format
        #  cfg:
        #    openai_key = < your openAI api key >
        #    openai_org_id = < your openAI organization ID >
        
        emb = OpenAIEmbeddings(openai_api_key=cfg.openai_key, openai_organization=cfg.openai_org_id, model=model)

    elif embedding_type == "hf":
        # dim size is 768 and maybe free
        emb = HuggingFaceEmbeddings()

    if isinstance(docs, list):
        if isinstance(docs[0], dict):
            if not target:
                raise Exception("targetが定義されてないよん。ニヤリ")
            if "." in target:
                keys = target.split(".")
            else:
                keys = [target]

            texts = []
            for doc in docs:
                for key in keys:
                    doc = doc[key]
                texts.append(doc.replace("\n", " "))
        
        elif isinstance(docs[0], str):
            texts = docs

        res = emb.embed_documents(texts)
        return [np.array(tmp) for tmp in res ]
        
    elif isinstance(docs, str):
        res = emb.embed_query(docs)
        return np.array(res)
                
class vector_db:
    def __init__(self, documents=None, cfg=None, target=None, emb_func=None, sim_metric="cosine"):
        if emb_func == None:
            emb_func = lambda x: get_embedding(x, target=target, cfg=cfg)
        self.cfg = cfg
        self.target = target
        self.emb = emb_func
        self.documents = []
        
        self.vectors = None
        if documents:
            self.add_documents(documents)

        if sim_metric == "cosine":
            self.metric = cosine_similarity
        elif sim_metric == "adams":
            self.metric = adams_similarity
        elif sim_metric == "derrida":
            self.metric = derridaean_similarity
        elif sim_metric == "eulidean":
            self.metric = euclidean_metric
        else:
            raise Exception("sim_metricにはcosine, adams, derrida, eulideanから選んでね")

    def add_document(self, document, vector=None):
        if vector is None:
            vector = self.emb([document])[0]     
        # to do 
        if self.vectors is None:
            self.vectors = np.empty((0, len(vector)), dtype=np.float32)
        
        elif len(vector) != self.vectors.shape[1]:
            raise ValueError("All vectors must have the same length.")
        self.vectors = np.vstack([self.vectors, vector]).astype(np.float32)
        self.documents.append(document)

    def add_documents(self, docs, vectors=None):
        if vectors == None:
            vectors = np.array(self.emb(docs)).astype(np.float32)
        for vec, doc in zip(vectors, docs):
            self.add_document(doc, vector=vec)

    def load(self, file_path):
        if file_path.endswith(".gz"):
            with gzip.open(file_path, "rb") as f:
                data = pickle.load(f)
        else:
            with open(file_path, "rb") as f:
                data = pickle.load(f)
        self.vectors = data["vec"].astype(np.float32)
        self.documents = data["docs"]

    def save(self, file_path):
        data = {
            "vec": self.vectors,
            "docs": self.documents
        }
        if file_path.endswith(".gz"):
            with gzip.open(file_path, "wb") as f:
                pickle.dump(data, f)
        else:
            with open(file_path, "wb") as f:
                pickle.dump(data, f)


    def query(self, text: str, k=5):
        """
        search k個の similarity vec 
        """
        embed_text = self.emb(text)
        res = hyper_SVM_ranking_algorithm_sort(self.vectors, embed_text, top_k=k, metric=self.metric)
        return [self.documents[index] for index in res]

