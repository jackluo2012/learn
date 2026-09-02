"""
================================================================================
 混合检索 + 重排序（Hybrid Search & Reranking）完整演示
================================================================================

本脚本在 100 本科幻小说上，用同一个查询词 "time travel" 依次演示 5 种检索方式，
并对比它们的结果差异：

  实验一：纯稠密向量检索（Dense / 语义检索）
  实验二：纯稀疏向量检索（Sparse / BM25 关键词检索）
  实验三：混合检索 + RRF 融合（Hybrid Search）
  实验四：ColBERT 多向量重排（服务端 rerank，token 级 late interaction）
  实验五：Cross-Encoder 本地重排（客户端 rerank，bge-reranker-base）

核心思想 —— 「两阶段检索」架构：
  第一阶段【召回 Recall】：用 cheap/fast 的方式从全库捞回 top-N 候选
  第二阶段【精排 Rerank】：用 expensive/accurate 的模型只对这 N 条候选精细打分

本脚本 embedding 全部在 Qdrant Cloud 服务端完成（cloud_inference=True），
本地只保留查询/文档文本 + 模型名，不需要下载任何 embedding 模型权重；
唯一的例外是实验五的 cross-encoder 重排器，它在客户端本地跑
（BAAI/bge-reranker-base 的 onnx 已预下载到 local_cache）。

数据：top_100_scifi_books_full.csv（已下载到脚本同目录）
================================================================================
"""

import os
import csv
from pathlib import Path

# ------------------------------------------------------------------------------
# 0. 环境准备
# ------------------------------------------------------------------------------
from dotenv import load_dotenv

# 加载当前脚本目录下的 .env（QDRANT_URL / QDRANT_API_KEY / RERANKER_MODEL 等）
load_dotenv(Path(__file__).resolve().parent / ".env")


def required_env(name: str) -> str:
    """读取必须存在的环境变量，缺失时给出明确报错。"""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"缺少环境变量: {name}")
    return value


# 必须在导入 fastembed / huggingface_hub 之前生效：
# 实验五要用的 bge-reranker-base 已预下载到 local_cache，
# 离线开关让 fastembed 直接读缓存、不发起任何网络请求（网络不稳时也不会卡死）。
os.environ["HF_HUB_OFFLINE"] = os.getenv("HF_HUB_OFFLINE", "1")

# fastembed 的 reranker 从这里读模型缓存（HF hub cache 格式）
MODEL_CACHE_DIR = str(Path(__file__).resolve().parent / os.getenv("MODEL_CACHE_DIR", "local_cache"))

from fastembed.rerank.cross_encoder import TextCrossEncoder   # 本地 cross-encoder 重排器（实验五）
from qdrant_client import QdrantClient, models                # Qdrant 客户端与模型定义
from qdrant_client.models import PointStruct, Document        # 单个数据点 / 待服务端推理的文本

# ------------------------------------------------------------------------------
# 1. 连接 Qdrant Cloud
# ------------------------------------------------------------------------------
client = QdrantClient(
    url=required_env("QDRANT_URL"),
    api_key=required_env("QDRANT_API_KEY"),
    # cloud_inference=True：开启「服务端推理」。之后所有 Document(text=..., model=...)
    # 都只把【文本 + 模型名】发到云端，由 Qdrant Cloud 在服务端完成 embedding。
    # 好处：本地零模型、零 GPU；代价：上传/查询多一次云端推理往返。
    cloud_inference=True,
    timeout=60,  # 云端推理 + 网络往返可能较慢，给足超时
)

collection_name = "hybrid-search"

# 每次运行都重建集合，保证结果可复现（正式场景请按需改为增量写入）
if client.collection_exists(collection_name=collection_name):
    client.delete_collection(collection_name=collection_name)

# ------------------------------------------------------------------------------
# 2. 三种向量：建集合
# ------------------------------------------------------------------------------
# 同一份数据，同一篇文档 description，用 3 个模型各嵌一次，挂在同一个点的 3 个具名向量上：
dense_embedding_model = "sentence-transformers/all-MiniLM-L6-v2"        # 稠密：384 维语义向量
sparse_embedding_model = "qdrant/bm25"                                  # 稀疏：BM25 词项权重向量
late_interaction_embedding_model = "answerdotai/answerai-colbert-small-v1"  # 多向量：ColBERT token 级向量

client.create_collection(
    collection_name,
    vectors_config={
        # 【dense】传统单向量：一篇文档压成 1 个 384 维向量，余弦相似度，走 HNSW 近似最近邻
        "dense": models.VectorParams(
            size=384,
            distance=models.Distance.COSINE,
        ),
        # 【multi】多向量（ColBERT late interaction）：
        #   一篇文档 = N 个 96 维向量（每个 token 一个），
        #   查询时对「每个 query token × 所有 doc token」取最大相似度再求和（MaxSim）。
        #   hnsw_config=HnswConfigDiff(m=0)：故意禁用 HNSW 索引 ——
        #   多向量体积大（每文档几十~上百个向量），建 ANN 索引既慢又费内存；
        #   而 m=0 后它【无法】做全库 ANN 召回，只能对 prefetch 送来的候选逐条精确打分，
        #   这恰好把它定位成一个纯粹的【重排序器（reranker）】，而不是召回器。
        "multi": models.VectorParams(
            size=96,
            distance=models.Distance.COSINE,
            multivector_config=models.MultiVectorConfig(
                comparator=models.MultiVectorComparator.MAX_SIM,
            ),
            hnsw_config=models.HnswConfigDiff(m=0),  # 禁用 HNSW：只为 rerank 服务，不做召回
        ),
    },
    sparse_vectors_config={
        # 【sparse】BM25 稀疏向量：维度 = 词表大小，非零位 = 文档里出现的词及其权重。
        # IDF 修饰符：让服务端在打分时使用逆文档频率（罕见词权重高），BM25 的灵魂所在
        "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF),
    },
)

# ------------------------------------------------------------------------------
# 3. 读取本地 CSV 并上传
# ------------------------------------------------------------------------------
# 数据已下载到本地（与脚本同目录），无需再联网下载。
# 列：Title, Author, ISBN, Description
csv_path = Path(__file__).resolve().parent / "top_100_scifi_books_full.csv"


def parse_csv(path: Path):
    """逐行读 CSV 为字典，yield 给生成器，避免一次性载入全部数据。"""
    with open(path, newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f)


# 把每本书构造成一个 Point：id 自增；三个向量字段都是 Document ——
# 在 cloud inference 模式下 Document 不会在本地编码，而是把文本原样交给云端推理。
# 也就是说：100 本书 × 3 个模型 = 300 次文本 embedding，全部发生在 Qdrant 服务端。
points = (
    PointStruct(
        id=idx,
        vector={
            "dense": Document(text=row["Description"], model=dense_embedding_model),
            "sparse": Document(text=row["Description"], model=sparse_embedding_model),
            "multi": Document(text=row["Description"], model=late_interaction_embedding_model),
        },
        payload={
            "title": row["Title"],
            "author": row["Author"],
            "description": row["Description"],  # 实验五本地重排时要用到原文
        },
    )
    for idx, row in enumerate(parse_csv(csv_path))
)

print(f"上传 {csv_path.name} 的全部书籍到 Qdrant Cloud（embedding 在服务端进行）...")
client.upload_points(
    collection_name=collection_name,
    points=points,
    batch_size=25,  # 100 条分 4 批上传，云端逐批推理
)
print("上传完成。\n")

# ------------------------------------------------------------------------------
# 结果打印辅助：让 5 组实验结果易于横向对比
# ------------------------------------------------------------------------------


def show(results, title: str, limit: int = 10):
    """打印一次查询的 top-N 结果：排名 / 分数 / 书名 / 作者。"""
    print("=" * 78)
    print(f"【{title}】")
    print("-" * 78)
    for i, p in enumerate(results.points[:limit], 1):
        print(f" {i:>2}. score={p.score:>9.4f}  《{p.payload['title']}》 - {p.payload['author']}")
    print()


QUERY = "time travel"

# ==============================================================================
# 实验一：纯稠密向量检索（Dense / 语义检索）
# ==============================================================================
# 原理：query 和文档各自编码成 1 个 384 维向量，按余弦相似度用 HNSW 近似最近邻召回。
# 特点：能理解语义（"时光机器" ≈ "time travel"），即使一个词都不重叠也能命中；
#       但对专有名词、型号、人名等必须逐字精确的查询容易"意会"出错。
results = client.query_points(
    collection_name,
    query=models.Document(text=QUERY, model=dense_embedding_model),
    using="dense",
    limit=10,
    with_payload=True,
)
show(results, f"实验一：纯稠密向量检索（dense / all-MiniLM-L6-v2）  query={QUERY!r}")

# ==============================================================================
# 实验二：纯稀疏向量检索（Sparse / BM25 关键词检索）
# ==============================================================================
# 原理：经典 BM25 词法打分——查询词与文档词的字面匹配 + 词频 + 逆文档频率。
# 特点：字面精确匹配（人名、术语、型号最可靠）；但完全不理解同义改写，
#       "time travel" 不会命中只写了 "temporal journey" 的文档。
# 分数是 BM25 得分（无上界，不代表相似度百分比）。
results = client.query_points(
    collection_name,
    query=models.Document(text=QUERY, model=sparse_embedding_model),
    using="sparse",
    limit=10,
    with_payload=True,
)
show(results, f"实验二：纯稀疏向量检索（sparse / BM25+IDF）  query={QUERY!r}")

# ==============================================================================
# 实验三：混合检索 + RRF 融合（Hybrid Search）
# ==============================================================================
# 架构：dense 和 sparse 各自召回 top20（Prefetch 阶段），再用 RRF 融合成一个排序。
# RRF（Reciprocal Rank Fusion）：不比较两路分数（量纲不同没法比），只看【排名】：
#     score(d) = Σ 1/(k + rank_i(d))，k=60
# 两路都排前面的文档得分高，天然互补：语义路补词法路的同义改写，
# 词法路纠正语义路的专有名词偏差。
# 注意：RRF 的 score 只有排序意义，没有绝对数值含义。
prefetch = [
    models.Prefetch(
        query=models.Document(text=QUERY, model=dense_embedding_model),
        using="dense",
        limit=20,
    ),
    models.Prefetch(
        query=models.Document(text=QUERY, model=sparse_embedding_model),
        using="sparse",
        limit=20,
    ),
]

results = client.query_points(
    collection_name,
    prefetch=prefetch,
    query=models.FusionQuery(fusion=models.Fusion.RRF),  # 对两路候选做 RRF 融合
    limit=10,
    with_payload=True,
)
show(results, f"实验三：混合检索 + RRF 融合（dense top20 + sparse top20 → RRF）  query={QUERY!r}")

# ==============================================================================
# 实验四：ColBERT 多向量重排（服务端 rerank / late interaction）
# ==============================================================================
# 与实验三唯一的区别：融合层不再是 RRF，而是用 multivector 向量对候选【重新打分】。
# 流程：prefetch 照旧两路召回 top20 → 把这 20 条候选的 ColBERT 多向量逐一取出，
#       与 query 的多向量做 token 级 MaxSim 精确计算（不经过 ANN，无召回损失）
#       → 按 MaxSim 分数排序取 top10。
# 这就是「用 ColBERT 做重排」：召回仍交给快而便宜的 dense+sparse，
# 精排交给慢而准的多向量交互。多向量在入库时禁了 HNSW（见建集合注释），
# 因此它在这里只能当 reranker，不会被误用于全库召回。
prefetch = [
    models.Prefetch(
        query=models.Document(text=QUERY, model=dense_embedding_model),
        using="dense",
        limit=20,
    ),
    models.Prefetch(
        query=models.Document(text=QUERY, model=sparse_embedding_model),
        using="sparse",
        limit=20,
    ),
]

results = client.query_points(
    collection_name,
    prefetch=prefetch,
    # query 换成 multivector：对 prefetch 候选做 MaxSim 精确重排
    query=models.Document(text=QUERY, model=late_interaction_embedding_model),
    using="multi",
    limit=10,
    with_payload=True,
)
show(results, f"实验四：ColBERT 多向量重排（hybrid 召回 → MaxSim 精排）  query={QUERY!r}")

# ==============================================================================
# 实验五：Cross-Encoder 本地重排（客户端 rerank）
# ==============================================================================
# 前四种都发生在 Qdrant 服务端；这一种把候选拿回本地，用交叉编码器精排。
#
# Cross-Encoder 与双塔（dense）的本质区别：
#   - 双塔：query 和 doc 各自独立编码，打分 = 两个向量的相似度（快，但交互浅）
#   - 交叉编码器：把 [query, doc] 拼接后送进同一个 Transformer，让每个 token
#     与对方 tokens 充分做 attention 后直接输出一个相关性分数（准，但每对都要跑一次模型）
# 因为每对 (query, doc) 都要过一遍模型，它根本没法扫全库 —— 只能对已召回的
# 小候选集（这里 20 条）重排。这是「检索精度天花板最高」的一层。
reranker_model = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")
reranker = TextCrossEncoder(model_name=reranker_model, cache_dir=MODEL_CACHE_DIR)

# 第一步：先复用实验三的混合检索，但取 20 条候选（比最终要的多，给精排留余地）
prefetch = [
    models.Prefetch(
        query=models.Document(text=QUERY, model=dense_embedding_model),
        using="dense",
        limit=20,
    ),
    models.Prefetch(
        query=models.Document(text=QUERY, model=sparse_embedding_model),
        using="sparse",
        limit=20,
    ),
]

candidates = client.query_points(
    collection_name,
    prefetch=prefetch,
    query=models.FusionQuery(fusion=models.Fusion.RRF),
    limit=20,  # 召回 20 条供重排（最终只展示 10 条）
    with_payload=True,
)

# 第二步：本地 cross-encoder 对 20 条候选逐一打分（分数越高越相关，是原始 logits 可为负）
print(f"本地 Cross-Encoder（{reranker_model}）对 {len(candidates.points)} 条候选重排中...")
rerank_scores = list(
    reranker.rerank(
        QUERY,
        [p.payload["description"] for p in candidates.points],
    )
)

# 第三步：按 cross-encoder 分数降序重排，取 top10
# （同时保留每条候选的 RRF 分数，方便观察「重排前后名次变化」）
reranked = sorted(
    zip(rerank_scores, candidates.points),
    key=lambda pair: pair[0],
    reverse=True,
)[:10]

print("=" * 78)
print(f"【实验五：Cross-Encoder 本地重排（hybrid 召回20 → bge-reranker-base 精排）】  query={QUERY!r}")
print("-" * 78)
for i, (ce_score, p) in enumerate(reranked, 1):
    # ce_score = cross-encoder 相关性 logits；p.score = 该候选原本的 RRF 分数
    print(f" {i:>2}. ce={ce_score:>8.3f}  (RRF={p.score:>7.4f})  《{p.payload['title']}》 - {p.payload['author']}")
print()
