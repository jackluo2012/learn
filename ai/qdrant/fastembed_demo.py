import os

# 模型已预下载到 ./local_cache（Qdrant/bge-small-zh-v1.5 + BAAI/bge-reranker-base），
# 开离线模式直接读本地缓存：启动快，且不受代理/网络波动影响。
# （如需重新下载新模型，删掉这一行，直连 huggingface.co 即可；
#   hf-mirror 镜像在 huggingface_hub 1.x 下会丢元数据头导致失败，不要用。）
os.environ["HF_HUB_OFFLINE"] = "1"

from fastembed import TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder

# step1：Embedding粗召回模型
# 注：fastembed 不支持 BAAI/bge-m3（dense+sparse+colbert 多向量模型），
# 中文场景用 bge-small-zh-v1.5 替代
embedding_model = TextEmbedding(model_name="BAAI/bge-small-zh-v1.5")

# step2：Reranker精排模型（独立模型！）
# 注：fastembed 不支持 bge-reranker-v2-m3，bge-reranker-base 为多语言版，支持中文
reranker = TextCrossEncoder(
    model_name="BAAI/bge-reranker-base",
    cache_dir="local_cache",  # 注意：Reranker 默认缓存目录是系统临时目录，不是 ./local_cache，需显式指定
)

# 知识库文档
docs = [
    "FastEmbed是qdrant出的向量推理库，基于onnx runtime",
    "MySQL是关系型数据库",
    "BGE-M3是智源的多语言embedding模型，支持混合检索",
    "Java虚拟机JVM跨平台原理"
]

# 文档向量化
doc_embeds = list(embedding_model.embed(docs))

query = "FastEmbed和BGE-M3是什么关系？"
query_embed = list(embedding_model.embed([query]))[0]

# =========这里省略向量库相似度搜索，模拟召回全部4条作为候选========
candidate_texts = docs

# RERANKER精排：传入问题+候选列表，得到分数
rerank_scores = list(reranker.rerank(query, candidate_texts))

# 按分数从高到低排序
results = sorted(zip(candidate_texts, rerank_scores), key=lambda x:x[1], reverse=True)

for text, score in results:
    print(f"score:{score:.3f} | {text}")
