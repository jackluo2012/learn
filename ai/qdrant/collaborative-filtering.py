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
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Document
# connect to Qdrant Cloud
client = QdrantClient(
    url=required_env("QDRANT_URL"),
    api_key=required_env("QDRANT_API_KEY"),
    cloud_inference=True,
)
COLLECTION_NAME = "test-items"
# 集合不存在时才创建
if not client.collection_exists(COLLECTION_NAME):
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE,
        ),
    )
else:
    print(f"Collection `{COLLECTION_NAME}` already exists, skip creation.")
