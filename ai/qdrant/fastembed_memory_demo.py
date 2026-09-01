import os
from pathlib import Path

# FastEmbed model cache
CACHE_DIR = Path(__file__).resolve().parent / "local_cache"
os.environ["FASTEMBED_CACHE_PATH"] = str(CACHE_DIR)
# 模型已预下载到 ./local_cache（Qdrant/bge-small-zh-v1.5 + BAAI/bge-reranker-base），
# 开离线模式直接读本地缓存：启动快，且不受代理/网络波动影响。
# （如需重新下载新模型，删掉这一行，直连 huggingface.co 即可；
#   hf-mirror 镜像在 huggingface_hub 1.x 下会丢元数据头导致失败，不要用。）
os.environ["HF_HUB_OFFLINE"] = "1"

from qdrant_client import QdrantClient, models

client = QdrantClient(":memory:")  # Qdrant is running from RAM.

from fastembed import TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder

# 添加数据
docs = [
    "Qdrant has a LangChain integration for chatbots.",
    "Qdrant has a LlamaIndex integration for agents.",
]
metadata = [
    {"source": "langchain-docs"},
    {"source": "llamaindex-docs"},
]
ids = [42, 2]


# step1：Embedding粗召回模型
# 注：fastembed 不支持 BAAI/bge-m3（dense+sparse+colbert 多向量模型），
# 中文场景用 bge-small-zh-v1.5 替代
model_name="BAAI/bge-small-zh-v1.5"
embedding_model = TextEmbedding(model_name,)
# 创建收藏集
client.create_collection(
    collection_name="test_collection",
    vectors_config=models.VectorParams(
        size=client.get_embedding_size(model_name), 
        distance=models.Distance.COSINE
    ),  # size and distance are model dependent
)
# 将文档插入到集合中
metadata_with_docs = [
    {"document": doc, "source": meta["source"]} for doc, meta in zip(docs, metadata)
]
client.upload_collection(
    collection_name="test_collection",
    vectors=[models.Document(text=doc, model=model_name) for doc in docs],
    payload=metadata_with_docs,
    ids=ids,
)

#运行向量搜索
search_result = client.query_points(
    collection_name="test_collection",
    query=models.Document(
        text="Which integration is best for agents?", 
        model=model_name
    )
).points
print(search_result)