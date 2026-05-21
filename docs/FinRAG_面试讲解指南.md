# FinRAG 面试讲解指南

> 适用对象：Jamie 面试前快速理解、复盘和背诵。
> 项目路径：`/Volumes/KINGSTON/projects/finRAG`
> 文档定位：这不是 README，而是一份“面试怎么讲”的讲稿 + 追问答法。
> 当前版本口径：v1.4 Advanced RAG Retrieval Architecture，覆盖 Phase 17-22 和 Phase 21.1 前端展示升级。
> 重要原则：面试时要明确区分 **当前 live provider 配置**、**离线 mock fallback / 测试能力**、**已经实现的功能**、**旧语料可能需要 reimport/reindex 才能展示的层级元数据**、**下一步生产化优化**。

---

## 0. 项目一句话定位

**FinRAG 是一个面向金融研究场景的本地 RAG Agent 面试展示项目：它把公开金融 PDF 文档经过可审计的数据管线转换为 chunks 和索引，查询时通过结构化查询理解、知识路由、元数据过滤、多阶段检索、rerank、证据压缩、迭代检索、层级下钻和带引用生成，最终在前端用 SSE 把整个 RAG 处理过程可视化出来。**

如果只能讲 20 秒，可以说：

> 我做的是一个金融研究场景的 RAG Agent demo，不是普通聊天机器人。它的重点不是只调大模型 API，而是展示一套可追溯、可观测、可降级的 RAG 工程链路：PDF 入库、chunk/index 构建、结构化 query plan、路由和过滤、多阶段召回、rerank、证据压缩、引用式生成，以及前端对每个中间阶段的可视化。

v1.4 之后的升级重点可以压缩成一句：

> v1.4 把原来“一个 hybrid retrieve(query) 返回 top-k”的黑盒检索，升级成 Query Plan -> Route/Filter -> Cascade Trace -> Iterative Retrieval -> Hierarchy Drill-down -> Evidence Pack -> Grounded Answer 的可解释流水线。

---

## 0.1 当前运行口径：现场调用模型，不靠 mock 数据

当前项目有两套 provider 口径，面试时必须说清楚：

- **面试展示 / 本地 `.env`：live provider**
  - `FINRAG_EMBEDDING_PROVIDER=bailian`
  - `FINRAG_RERANK_PROVIDER=bailian`
  - `FINRAG_TEXT_PROVIDER=bailian`
  - 模型包括 `text-embedding-v4`、`qwen3-rerank`、`qwen-plus`

- **测试 / 无网兜底：mock provider**
  - pytest 和 `.env.example` 默认使用 mock。
  - mock embedding/rerank/text 用于稳定回归测试、无 API key 环境和 provider 失败兜底。

面试推荐表达：

> 这个项目不是用 mock 数据写死答案。当前演示配置会现场调用 Bailian/Qwen：embedding 生成向量，rerank 做候选精排，text provider 生成最终带引用答案。mock provider 是为了单元测试和网络失败兜底，体现可测试、可降级和 provider 可替换，不是主展示链路。

---

## 1. 面试 1-2 分钟开场讲法

可以按下面这段背：

> FinRAG 是我为了展示金融 RAG 工程能力做的一个本地 MVP。它的用户假设是金融研究员或投顾分析师，典型问题包括“英伟达某季度营收是多少”“宁德时代近期有哪些经营风险”“宏观消费变化如何影响贵州茅台盈利能力”。
>
> 我没有把它做成只会聊天的 demo，而是按真实 RAG 系统拆成三层。第一层是数据治理，从公开 PDF 文档开始，用 `pdf2md --profile finrag` 转成带 frontmatter、页码 marker 和 hash 的 Markdown，再由 backend importer 统一成 `documents.json`、`chunks.json`，并构建 BM25 和 vector index。第二层是 v1.4 查询链路，FastAPI 收到问题后先生成结构化 `RetrievalPlan`，里面有 intent、task_type、entities、metrics、time_range 和 retrieval_strategy；然后根据 plan 做知识路由、metadata filter、多阶段召回、RRF 融合、rerank、EvidencePack 证据压缩；对风险、原因、趋势类问题，还会触发规则化的 iterative retrieval；如果命中 section/table 父 chunk，还能做 hierarchy drill-down 扩展子证据。第三层是展示层，React 前端通过 SSE 接收 `query_rewrite`、`retrieval_complete`、`rerank_complete`、`answer_chunk`、`done` 等事件，右侧不只展示 BM25/Vector/Rerank，还展示 Query Plan、Route & Filters、Cascade、Iterative Steps、Hierarchy & Drill-down。
>
> 这个项目我强调三个取舍：第一，金融问答必须可追溯，所以答案后有 citation，右侧能看到证据；第二，演示不靠假数据，当前 `.env` 已切到 Bailian/Qwen live provider，mock 只是测试和失败兜底；第三，每个新增能力都保持向后兼容和多层降级，所以即使 rerank、metadata filter、iterative retrieval 或向量维度出现问题，也能回退到稳定路径并把降级原因显示出来。

---

## 2. 系统整体架构

### 2.1 数据管线视角

```text
公开 PDF 文档
  data/docs/source_documents/**/*.pdf
        |
        v
pdf2md --profile finrag
        |  输出带 frontmatter、页码 marker、hash、manifest 的 raw Markdown
        v
backend/app/data/raw/
  extracted/<collection-name>/*.md
  _meta/*-manifest.{md,json}
        |
        v
backend/scripts/import_corpus.py
        |  统一 Document / Chunk schema，补充 doc/chunk metadata
        |  v1.4 可生成 section/table 父子层级 metadata
        v
backend/app/data/processed/
  documents.json
  chunks.json
        |
        v
backend/scripts/build_index.py
        |  构建 BM25 index + vector index
        v
backend/app/data/index/
  bm25_index.json
  vector_index.json
```

### 2.2 v1.4 查询链路视角

```text
用户问题
  |
  v Phase 17
Structured Query Understanding
  RetrievalPlan { intent, task_type, entities, metrics, time_range, strategy, filters, signals }
  |
  v Phase 18
Knowledge Routing + Metadata Filtering
  choose_route(plan) + apply_metadata_filters(strict -> relaxed -> all)
  |
  v Phase 19
Multi-stage Retrieval Cascade Trace
  query_plan -> coarse_recall -> metadata_filter -> hierarchy_drill_down -> fusion -> rerank -> final_evidence
  |
  +-- Phase 21: analytical/reasoning 查询可触发 2-3 步 iterative retrieval
  |
  v Phase 22
Hierarchy Drill-down
  section/table 父 chunk -> parent_id/child_ids 扩展子 evidence
  |
  v Phase 20
Evidence Compression
  EvidencePack 去重、字段保留、文本截断、citation_id 保持一致
  |
  v
Answer Generation
  Qwen/Bailian live provider + citation spans + SSE streaming
```

### 2.3 前端展示视角

```text
React / Vite frontend
  左侧：示例问题 + 文档库 + KB 管理入口
  中间：SSE 阶段进度 + Markdown 答案 + citation click
  右侧：RAG Process Inspector
    - Query Plan
    - Route & Filters
    - Cascade
    - Iterative Steps
    - Hierarchy & Drill-down
    - BM25 / Vector / Rerank evidence panels
```

---

## 3. 基础数据流：PDF -> Markdown -> chunks -> index

### 3.1 PDF -> Markdown

相关模块：

- `pdf2md/src/elite_daily_pdf_to_md/finrag.py`
- `backend/app/data/raw/`

核心做法：

- FinRAG profile 把金融 PDF 转到 backend raw 目录。
- Markdown frontmatter 保留 `domain`、`collection`、source PDF、title、extractor、page count、char count、`pdf_sha256`、`content_hash` 等。
- 正文保留 `<!-- page: 1 -->` 页码 marker，后续 chunk 可继承页码用于引用追溯。
- 生成 manifest 记录成功、跳过、失败，便于复跑和审计。

面试讲点：

> 我没有把 PDF 解析塞进在线查询链路，而是离线 ingestion。这样查询延迟稳定，而且 PDF 解析失败、hash、manifest 都能审计。金融文档尤其是财报和研报，更适合先做离线质量控制。

### 3.2 Markdown -> documents/chunks

相关模块：

- `backend/app/core/ingestion/raw_loader.py`
- `backend/app/core/ingestion/corpus_importer.py`
- `backend/app/core/ingestion/chunker.py`
- `backend/app/models/schemas.py`

当前数据口径：

- 公开 demo corpus 约 40 篇文档，覆盖宁德时代、贵州茅台、NVIDIA、台积电。
- 历史语料已有约 9303 个基础 chunk；Phase 22 后重新 import/reindex 可生成 section/table parent chunk 和 hierarchy metadata。
- chunk metadata 包含 doc/company/type/page/section 等字段；v1.4 进一步可包含 `chunk_level`、`parent_id`、`child_ids`、`section_title`、`section_path`。

注意口径：

> 如果面试时要稳定展示 hierarchy drill-down，旧索引需要经过 Phase 22 后的 importer 重新处理和重建索引。前端不会伪造 parent-child 数据；没有 metadata 时会显示 unavailable。

### 3.3 chunks -> BM25 / vector index

相关模块：

- `backend/app/core/retrieval/bm25_store.py`
- `backend/app/core/retrieval/vector_store.py`
- `backend/app/core/providers/embeddings.py`

当前实现：

- BM25：`jieba` + `rank_bm25`，适合公司名、股票代码、财务科目、季度等精确词。
- Vector：本地 JSON vector matrix + cosine similarity，provider 抽象支持 mock 和 Bailian。
- 当前不是 FAISS 文件索引。更准确的说法是：模块边界已经为后续替换 FAISS、pgvector、Milvus、Qdrant 留好。

面试讲点：

> 金融问答既有精确词，也有抽象语义。BM25 稳定命中公司名和指标，向量检索处理“经营风险、宏观影响”这类语义问题，RRF 融合不要求两路分数同尺度，所以工程上稳。

---

## 4. v1.4 核心升级：Phase 17-22

### 4.1 Phase 17：结构化查询理解

解决的问题：旧版 `analyze_query()` 只有 expanded terms 和 intent，下游不知道这是“营收数字查询”还是“经营风险分析”。

核心产物：`RetrievalPlan`

```python
RetrievalPlan {
    original_query
    normalized_query
    intent              # factual / analytical / reasoning
    task_type           # metric_lookup / causal_analysis / risk_analysis / trend_analysis / comparison / general_analysis
    entities            # 规范化实体，例如 英伟达 -> NVIDIA
    metrics             # 规范化指标，例如 营收 -> revenue
    time_range          # year / quarter / fiscal / relative / raw
    preferred_doc_types
    retrieval_strategy  # table_fact_first / financial_report_first / research_report_analysis / general_hybrid
    filters
    signals
}
```

面试讲点：

- 规则化 query plan 比“直接把 query 丢给 retriever”更可控。
- 实体和指标规范化避免 “英伟达 / NVIDIA / NVDA” 在下游漂移。
- 演示场景下规则系统比 LLM planner 更确定、可测、可复现，未来可以把 planner 替换成 LLM。

### 4.2 Phase 18：知识路由和元数据过滤

解决的问题：不同问题不应该走同一套检索策略。

四种主要 route：

| Route | 典型问题 | 检索偏好 |
| --- | --- | --- |
| `table_fact_first` | “NVIDIA FY2026 Q3 营收是多少？” | 表格事实 / 财报 |
| `financial_report_first` | 有公司、有期间、偏财报定位 | 财报优先，研报兜底 |
| `research_report_analysis` | 风险、原因、趋势、比较 | 研报优先，财报补充 |
| `general_hybrid` | 无明显结构信号 | 通用 BM25 + vector |

metadata filter 的三层降级：

```text
strict filters 命中足够候选
  -> 直接返回
strict filters 候选不足
  -> 放松 chunk_type/year/quarter 等约束
仍不足
  -> 回退全量候选，并记录 fallback_reason
```

面试讲点：

> 现在的过滤在实现上是 post-recall filter，因为本地 JSON vector store 不支持原生 filter pushdown。trace 里会明确标注 `applied_at: post_recall`，这比把它伪装成真正 pre-filter 更诚实。后续换 Qdrant、Milvus、pgvector 后，可以把同一套 filter contract 下推到向量库。

### 4.3 Phase 19：多阶段检索级联追踪

解决的问题：旧版只有最终 fused list，看不到每个阶段召回了多少、过滤了多少、是否降级。

核心模型：`RetrievalCascadeStage`

```python
RetrievalCascadeStage {
    name            # query_plan / coarse_recall / metadata_filter / hierarchy_drill_down / fusion / rerank / final_evidence
    method          # bm25+vector+supplemental / metadata_post_recall_filter / rrf / ...
    input_count
    output_count
    degraded
    fallback_reason
    metadata
}
```

面试讲点：

- trace 不是日志，而是可返回给前端和 debug API 的结构化数据。
- input/output count 足够支撑演示和排障，不把每个候选详情塞进 SSE。
- 如果答案错，可以沿着 cascade 看是 query plan 错、召回错、filter 错、rerank 错还是生成错。

### 4.4 Phase 20：证据压缩和 Context Builder

解决的问题：直接把 Top5 chunk 全文塞给 LLM 容易重复、冗长，并可能丢失表格事实 metadata。

核心产物：`EvidencePack`

- 按 chunk_id、表格事实 key、文本摘要 key 去重。
- 表格事实保留 `metric/value/unit/period/page/source` 等字段。
- 长文本生成 `compact_content`，但前端 evidence 仍能保留原始内容字段。
- citation_id 在压缩前后保持一致，避免引用错位。

面试讲点：

> 我没有让 LLM 再做一次黑盒压缩。表格事实用结构化模板无损保留，文本按规则截断和去重，这样更便宜、更可测，也更容易解释。

### 4.5 Phase 21：迭代检索 Demo 模式

解决的问题：“经营风险”“宏观影响”“趋势原因”这类问题，单次检索容易只拿到一个角度，缺少背景、驱动和交叉验证。

触发条件：

- `task_type` 属于 `risk_analysis`、`causal_analysis`、`trend_analysis`、`comparison`。
- 非 `table_fact_first` 精确表格事实查询。

规则化步骤：

| Step | purpose | 目标 |
| --- | --- | --- |
| 1 | `background_facts` | 先召回基础事实 |
| 2 | `risk_or_driver_evidence` | 召回风险、原因、驱动因素 |
| 3 | `cross_check` | 对 risk/causal/comparison 增加交叉验证或反向证据 |

降级策略：

- planner 异常 -> single-pass
- step 执行异常 -> single-pass
- 多步合并后没有证据 -> single-pass
- 降级原因通过 trace 暴露，不让用户拿到空结果。

面试讲点：

> 这是 agentic retrieval 的确定性 baseline。真正 ReAct agent 会根据每步结果动态决定下一步，但面试 demo 更需要可复现和可测试，所以先用规则规划。后续替换 `plan_iterative_retrieval()` 即可升级成 LLM-driven planner。

### 4.6 Phase 22：层级分块与下钻

解决的问题：旧 chunk 只有段落粒度，命中段落后看不到所属章节，命中表格行后看不到表格全貌。

Import 阶段：

- markdown heading 识别出 section path。
- section 生成 `chunk_type=section` 的父 chunk。
- 父 chunk 有 `child_ids`，子 chunk 有 `parent_id`。
- table 和 table_row 也可建立父子关系。

Retrieval 阶段：

- 命中 section/table 父 chunk 后，按 parent_id/child_ids 找子 chunk。
- 每父最多扩展 3 个子 chunk，全局最多 8 个。
- 子 evidence 进入 supplemental hits，再参与 RRF 融合。
- 仅在适合的 analytical/reasoning 路径启用，避免污染精确数字查询。

面试讲点：

> 我没有重写整个 retriever，而是把 hierarchy drill-down 设计成召回后的可插拔扩展层。这样 BM25/vector store 接口保持稳定，旧消费者不受影响，新 trace 里能看到 `hierarchy_drill_down` 阶段。

---

## 5. 前端 v1.4 展示怎么讲

Phase 21.1 的目标不是做生产级简洁 UI，而是把工程处理过程展示出来。右侧栏现在是一个 RAG Process Inspector，展示真实 SSE payload 字段，不伪造后端没有的数据。

### 5.1 Query Plan 面板

来源：`query_rewrite` SSE 事件中的 `plan`。

展示内容：

- intent：`factual / analytical / reasoning`
- task_type：`metric_lookup / causal_analysis / risk_analysis / trend_analysis / comparison / general_analysis`
- retrieval_strategy：`table_fact_first / financial_report_first / research_report_analysis / general_hybrid`
- entities、metrics、preferred_doc_types、time_range
- expanded terms 和 sub_queries

面试讲法：

> 这一块证明系统不是直接检索字符串，而是先把金融问题结构化成下游可消费的 plan。后面的 route、filter、iterative retrieval 都基于这个 plan。

### 5.2 Route & Filters 面板

来源：`retrieval_complete.cascade_trace` 中的 `query_plan` 和 `metadata_filter` 阶段。

展示内容：

- Route 和 route_reason。
- Filter Count，例如 `28 -> 20`。
- 降级徽章，例如 `metadata_filters_relaxed_to_all`。
- applied filters：company、doc_type、metric、year、chunk_type 等。

面试讲法：

> 如果 strict filter 候选不足，系统会自动放松约束并把原因展示出来。这个设计比静默返回 0 条结果更适合真实 RAG，因为金融语料 metadata 往往不完美。

### 5.3 Cascade 面板

来源：`retrieval_complete.cascade_trace` + `rerank_complete.cascade_trace`。

典型阶段：

```text
query_plan          1 -> 1
coarse_recall       1 -> N
metadata_filter     N -> M
hierarchy_drill_down N -> K
fusion              N -> 20
rerank              20 -> 5
final_evidence      5 -> 5 或 5 -> 3
```

面试讲法：

> Cascade 是这个系统的核心可观测性设计。面试官问“为什么答案这么来”时，我可以沿着每一层解释候选怎么变少、哪里发生降级、最后哪些 evidence 真正进入生成。

### 5.4 Iterative Steps 面板

来源：`retrieval_complete.iterative_trace.steps`。

展示内容：

- purpose
- 真实拼出来的 retrieval_query
- route
- selected_evidence_ids
- degraded / fallback_reason

面试讲法：

> 风险和原因类问题不是一次检索到底，而是拆成背景事实、驱动证据、交叉验证。现在是确定性规划，优点是可复现；生产化可以替换成 LLM planner。

### 5.5 Hierarchy & Drill-down 面板

来源：

- cascade 中 `name=hierarchy_drill_down` 的 stage。
- evidence metadata 中的 `chunk_level`、`parent_id`、`child_ids`、`section_title`、`section_path`。

面试讲法：

> 如果后端 payload 里有层级数据，前端会展示父级候选到子证据的扩展过程；如果旧语料还没 reindex，没有这些字段，前端会明确显示 unavailable，不会 mock 一棵假的层级树。

---

## 6. Demo 推荐流程

### 6.1 展示前准备

1. 确认 backend `.env` 使用 live provider。
2. 启动 backend 和 frontend。
3. 如果要展示 Phase 22 层级 metadata，确认当前 processed/index 是 Phase 22 后重新 import/reindex 的结果。
4. 准备 3 类问题：精确数字、风险分析、因果推理。

### 6.2 推荐问题

| 目的 | 问题 | 重点展示 |
| --- | --- | --- |
| 精确表格事实 | `英伟达2026年第三季度的总营收是多少？` | table_fact_first、citation、表格事实保留 |
| 风险分析 | `宁德时代近期有哪些潜在经营风险？` | risk_analysis、research_report_analysis、iterative retrieval |
| 因果推理 | `宏观消费变化如何影响贵州茅台盈利能力？` | causal_analysis、sub_queries、multi-step evidence |
| 层级下钻 | 选择能命中 section/table 父 chunk 的问题 | hierarchy_drill_down、section_path、parent/child metadata |

### 6.3 现场讲解顺序

1. 先问一个精确数字题，证明不是泛泛聊天，答案有 citation。
2. 点击 citation，展示证据和文档来源。
3. 看右侧 Query Plan，解释实体、指标、时间、策略。
4. 看 Route & Filters，解释为什么走某个 route，filter 有没有放松。
5. 看 Cascade，解释候选从召回到 rerank 到 evidence pack 的变化。
6. 再问一个风险/因果题，展示 Iterative Steps。
7. 如果语料已重建，展示 Hierarchy & Drill-down；如果没有，就主动说明需要 reimport/reindex，这是正确的数据边界，不是前端假展示。

---

## 7. 关键技术选型与替代方案

| 模块 | 当前选择 | 为什么适合当前项目 | 何时替换 |
| --- | --- | --- | --- |
| API | FastAPI + Pydantic | Python RAG 生态友好，SSE 和 schema 清晰 | 复杂业务后端或企业框架约束 |
| 前端 | React + TypeScript + Vite | 快速构建流式 demo，类型安全 | 需要 SSR/权限/生产级路由时 |
| PDF 抽取 | PyMuPDF / pymupdf4llm | 本地稳定，适合文本层 PDF | 扫描件多时加入 OCR |
| Raw 格式 | Markdown + frontmatter | 人可读、可审计、便于复跑 | 大规模生产可转对象存储 + DB |
| 关键词检索 | jieba + rank_bm25 | 中文公司名、指标、季度命中稳定 | 文档量大时换 Elasticsearch/OpenSearch |
| 向量检索 | JSON vector matrix + cosine | 小规模 demo 简单、可测、可审计 | 换 FAISS、pgvector、Milvus、Qdrant |
| Embedding/Rerank/Text | Bailian live + mock fallback | 现场真实调用，测试可离线 | 根据成本、延迟、合规切 OpenAI/DeepSeek/本地模型 |
| 融合 | RRF | 不依赖分数归一化 | 有评测集后可学习加权或 LTR |
| 证据压缩 | 规则 EvidencePack | 表格事实可无损保留，便宜可测 | 复杂摘要可加入 LLM compression |
| Agentic retrieval | 规则化 iterative steps | 可复现、可测试、适合面试演示 | 生产可升级 ReAct/LLM planner |

---

## 8. 工程亮点怎么说

### 8.1 可追溯

- PDF 到 Markdown 有 hash、manifest、page marker。
- chunk 继承 document metadata。
- answer 中 citation_id 映射到 rerank evidence。
- 前端 citation click 能回到证据。

### 8.2 可观测

- `/api/query` SSE 不只返回答案，还返回 plan、trace、iterative steps。
- `/api/debug/retrieval` 可以看更完整的检索过程。
- 前端把 query plan、route/filter、cascade、iterative、hierarchy 展示出来。

### 8.3 可降级

- provider 失败：mock/fallback。
- rerank 失败：回退 fused Top5，并标记 `degraded`。
- metadata filter 太窄：strict -> relaxed -> all。
- iterative retrieval 失败：回退 single-pass。
- hierarchy 无数据：显示 unavailable，不伪造。

### 8.4 向后兼容

- SSE 事件名不改，新增字段都是 optional。
- `RetrievalPlan`、`cascade_trace`、`iterative_trace` 都是增量字段。
- 老前端或老测试不会因为新字段缺失而崩。

### 8.5 可测试

- mock provider 保证无网可测。
- backend 已有针对 query analysis、routing/filter、hybrid retrieval、query API、debug retrieval、hierarchy import 等测试。
- v1.4 完成时 backend full suite 通过 116 个测试；Phase 21.1 frontend `npm run lint` 和 `npm run build` 通过。

---

## 9. 常见追问答法

| 追问 | 推荐回答 |
| --- | --- |
| 为什么不用 LangChain/LlamaIndex？ | 我想展示底层 RAG 工程能力，而不是把关键过程藏在框架里。这个项目每个阶段的输入输出都能讲清楚，也能在前端展示。后续如果接框架，也会放在明确边界后面。 |
| 为什么 query planning 不用 LLM？ | 演示和测试阶段需要确定性。规则化 plan 覆盖常见金融问答场景，低延迟、可复现。生产化可以把 planner 替换成 LLM，但 contract 不变。 |
| metadata filter 为什么不是向量库原生 pre-filter？ | 当前本地 JSON vector store 不支持 filter pushdown，所以实现是 post-recall filter，并在 trace 里标注 `applied_at=post_recall`。换 Qdrant/Milvus/pgvector 后可以把同一套 filters 下推。 |
| hierarchy_drill_down 显示 0 是不是 bug？ | 不一定。只有命中 section/table 父 chunk 时才会扩展子 evidence；如果查询直接命中 table_fact 或 text，0 child evidence 是正常结果。旧语料未 reindex 也可能没有 hierarchy metadata。 |
| iterative retrieval 和真正 Agent 有什么差距？ | 当前是 agentic retrieval baseline：固定规划 2-3 步，保证可复现。真正 Agent 会根据每步结果动态决定下一步，这是下一阶段可以替换的部分。 |
| 如何判断答案可信？ | 第一看 citation 是否存在，第二看右侧 evidence，第三看 cascade 是否有降级，第四可用 debug retrieval 看完整候选。生产化还需要 faithfulness 和 citation accuracy 评测。 |
| 为什么 vector store 不是 FAISS？ | 当前 corpus 小，本地 JSON matrix 更容易审计和测试。模块边界已经抽象好，后续替换 FAISS/pgvector/Milvus 不影响 query plan、route、trace、frontend 展示。 |
| 这和普通 RAG demo 最大区别是什么？ | 普通 demo 多数只展示最终答案；FinRAG 展示从 query understanding 到 route/filter/cascade/iterative/hierarchy/evidence pack 的中间过程，更像真实可 debug 的 RAG 系统。 |

---

## 10. 当前局限与下一步

面试时要主动、诚实地说这些边界：

1. **旧语料可能需要 reimport/reindex 才能完整展示 Phase 22 hierarchy**
   前端已经能展示 `parent_id`、`child_ids`、`section_path`，但不会伪造旧索引没有的数据。

2. **向量检索当前是 JSON matrix，不是生产级向量库**
   适合本地 demo；生产应换 FAISS、pgvector、Milvus 或 Qdrant，并把 metadata filter 下推。

3. **规则化 planner 不是完整 LLM agent**
   当前优先确定性和可测试；下一步可把 iterative planner 升级为 LLM-driven ReAct loop。

4. **评测体系还可加强**
   现在有 pytest contract/unit tests；生产还需要 golden set、Recall@K、MRR、citation accuracy、faithfulness、latency 监控。

5. **表格/OCR 能力仍可升级**
   当前适合文本层 PDF 和已有 table facts；扫描件 OCR、复杂跨页表格、图表理解仍是后续方向。

6. **前端是 demo-oriented，不是生产产品 UI**
   右侧面板故意信息密度高，为了展示工程能力；正式产品会隐藏部分中间态，只保留用户需要的解释和来源。

---

## 11. 关键文件清单

| 文件 | 角色 |
| --- | --- |
| `backend/app/models/schemas.py` | `RetrievalPlan`、cascade stage、iterative trace、hierarchy metadata schema |
| `backend/app/models/events.py` | SSE event schema，追加 plan/cascade/iterative 字段 |
| `backend/app/core/agent/query_ontology.py` | 金融实体/指标本体匹配 |
| `backend/app/core/agent/query_analysis.py` | query rewrite、intent、retrieval plan 构建 |
| `backend/app/core/retrieval/router.py` | route decision |
| `backend/app/core/retrieval/filters.py` | metadata filters 构建和松弛降级 |
| `backend/app/core/retrieval/hybrid.py` | BM25/vector/supplemental/RRF/hierarchy drill-down |
| `backend/app/core/retrieval/trace.py` | cascade trace 辅助 |
| `backend/app/core/agent/context_builder.py` | EvidencePack 证据压缩 |
| `backend/app/core/agent/retrieval_planner.py` | iterative retrieval 规则规划 |
| `backend/app/core/agent/workflow.py` | 查询主工作流和 SSE 组装 |
| `backend/app/core/ingestion/chunker.py` | section path 和 chunk 切分 |
| `backend/app/core/ingestion/corpus_importer.py` | parent/child hierarchy metadata 生成 |
| `backend/app/api/query.py` | `/api/query` SSE |
| `backend/app/api/debug.py` | `/api/debug/retrieval` 调试接口 |
| `frontend/src/api/finrag.ts` | 前端 SSE payload 类型 |
| `frontend/src/types.ts` | per-turn `RetrievalSnapshot` |
| `frontend/src/App.tsx` | 捕获 plan/cascade/iterative trace |
| `frontend/src/components/RagProcessInspector.tsx` | 右侧 RAG 过程展示组件 |
| `frontend/src/components/SidebarRight.tsx` | process inspector + BM25/Vector/Rerank evidence panels |

---

## 12. 数字和验证口径

可以这样讲：

- v1.4 backend 完成后，backend full suite 通过 **116 个测试**。
- Phase 21.1 frontend 完成后，`npm run lint` 和 `npm run build` 通过。
- 新增 `/api/query` 事件名为 **0 个**：仍复用既有 SSE 事件，通过 optional payload fields 向后兼容。
- 新增前端展示不引入 fake hierarchy：有真实后端字段才展示，没有就显示 unavailable。
- 当前项目是 interview/demo MVP，不宣称生产 SLA、生产级向量库或完整金融合规系统。

---

## 13. 最后总结话术

如果面试最后需要收束，可以这样说：

> 这个项目对我来说不是“做一个能回答问题的聊天页”，而是把 RAG 系统的关键工程问题拆开并落地：数据怎么可信地进来，查询怎么结构化，检索怎么路由和过滤，候选怎么融合和重排，证据怎么压缩并保留 citation，复杂问题怎么多步检索，层级文档怎么下钻，最终这些过程怎么通过 SSE 在前端展示出来。它现在仍是本地 demo，不是生产系统，但已经覆盖了真实 RAG 架构里最核心的可追溯、可观测、可降级和可测试能力。

