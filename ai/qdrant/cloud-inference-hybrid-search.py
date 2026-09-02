import os
from pathlib import Path
from dotenv import load_dotenv
# 加载当前脚本目录下的 .env
load_dotenv(Path(__file__).resolve().parent / ".env")

def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"缺少环境变量: {name}")
    return value

# 必须在 fastembed 导入前设置
os.environ["HF_HUB_OFFLINE"] = os.getenv("HF_HUB_OFFLINE", "1")

from fastembed import TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from qdrant_client import QdrantClient,models
from qdrant_client.models import Distance, VectorParams, PointStruct, Document
# connect to Qdrant Cloud
client = QdrantClient(
    url=required_env("QDRANT_URL"),
    api_key=required_env("QDRANT_API_KEY"),
    cloud_inference=True,
    timeout=30,  # 设置超时时间为 30 秒
)
COLLECTION_NAME = "miriad-miriad-4-4M"
# 集合不存在时才创建
if not client.collection_exists(COLLECTION_NAME):
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            "dense_vector": models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            )
        },
        sparse_vectors_config={
            "bm25_sparse_vector": models.SparseVectorParams(
                modifier=models.Modifier.IDF # 启用逆文档频率
            )
        }
    )
else:
    print(f"Collection `{COLLECTION_NAME}` already exists, skip creation.")

from qdrant_client.http.models import PointStruct, Document

# 数据集下载需要联网：离线开关在 huggingface_hub 导入时（由 fastembed 带入）已固化为 True，
# 只改回环境变量不够，必须在 import datasets 前把已固化的常量一并改回
os.environ["HF_HUB_OFFLINE"] = "0"
import huggingface_hub.constants as _hf_constants
_hf_constants.HF_HUB_OFFLINE = False

from datasets import load_dataset
from itertools import islice
import uuid

dense_model = "sentence-transformers/all-minilm-l6-v2"

bm25_model = "qdrant/bm25"

# 流式读取：split="train[0:100]" 是非流式切片，会先下载全部 49 个 parquet（约 6.3GB）再切前 100 条；
# streaming=True 只按需拉取行组，几 MB 即可拿到前 100 条
ds = islice(load_dataset("miriad/miriad-4.4M", split="train", streaming=True), 100)

points = []

for idx, item in enumerate(ds):
    passage = item["passage_text"]

    point = PointStruct(
        id=uuid.uuid4().hex,  # 设置唯一的ID
        payload=item,
        vector={
            "dense_vector": Document(
                text=passage,
                model=dense_model
            ),
            "bm25_sparse_vector": Document(
                text=passage,
                model=bm25_model
            )
        }
    )
    points.append(point)

client.upload_points(
    collection_name=COLLECTION_NAME, 
    points=points, 
    batch_size=8
)


query_text = "What is relapsing polychondritis?"


results = client.query_points(
    collection_name=COLLECTION_NAME,
    prefetch=[
        models.Prefetch(
            query=models.Document(
                text=query_text,
                model=dense_model
            ),
            using="dense_vector",
            limit=5
        ),
        models.Prefetch(
            query=models.Document(
                text=query_text,
                model=bm25_model
            ),
            using="bm25_sparse_vector",
            limit=5
        )
    ],
    query=models.FusionQuery(fusion=models.Fusion.RRF),
    limit=5,
    with_payload=True
)

print(results.points)