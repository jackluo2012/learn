# Qdrant 练习

## cloud-inference-hybrid-search.py

Qdrant Cloud **Inference（服务端推理）** + **混合检索（Hybrid Search）** 练习脚本：

- 从 HF 下载 `miriad/miriad-4.4M` 数据集的前 100 条（流式，只拉几 MB）
- 上传到 Qdrant Cloud 集合 `miriad-miriad-4-4M`，稠密向量 `dense_vector`（all-MiniLM-L6-v2，384 维）+ 稀疏向量 `bm25_sparse_vector`（BM25 + IDF）
- 嵌入均在 Qdrant Cloud 服务端完成（`cloud_inference=True`，本地不用跑模型）
- 用 `Prefetch` 双路召回 + `FusionQuery(RRF)` 融合，查询 "What is relapsing polychondritis?"

## 运行方式

```bash
https_proxy=http://127.0.0.1:7897 http_proxy=http://127.0.0.1:7897 \
  .venv/bin/python cloud-inference-hybrid-search.py
```

- 环境在 `.venv`（Python 3.12），`.env` 里配 `QDRANT_URL` / `QDRANT_API_KEY`
- **必须挂代理环境变量**，见下方踩坑记录 ①
- 代理只需 http 协议；**不要**设 `all_proxy=socks5://`——qdrant_client 底层的 httpx 未装 socksio，会直接 `ImportError`

## reranking-hybrid-search.py

**混合检索 + 重排序**练习脚本，在 100 本科幻小说上用同一个查询词 `"time travel"` 依次演示 5 种检索方式并对比结果差异：

1. Dense 稠密向量检索（all-MiniLM-L6-v2，语义）
2. Sparse BM25 检索（qdrant/bm25 + IDF，关键词）
3. Hybrid 双路召回 + RRF 融合
4. ColBERT 多向量重排（服务端，token 级 MaxSim，`hnsw_config=m=0` 锁定为纯 reranker）
5. Cross-Encoder 本地重排（客户端，BAAI/bge-reranker-base，离线从 local_cache 加载）

- 数据：本地 `top_100_scifi_books_full.csv`（不再联网下载）；embedding 全部走 Qdrant Cloud 服务端推理
- 运行：`.venv/bin/python reranking-hybrid-search.py`
- 📖 详细原理、五种方式对比表、选型指南见 [reranking-hybrid-search-说明.md](reranking-hybrid-search-说明.md)

## 踩坑记录（2026-09-01）


### ① HF 大文件下载断流，进程卡死

huggingface.co 主站（API、元数据）可以直连，但真正的数据文件走 **cdn-lfs / xet 通道**，直连会被墙 SSL 中断——表现为 `.incomplete` 缓存文件停在几百 KB 不再增长、进程无输出挂死。

解决：给进程挂本机代理（Clash 混合端口 7897），实测下载约 3 MB/s。

```bash
https_proxy=http://127.0.0.1:7897 http_proxy=http://127.0.0.1:7897 <命令>
```

小文件（几百 KB 的模型配置等）直连一般没事；大文件（parquet、模型权重）必须挂代理。`HF_HUB_OFFLINE=1` 只适合已有本地缓存的场景。

### ② `split="train[0:100]"` 会下载整个数据集

`load_dataset(..., split="train[0:100]")` 是**非流式**切片：先把全部 49 个 parquet（约 **6.3 GB**）下载完，再做切片，之后还要再花十几 GB 磁盘做 Arrow 缓存——只为了取 100 条。

解决：脚本已改为流式读取，只按需拉取行组（几 MB）：

```python
ds = islice(load_dataset("miriad/miriad-4.4M", split="train", streaming=True), 100)
```

后续 `for idx, item in enumerate(ds)` 迭代行为与非流式完全一致，无需改动。

### 其他

- 中断的全量下载会在 `~/.cache/huggingface/hub/datasets--miriad--miriad-4.4M` 留下 parquet 残片（约 130 MB），不碍事，可整目录删除
- 首次运行已创建集合；之后再跑会打印 `already exists, skip creation`，重复运行会以新 UUID 重复上传这 100 条

## 预期输出

RRF 融合后返回 5 条，前 3 名命中同一篇 relapsing polychondritis（复发性多软骨炎）论文的相邻段落（qa_id 前缀 `38_77498699`），score 0.75 / 0.75 / 0.67，另有两条低分相关结果 0.2。
