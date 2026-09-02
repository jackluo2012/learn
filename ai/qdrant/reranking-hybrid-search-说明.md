# 混合检索与重排序详解 —— reranking-hybrid-search.py

> 配套脚本：`reranking-hybrid-search.py`（数据：`top_100_scifi_books_full.csv`，100 本科幻小说）
> 查询词统一为 `"time travel"`，embedding 全部由 Qdrant Cloud 服务端推理完成。

---

## 0. 一句话总结（TL;DR）

| 方式 | 一句话 | 适合 |
|---|---|---|
| Dense 稠密检索 | 按语义"意会"你的查询 | 同义改写、跨语言、模糊描述 |
| Sparse (BM25) | 按"字面"匹配你的查询 | 专有名词、型号、代码、罕见词 |
| Hybrid (RRF) | 语义 + 字面两路结果按排名融合 | 绝大多数通用搜索系统的默认起点 |
| ColBERT 重排 | token 级精细交互，给候选重新打分 | 服务端精排，精度和延迟的平衡点 |
| Cross-Encoder 重排 | query 和文档拼一起过模型，精度天花板最高 | 对 top 候选做最终精排（RAG 引用排序等） |

一次查询只用一个词 `"time travel"`，五种方式给出**五份不同的排序**——这正是本文要解释的。

---

## 1. 全景图：两阶段检索架构

现代搜索/RAG 系统几乎都是「**召回 → 融合 → 精排**」的多层漏斗：

```
  100 本书的库
       │
       │  第一阶段【召回 Recall】—— 快而糙，扫全库
       │
       ├─── dense 向量检索 (HNSW 近似) ──→ top 20   ← 理解语义
       ├─── sparse BM25 检索           ──→ top 20   ← 精确字面
       │
       │  第二阶段【融合 Fusion】
       │
       └─── RRF 排名融合 ────────────→ top 20 候选
              │
              │  第三阶段【精排 Rerank】—— 慢而准，只看候选
              │
              ├─── ColBERT 多向量 MaxSim（服务端）──→ top 10
              └─── Cross-Encoder（客户端本地）  ──→ top 10
```

**核心矛盾**：效果好和跑得快不可兼得。embedding 检索快是因为它把"理解文本"的工作**提前到了入库时**（每篇文档只编码一次），查询时只算向量夹角；而精排模型必须**在查询时**对每一对 (query, 文档) 现场做深度交互计算。所以精排模型只能喂给已经筛小的候选集（20~200 条），不可能扫全库。

脚本里 5 个实验 = 这个漏斗从上到下的每一层单独演示。

---

## 2. 实验一：Dense 稠密向量检索（语义检索）

### 原理

- 模型：`sentence-transformers/all-MiniLM-L6-v2`，把**一篇文档压成 1 个 384 维向量**
- 入库时算好文档向量，建 HNSW 近似最近邻索引；查询时把 query 也编码成向量，找夹角最近的文档
- 打分：余弦相似度，范围约 0~1

### 关键特性

| 优点 | 缺点 |
|---|---|
| 理解语义：query 说"时光旅行"，文档写 "travels far into the future" 也能命中 | 是"压缩"，细节必然丢失：384 个数字要装下一整篇文档 |
| 对错别字、改写、跨语言有一定容忍度 | 对专有名词、型号、代码不敏感：`all-MiniLM-L6-v2` 分不清 `iPhone 15` 和 `iPhone 14` |
| 查询快（HNSW 只算部分向量） | 两个向量算相似度 = 两次独立编码后对比，query 和文档**从未直接见面**（双塔架构的天花板） |

### 本次实际结果

```
 1. score=0.5158  《The Time Machine》 - H.G. Wells          ← 正确！语义冠军
 2. score=0.4395  《Slaughterhouse-Five》
 3. score=0.4391  《The Peripheral》
 ...
```

 dense 的表现符合直觉：讲时间旅行的开山之作排第一。但注意《Station Eleven》没进前十——它的描述 "A traveling symphony roams a post-pandemic North America" 与时间旅行**语义无关**，dense 正确地过滤掉了它。

---

## 3. 实验二：Sparse 稀疏向量检索（BM25 关键词检索）

### 原理

- 模型：`qdrant/bm25`，把文档表示成**词表大小的稀疏向量**：非零位置 = 出现过的词，权重 = 词频（配合服务端 `Modifier.IDF` 打逆文档频率权重）
- 打分：经典 BM25 —— 命中词越多、词越罕见、文档越短，分越高；**分数无上界，没有相似度的百分比含义**
- 本质：这就是搜索引擎时代的词法检索（Elasticsearch/Lucene 的核心），只是装进了向量接口

### 关键特性

| 优点 | 缺点 |
|---|---|
| 字面精确匹配：人名、药名、零件号、错误码、代码标识符，词法检索最可靠 | 完全不理解语义："time travel" 命中不了只写 "temporal journey" 的文档 |
| 零训练、零幻觉，行为完全可解释 | 只认字面：换个说法、拼写变体之外的同义词全军覆没 |
| 命中词自带证据（哪个词命中的很清楚） | 长尾表达召回差 |

### 本次实际结果（最有教学价值的一组）

```
 1. score=5.1670  《Station Eleven》     ← 描述只有 "A traveling symphony roams..."！
 2. score=5.1534  《Hyperion》           ← "Travelers share haunting tales..."
 3. score=5.1534  《The Space Between Worlds》 ← "A multiverse traveler..."
 4. score=5.1534  《The Time Machine》   ← "travels far into the future"
 ...
```

冠军是《Station Eleven》——一本**和时间旅行毫无关系**的书。原因：

1. BM25 做词干还原后，"travel**ing**"、"travel**er**"、"travel**s**" 全都和 "travel" 匹配；
2. BM25 有**文档长度归一化**：《Station Eleven》的描述是全场最短的（8 个词），命中一次的"浓度"最高，反而反超；
3. 它展示了词法检索的经典失败模式：**字面沾边就算命中，语义完全不管**。

而 dense 排第一的《The Time Machine》在这里只排第 4。两路检索的错误是**错开的**——这就是混合检索的价值来源。

---

## 4. 实验三：Hybrid 混合检索 + RRF 融合

### 原理

两路各自召回 top 20，然后用 **RRF（Reciprocal Rank Fusion，倒数排名融合）** 合并：

```
RRF(d) = Σ over 每一路 : 1 / (k + rank_i(d))
```

- **只看排名，不看分数**：dense 的余弦分（0~1）和 BM25 分（无上界）量纲完全不同，没法直接相加；RRF 聪明地绕开这一点，只问"你在自己那路排第几名"
- Qdrant 的实现中平滑常数取 **k=2**（论文里经典值是 60，k 越大对头部排名的奖励越平缓），rank 从 0 开始
- 用本次真实数据验证《The Time Machine》的 RRF = 0.7：dense 第 1 名贡献 `1/(2+0)=0.5`，sparse 第 4 名（rank=3）贡献 `1/(2+3)=0.2`，合计 **0.7** ✓

### 关键特性

| 优点 | 缺点 |
|---|---|
| 两路错误互补：dense 的同义改写 + BM25 的精确字面 | 分数只有排序意义，**无法当置信度用**（0.7 不代表 70% 相关） |
| 几乎零成本提升：多建一路稀疏向量即可 | 两路都各自取 top-K，**头部之外的文档永久丢失**（融合救不回没被召回的） |
| 是 OpenSearch、Elasticsearch、Qdrant 等的标配能力 | 需要同时维护两种向量（存储 ×2） |

### 本次实际结果

```
 1. score=0.7000  《The Time Machine》      ← dense 第1 + sparse 第4，两路合力登顶
 2. score=0.5476  《Station Eleven》        ← BM25 第1强行带进前二（dense 漏掉的）
 3. score=0.5000  《Slaughterhouse-Five》   ← 两路都排第3，稳步居中
 4. score=0.4500  《The Space Between Worlds》
 5. score=0.4242  《Hyperion》
 ...
```

对比观察：

- 《The Time Machine》：dense 第 1、sparse 第 4 → RRF 第 1，**两路都认可**的文档在融合后吃红利；
- 《Station Eleven》：dense 前 20 都没有它，但 BM25 第 1 → RRF 第 2。**词法路把语义路看漏的硬拽了回来**——注意这是把"错"也拽回来了（它确实不相关），融合本身不判断对错，只折中两路意见。

到这一层，系统已经有了"语义 + 字面"的双重视角，但所有打分仍然停留在**单向量（或者排名）粒度**。最后一层精排要解决的是：候选集已经很小了，能不能让 query 和文档**真正深度见面**？

---

## 5. 为什么要重排（Reranking）？

先看两种模型的本质区别：

```
Bi-Encoder（双塔，实验一）          Cross-Interaction（深度交互，实验四/五）
                                   
query  ──编码──▶ q向量 ─┐          query 文档
                        ├─夹角─▶ 分   └──拼接──▶ 同一个Transformer ──▶ 分
doc    ──编码──▶ d向量 ─┘                        （token 间互相 attention）
                                   
两份表示从未直接见面                 每个 query token 都和所有 doc token 交互
快：文档可以提前编码入库             慢：每一对 (query, doc) 都要现场跑一遍模型
糙：一篇文档压成一个点               准：精度天花板最高
```

双塔的结构性缺陷：**一篇 100 词的文档被压成 1 个向量**，无论向量维度多高，"查询词到底和文档里哪个词对上了"这个信息都丢了。深度交互模型把计算留到查询时，精度上一个台阶——代价是没法提前算，所以只能对小候选集用。

**重排 = 用精排模型的准，补召回模型的糙，但只对已经筛出来的 20~200 条候选算账。** 这就是两阶段架构的全部动机。

### 5.1 实验四：ColBERT 多向量重排（服务端）

- 模型：`answerdotai/answerai-colbert-small-v1`，**一篇文档 = N 个 96 维向量（每个 token 一个）**，称为多向量（multivector）
- 打分：**MaxSim** —— 对每个 query token，在文档所有 token 向量里找最相似的那个（Max），再对所有 query token 求和（Sim）。相当于"轻量级的深度交互"：比单向量细 100 倍，比 full cross-encoder 便宜得多
- **存疑点解答——建集合时为什么 `hnsw_config=HnswConfigDiff(m=0)`**：
  - 每篇文档几十到几百个 token 向量，若给多向量建 HNSW 索引，索引体积和构建时间都会暴涨；
  - 而 `m=0` 之后多向量**无法做全库 ANN 召回**，只能对 `prefetch` 送来的候选逐条精确算分；
  - 这等于在数据库层面就把多向量**锁死为纯 reranker**，召回它管不了，也不会有人误用它做召回。存储换精度：多向量的存储开销是单向量的几十倍，只在精排这个收益最大的环节使用它。

```
 1. score=4.6984  《Slaughterhouse-Five》  ↑2  "time-tripping"
 2. score=4.6474  《The Forever War》      ↑6  "time dilation"
 3. score=4.6472  《Kindred》              ↑3  "pulled back in time"
 4. score=4.6340  《Spin》
 5. score=4.5907  《The Light Brigade》
 6. score=4.5856  《The Time Machine》     ↓5  ← 语义冠军被拉下来了
 ...
```

解读（体现了 ColBERT 的"品味"）：

- 《Forever War》从 hybrid 的第 8 升到第 2——token 级匹配捕捉到 "time dilation"（时间膨胀）里高频的 "time" 与 "time travel" 的**逐 token 命中密度**；
- 《The Time Machine》降到第 6——它的描述 "A Victorian scientist travels far into the future" 里 "time" 只出现 1 次，token 重叠密度反而低。**ColBERT 眼中的"相关"= token 级命中密度**，与整篇文档的语义（dense 的"相关"）是两种不同的判断标准；
- 注意所有分数挤在 4.52~4.70 之间：MaxSim 分数区分度天然偏小，**比较的是相对顺序**，不要看绝对值。

### 5.2 实验五：Cross-Encoder 本地重排（客户端）

前面所有检索都发生在 Qdrant 服务端；这一步把候选拉回本地，用 **BAAI/bge-reranker-base**（onnx 已预下载到 `local_cache`，离线运行）重排：

- **把 `[query, 文档]` 拼接成一个输入**送进同一个 Transformer，token 之间充分互相 attention 后直接输出一个相关性分数（原始 logits，可为负，只有排序意义）
- 这是**深度交互的完全体**：ColBERT 是"token 对 token 的轻量交互"，cross-encoder 是"整句放进同一个上下文里彻底交互"
- 因为每一对都要现场过一遍模型，**它永远不可能扫全库**——只能服务精排

```python
# 脚本中的三步：
candidates = client.query_points(...)          # ① hybrid RRF 召回 20 条
scores = reranker.rerank(QUERY, descriptions)  # ② 本地模型对 20 对 (query, doc) 打分
reranked = sorted(zip(scores, candidates), reverse=True)  # ③ 按新分排序取 top10
```

```
 1. ce= -2.563  (RRF=0.1111) 《The Sirens of Titan》  ← RRF 排名靠后，被精排捞回
 2. ce= -3.778  (RRF=0.2500) 《The Peripheral》       ← "Two timelines intersect"
 3. ce= -5.705  (RRF=0.2679) 《Spin》
 4. ce= -5.888  (RRF=0.5000) 《Slaughterhouse-Five》
 ...
 9. ce= -7.856  (RRF=0.7000) 《The Time Machine》    ← 全场语义冠军降到第 9！
```

解读（同样重要——**重排不是魔法**）：

- 排序剧变的原因：cross-encoder 的"相关性判断"与前面所有方式都不同，它看到的是完整的 query+doc 交互，权衡完全属于另一个模型的世界；
- 《The Sirens of Titan》RRF 只有 0.11（第 18 名附近）却被推到第 1：**召回阶段 ranking 看漏的候选，精排有第二次机会**，这是重排层独有的价值；
- 反面教材同样真实：`bge-reranker-base` 是一个较小、偏中文场景的模型，对一句话英文书介的判断与人类直觉有明显出入（《The Time Machine》掉到第 9）。**精排的质量上限 = reranker 模型本身**——生产中应换更强的模型（`BAAI/bge-reranker-v2-m3`、Cohere Rerank、Voyage rerank 等）并用自有标注数据评测，"挂了重排就一定更好"并不成立。

---

## 6. 五种方式横向对比总表

| | 实验一 Dense | 实验二 Sparse/BM25 | 实验三 Hybrid RRF | 实验四 ColBERT 重排 | 实验五 Cross-Encoder |
|---|---|---|---|---|---|
| **打分原理** | 两个单向量算余弦 | 词法匹配 + TF-IDF | 两路排名倒数求和 | query/doc token 向量两两 MaxSim | query+doc 拼接过同一个模型 |
| **交互深度** | 无（双塔） | 无（字面） | 无（只看排名） | token 级（浅交互） | 全 token 互相 attention（完全交互） |
| **query 与文档何时见面** | 永不见面 | 词对词 | 从不见面 | 查询时逐 token 对 | 查询时整句见面 |
| **分数含义** | 余弦相似度 0~1 | BM25 分，无上界 | 纯排序意义 | 相对排序意义 | logits，纯排序意义 |
| **能否做全库召回** | ✅ HNSW | ✅ 倒排/稀疏索引 | ✅（组合召回） | ❌（本例故意 m=0 禁用） | ❌ 成本不允许 |
| **能否做精排** | 勉强 | 不能 | 不能 | ✅ 主场 | ✅ 天花板 |
| **计算开销（查询时）** | 低 | 低 | 低（多一路） | 中（候选数 × token 数） | 高（候选数 × 模型前向） |
| **存储开销** | 384 维 ×1 | 稀疏向量 | 两者之和 | **96 维 ×N tokens，几十倍** | 无（模型在客户端） |
| **可解释性** | 差 | 强（哪个词命中一目了然） | 差 | 中 | 差 |
| **本次 top1** | The Time Machine ✓ | Station Eleven ✗ | The Time Machine ✓ | Slaughterhouse-Five | The Sirens of Titan |

---

## 7. 选型指南：什么场景用什么

### 只用 Dense（实验一）就够了，当：

- 语料是自然语言长文本（文章、评论、说明书）
- 用户查询是口语化描述，且不涉及精确专有名词
- 对延迟极其敏感、想保持架构最简单
- 典型：推荐"相似内容"、聊天记忆检索

### 必须上 BM25 / Hybrid（实验二、三），当：

- 查询里充满**必须逐字命中的 token**：型号（`RTX 4090`）、错误码（`ECONNRESET`）、人名药名、法律条款编号、SKU
- 语料有大量专有名词、缩写、罕见词（BM25 的 IDF 对罕见词加权，dense 反而会"平均掉"它们）
- 这也是为什么**通用搜索系统默认就该是 hybrid**：你无法预知用户下一次查的是"怎么缓解焦虑"（语义）还是`ERR_CONNECTION_RESET`（字面）

### 再加一层重排（实验四、五），当：

- 精度带来的业务价值高：RAG 的引用排序（引用错 = 回答错）、法律/医疗检索、问答系统
- 能接受额外延迟：精排只算 top 20~100 候选，通常增加几十毫秒到几百毫秒
- 记住两阶段口诀：**召回要快所以粗，精排要准所以窄**

### ColBERT 重排 vs Cross-Encoder 重排怎么选？

| | ColBERT 多向量（实验四） | Cross-Encoder（实验五） |
|---|---|---|
| **跑在哪** | Qdrant **服务端**（向量已入库） | **客户端/应用侧**（要先取回候选文本） |
| **延迟** | 低（MaxSim 是矩阵运算，数据库内完成） | 高（每候选一次 transformer 前向） |
| **精度** | 好（轻量交互） | 更好（完全交互，精度天花板） |
| **额外成本** | 入库时多算多存（多向量体积大） | 查询时多算；模型要自己部署/维护 |
| **适合** | 想在数据库一层解决、延迟敏感、候选量稍大 | 精度优先、候选量小（top 10~50）、有 GPU 或容忍 CPU 排 20 条 |
| **典型搭配** | hybrid 召回 → ColBERT 精排（本脚本实验四） | hybrid 召回 → ColBERT → Cross-Encoder 三级漏斗（超重场景） |

### 推荐的生产默认架构

```
用户查询
   │
   ▼
hybrid 双路召回 top 50~200 ──▶ RRF 融合取 top 20~50      ← 数据库内完成，毫秒级
   │
   ▼
ColBERT 或 Cross-Encoder 重排 ──▶ top 10                ← 一层精排，覆盖 90% 场景
   │
   ▼
（可选）LLM 生成回答 / 直接返回列表
```

> 实践数字：召回 100+ 候选、精排到 10，是性价比最高的一档；把精排候选从 50 加到 500，质量提升很小、延迟翻好几倍。

---

## 8. 本次运行环境与脚本要点

- 连接：Qdrant Cloud，`cloud_inference=True` —— **所有 embedding（dense/sparse/multi 的入库与查询编码）都在 Qdrant 服务端完成**，本地不加载任何 embedding 模型
- 数据：本地 `top_100_scifi_books_full.csv`（Title/Author/ISBN/Description），不再从 GitHub 下载
- 同一个点的三个具名向量：`dense`(384) + `sparse`(BM25+IDF) + `multi`(ColBERT 96 维多向量，禁 HNSW)
- 唯一本地模型：实验五的 `BAAI/bge-reranker-base`（onnx 预下载于 `local_cache`，`HF_HUB_OFFLINE=1` 离线加载）
- 修复的原脚本问题：
  1. CSV 改为读本地文件（原来 `urllib` 拉 GitHub raw，网络不稳即失败）
  2. 补上 `PointStruct` / `Document` 显式导入
  3. 原脚本导入了 `TextCrossEncoder` 却从未使用——补全为实验五
  4. `pprint` 整包输出难以阅读——改为统一格式化打印，五种方式可直接横向对比
