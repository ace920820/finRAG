# FinRAG 面试讲解指南

> 适用对象：Jamie 面试前快速理解、复盘和背诵。  
> 项目路径：`/Volumes/KINGSTON/projects/finRAG`  
> 文档定位：这不是 README，而是一份“面试怎么讲”的讲稿 + 追问答法。  
> 重要原则：下面会明确区分 **已实现**、**设计意图**、**下一步优化**，不要把当前 mock provider 或待完善能力说成生产级能力。

---

## 0. 项目一句话定位

**FinRAG 是一个面向金融研究场景的本地 RAG 面试展示项目：它把公开金融 PDF 文档转换成 Markdown，切分成 chunks 并建立 BM25 + 向量索引，查询时通过 query rewrite、混合检索、rerank、带引用生成和前端 SSE 可视化，展示一个可追溯、可观测、可替换模型 provider 的端到端金融问答闭环。**

如果面试只能讲 20 秒，可以说：

> 我做的是一个金融研究场景的 RAG Agent demo，不是普通聊天机器人。核心价值是把财报、研报等 PDF 文档经过可重复的数据管线入库，然后查询时同时展示 BM25、向量召回、Rerank Top5、最终带引用的 Markdown 答案。它重点展示的是 RAG 系统工程能力：数据治理、检索链路、provider 抽象、SSE 流式输出、引用追溯和前后端联调，而不是只调一个大模型 API。

---

## 1. 面试 1-2 分钟开场讲法

可以按下面这段背：

> FinRAG 是我为了展示金融 RAG 工程能力做的一个本地 MVP。它的用户假设是金融研究员或投顾分析师，典型问题包括“某家公司收入是多少”“近期经营风险是什么”“AI 算力链条对上下游公司业绩有什么影响”。  
> 
> 我没有把它做成一个只会聊天的 demo，而是按真实 RAG 系统的链路拆成三层：第一层是数据管线，从公开 PDF 文档开始，用 `pdf2md --profile finrag` 把 PDF 转成带 frontmatter 和 page marker 的 Markdown，再由 backend importer 统一成 `documents.json` 和 `chunks.json`，然后构建 BM25 和 vector index；第二层是查询链路，FastAPI 接到问题后先做 query rewrite 和意图识别，然后 BM25 与向量召回并行，RRF 融合后送 rerank，最后基于 Top5 evidence 生成带 citation 的 Markdown 答案；第三层是展示层，React 前端通过 SSE 逐阶段接收 `query_rewrite`、`retrieval_complete`、`rerank_complete`、`answer_chunk`、`done` 等事件，让面试官能看到系统不是黑盒，而是每一步检索证据都可视化。  
> 
> 这个项目里我特别强调三个取舍：第一，金融问答必须可追溯，所以答案后面要有 citation，右侧能看到对应证据；第二，面试 demo 要稳定，所以默认 provider 是 mock，但 embedding、rerank、text 都抽象成 provider，后续可以切到阿里百炼/Qwen 等真实服务；第三，先做端到端闭环，再逐步提升语义检索质量、metadata 质量、评测和生产化能力。当前我会明确说明 mock embedding 不是生产级语义检索，它主要用于离线可重复测试和 demo 稳定性。

---

## 2. 系统整体架构

### 2.1 当前实现视角

```text
公开 PDF 文档
  data/docs/source_documents/**/*.pdf
        │
        ▼
pdf2md --profile finrag
        │  输出带 frontmatter、页码 marker、hash、manifest 的 raw Markdown
        ▼
backend/app/data/raw/
  extracted/<collection-name>/*.md
  _meta/*-manifest.{md,json}
        │
        ▼
backend/scripts/import_corpus.py
        │  统一 Document / Chunk schema，确定 doc_id / chunk_id / metadata
        ▼
backend/app/data/processed/
  documents.json
  chunks.json
        │
        ▼
backend/scripts/build_index.py
        │  构建 BM25 index + vector index
        ▼
backend/app/data/index/
  bm25_index.json
  vector_index.json
        │
        ▼
FastAPI backend
  GET  /api/documents
  POST /api/preview-rewrite
  POST /api/query   text/event-stream
        │
        ▼
React / Vite frontend
  左侧文档库 + 示例问题
  中间答案流 + citation
  右侧 BM25 / Vector / Rerank 可视化
```

### 2.2 查询链路架构

```text
用户问题
  │
  ▼
Query Analysis
  - alias / keyword expansion
  - sub-query construction
  - intent classification: factual / analytical / reasoning
  │
  ▼
Hybrid Retrieval
  ├─ BM25Store: jieba + rank_bm25
  ├─ VectorStore: embedding + cosine similarity
  ├─ supplemental/entity/topic boost
  └─ RRF fusion: fused_top20
  │
  ▼
RerankService
  - provider rerank candidates
  - fallback to fused Top5 on provider failure
  - assign citation_id = 1..5
  │
  ▼
AnswerGenerator
  - build_generation_prompt
  - provider generate_text
  - fallback mock answer
  - citation span: <span class="cite" data-id="1">[1]</span>
  │
  ▼
SSE stream to frontend
  query_rewrite → intent_detected → retrieval_complete → rerank_complete
  → ping → answer_chunk(s) → done / error
```

---

## 3. 核心数据流：PDF → Markdown → chunks → index → retrieval → rerank → answer → frontend SSE

### 3.1 PDF → Markdown

**相关模块：**

- `pdf2md/README.md`
- `pdf2md/src/elite_daily_pdf_to_md/finrag.py`
- `backend/app/data/raw/`

**已实现：**

- `pdf2md` 原本是 Elite Daily PDF 转 Markdown 工具，后续增加了 `--profile finrag`。
- FinRAG 模式会把金融 PDF 转到 FinRAG 自己的 raw 目录，而不是 Obsidian vault：

```bash
cd pdf2md
python3 -m elite_daily_pdf_to_md.cli \
  --profile finrag \
  --source-dir "/path/to/source-pdfs" \
  --raw-root "/Volumes/KINGSTON/projects/finRAG/backend/app/data/raw" \
  --collection-name "research-reports" \
  --extractor pymupdf
```

**关键设计点：**

- 输出 Markdown 不只是正文，还包含 frontmatter：`domain`、`collection`、源 PDF 路径/名称、title、extractor、page count、char count、`pdf_sha256`、`content_hash`、`text_sha256` 等。
- 正文保留 `<!-- page: 1 -->` 这种页码 marker，后续 chunk 可以继承页码，便于引用追溯。
- 会生成 manifest，记录成功、跳过、失败，方便审计和复跑。
- 不做 OCR：当前假设 PDF 有文本层；扫描件 OCR 是下一步能力，不在当前 MVP。

### 3.2 Markdown → documents.json / chunks.json

**相关模块：**

- `backend/scripts/import_corpus.py`
- `backend/app/core/ingestion/raw_loader.py`
- `backend/app/core/ingestion/corpus_importer.py`
- `backend/app/core/ingestion/chunker.py`
- `backend/app/models/schemas.py`

**已实现：**

```bash
cd backend
python3 scripts/import_corpus.py \
  --raw-root app/data/raw \
  --collection-name research-reports \
  --processed-dir app/data/processed
```

或者导入后直接重建索引：

```bash
cd backend
python3 scripts/import_corpus.py \
  --raw-root app/data/raw \
  --collection-name research-reports \
  --processed-dir app/data/processed \
  --index-dir app/data/index \
  --rebuild-index
```

**当前数据状态：**

- `backend/app/data/processed/documents.json`：40 篇文档。
- `backend/app/data/processed/chunks.json`：9303 个 chunk。
- 公司覆盖：宁德时代、贵州茅台、NVIDIA、台积电，各 10 篇。
- 文档类型：主要是 financial_report，少量 research_report。
- PDF 来源整理记录见：`docs/agents-work-docs/finrag_demo_public_data_sourcing_2026-05-13.md`。

**chunking 设计：**

- 默认目标长度约 900 字符。
- 按段落和页码 marker 切分。
- 长段落会按句子边界拆，再不行 hard wrap。
- 每个 chunk 有：
  - `chunk_id`
  - `doc_id`
  - `section`
  - `page_num`
  - `chunk_index`
  - `content`
  - `metadata`

### 3.3 chunks → index

**相关模块：**

- `backend/scripts/build_index.py`
- `backend/app/core/retrieval/index_store.py`
- `backend/app/core/retrieval/bm25_store.py`
- `backend/app/core/retrieval/vector_store.py`
- `backend/app/core/providers/embeddings.py`

**已实现：**

```bash
cd backend
python3 scripts/build_index.py \
  --processed-dir app/data/processed \
  --index-dir app/data/index
```

输出：

```text
backend/app/data/index/
  bm25_index.json
  vector_index.json
```

**BM25 index：**

- 使用 `jieba` 分词。
- 使用 `rank_bm25.BM25Okapi`。
- 优点：对公司名、股票代码、指标名、季度、财务科目等精确词很友好。

**Vector index：**

- 当前实现是本地 JSON 向量矩阵 + cosine similarity，不是 FAISS 文件索引。
- provider 抽象支持 mock 和 Bailian。
- 默认 `MockEmbeddingProvider` 是 sha256 deterministic embedding，维度 8。
- 面试中必须诚实说明：**当前默认向量检索主要用于离线可重复和展示链路，不等价于生产级语义检索**。

> 注意：早期需求文档设想了 FAISS + BGE-M3；当前代码实现先采用轻量 JSON vector store + provider abstraction。面试时可以说“需求设计上预留了 FAISS/BGE-M3，当前 MVP 为了本地稳定和测试可重复，先用轻量实现跑通闭环”。

### 3.4 retrieval：BM25 + Vector + RRF

**相关模块：**

- `backend/app/core/retrieval/hybrid.py`
- `backend/tests/test_hybrid_retrieval.py`

**已实现：**

查询时：

1. `BM25Store.search(query, top_k=20)`
2. `VectorStore.search(query, top_k=20)`
3. `_supplemental_hits()`：针对实体 + 主题词做补充召回。
4. `_rrf_fuse()`：使用 RRF（Reciprocal Rank Fusion）融合。
5. 返回三个数组：
   - `bm25_results`
   - `vector_results`
   - `fused_top20`

**为什么要混合检索：**

- 金融问题里经常有精确实体：公司名、股票代码、报表科目、日期、季度。BM25 能稳定命中这些词。
- 用户也会问抽象问题：经营风险、AI 算力链条、宏观影响。向量检索适合语义泛化。
- RRF 不要求两个通道分数同尺度，按排名融合，工程上更稳。
- 前端同时展示 BM25、Vector、Rerank，有利于面试官理解系统不是“黑盒回答”。

### 3.5 rerank：Top20 → Top5 evidence

**相关模块：**

- `backend/app/core/retrieval/rerank_service.py`
- `backend/app/core/providers/rerank.py`
- `backend/tests/test_rerank_service.py`

**已实现：**

- `RerankService.rerank(query, candidates)` 将 fused candidates 送给 rerank provider。
- 默认 `MockRerankProvider` 用 query/document 字符重叠 + hash 稳定分数。
- 支持 `BailianRerankProvider`，但需要环境变量和真实 API。
- 如果 rerank provider 失败，会 fallback 到 fused Top5，并设置 `degraded=True`。
- Top5 evidence 会分配 `citation_id` 1-5。

**当前限制：**

- 当前 rerank provider 接收到的是 `candidate.preview`，而 preview 在 `BM25Store` / `VectorStore` 中默认只有 `chunk.content[:120]`。
- `RerankResultItem.content` 当前也来自 `candidate.preview`，所以前端展示的 evidence 可能是 120 字摘要，而不是完整 chunk。
- 面试时可说：“MVP 已经有 rerank 抽象和 Top5 引用链路，但下一步会把 rerank 输入从 preview 改成完整 chunk content，同时前端展示完整证据文本。”

### 3.6 answer generation：基于 evidence 的引用式回答

**相关模块：**

- `backend/app/core/agent/prompts.py`
- `backend/app/core/agent/generator.py`
- `backend/app/core/providers/text.py`（实现代码实际位于 provider 文件中）
- `backend/app/core/agent/workflow.py`

**已实现：**

- Prompt 明确要求：只依据给定资料回答；资料没有则说“资料中未提及”；输出 Markdown；关键结论后加 citation。
- `AnswerGenerator` 调用 text provider。
- provider 失败或返回空时，会回退到 `build_mock_answer()`。
- citation 用前端可点击的 HTML span：

```html
<span class="cite" data-id="1">[1]</span>
```

**需要诚实说明：**

- 默认 text provider 是 mock，不是每次真实调用 Qwen/DeepSeek/OpenAI。
- mock answer 主要用于 demo 稳定性和测试可重复。
- 真正生产场景要加：更严格的引用校验、答案事实一致性评测、敏感/合规策略、模型输出 guardrail。

### 3.7 frontend SSE 展示

**相关模块：**

- `backend/app/api/query.py`
- `backend/app/core/sse.py`
- `frontend/src/api/finrag.ts`
- `frontend/src/App.tsx`
- `frontend/src/components/ChatArea.tsx`
- `frontend/src/components/SidebarLeft.tsx`
- `frontend/src/components/SidebarRight.tsx`

**已实现：**

`POST /api/query` 返回 `text/event-stream`，事件顺序大致是：

```text
query_rewrite
intent_detected
retrieval_complete
rerank_complete
ping
answer_chunk ...
done
```

前端通过 fetch stream 自己解析 SSE frame，而不是 `EventSource`，因为查询是 POST 且要发送 JSON body。

前端展示：

- 左栏：示例问题、文档库。
- 中间：用户问题、阶段进度、Markdown 答案、citation click。
- 右栏：BM25 / Vector / Rerank 结果。

**当前限制：**

- `ChatArea` 中耗时、准确度 `98%`、来源引用 `5个文档` 等仍有展示型硬编码成分，不应在面试中说成真实评测指标。
- 当前 `SidebarRight` 用单一 `openPanel`，BM25/Vector/Rerank 不是完全独立折叠，也不能 all-collapsed；这正是 v1.2 roadmap 里的优化项。
- `Message` 类型里有 `retrievalSnapshot`，但 `App.tsx` 当前没有真正把每轮检索结果写入每条 assistant message，因此多轮会话证据仍是全局状态，旧答案 citation 可能受最新查询影响；这是 v1.2 的 per-turn traceability 目标。

---

## 4. 为什么这么设计

### 4.1 为什么是金融 RAG，而不是通用聊天

金融问答的核心风险是“看起来合理但没有依据”。尤其涉及营收、同比、风险、行业判断时，面试官会关注：

- 数据从哪里来？
- 引用能否追溯到文档和页码？
- 模型是否编造？
- 如果资料没有，系统是否拒答？
- 如果 provider 挂了，demo 是否还能跑？

所以 FinRAG 的设计重点不是“回答得像人”，而是：

1. **资料入库可追溯**：PDF → Markdown → document/chunk → index，每一步有 hash / manifest / metadata。
2. **检索过程可解释**：前端展示 BM25、Vector、Rerank。
3. **答案可引用**：citation_id 映射到 rerank evidence。
4. **provider 可替换**：mock、Bailian、未来 OpenAI/DeepSeek 都可以放在 provider 层。
5. **demo 稳定优先**：默认 mock provider，避免面试现场被网络、rate limit、API key 拖垮。

### 4.2 为什么先做闭环，再做效果优化

面试项目最容易犯的错是：一开始就追求“最强模型、最大向量库、最复杂 Agent”，结果端到端跑不通。

这个项目的工程取舍是：

- 先确定 API contract：`GET /api/documents`、`POST /api/query`、`POST /api/preview-rewrite`。
- 先让数据能从 PDF 进入统一 schema。
- 先让前端能看到 query lifecycle。
- 再逐步替换真实 embedding/rerank/LLM，提升检索质量。

面试时可以这么说：

> 我把这个项目当成一个可迭代的 RAG 产品来做。MVP 阶段先保证“数据能进来、检索能发生、证据能展示、答案能引用、前端能流式渲染”。这样每一层都可测试、可替换。真实语义 embedding、FAISS/Milvus、评测集、生产监控属于下一阶段增强，而不是一开始就堆进去。

### 4.3 为什么要 mock/real provider 双轨

**mock provider 的价值：**

- 测试不依赖外网。
- 不依赖 API key。
- 不受 rate limit 影响。
- 输出稳定，便于回归测试和面试演示。

**real provider 的价值：**

- 真实 embedding 提供语义召回能力。
- 真实 rerank 提升 Top5 evidence 相关性。
- 真实 LLM 提高回答质量。

**正确表述：**

> 当前默认 mock provider 不是为了假装效果好，而是为了让工程链路稳定可测；provider 抽象的意义是后续可以在不改 workflow 的情况下切到 Bailian/Qwen 等真实模型。面试时我会明确说明当前 mock embedding 的局限，不把它说成生产级语义检索。

---

## 5. 模块拆解

### 5.1 `pdf2md/`：PDF 到 raw Markdown

职责：

- 发现 PDF。
- 忽略 `._*.pdf` 等 macOS 资源文件。
- 用 PyMuPDF / pymupdf4llm 提取文本。
- 保留页码 marker。
- 输出 Markdown + manifest。
- FinRAG 模式写入 `backend/app/data/raw/`。

面试讲点：

> 我没有把 PDF 解析直接塞进在线查询链路，而是做成离线 ingestion。这样查询延迟稳定，而且 PDF 解析失败、hash、manifest 都可以被审计。金融文档尤其是 PDF 表格很复杂，所以离线处理更适合做质量控制。

### 5.2 `backend/`：RAG 主链路

职责：

- FastAPI API：`/api/documents`、`/api/query`、`/api/preview-rewrite`。
- ingestion：raw Markdown → Document / Chunk。
- retrieval：BM25、Vector、RRF。
- rerank：provider + fallback。
- agent：query rewrite、intent、prompt、generation。
- SSE：事件格式化与流式输出。
- tests：schema、retrieval、rerank、query API、import pipeline、provider config。

面试讲点：

> 后端的核心不是一个大函数，而是按 RAG 生命周期拆模块。每个模块有清晰输入输出，所以可以单测：query analysis 测 expanded terms，retrieval 测三阶段结果，rerank 测 Top5 和 fallback，query API 测 SSE 事件顺序。

### 5.3 `frontend/`：面试展示 UI

职责：

- 左栏：示例问题 + 文档库。
- 中间：会话流、阶段进度、Markdown 答案、citation badge。
- 右栏：BM25、Vector、Rerank 可视化。
- API adapter：把 backend 英文字段映射成中文 UI 类型。
- fetch stream：解析 POST SSE。

面试讲点：

> 前端不是只展示答案，而是把 RAG 的内部过程外显出来。面试时我可以边问问题边指右侧：这些是关键词召回，这些是向量召回，这些是 rerank 后真正喂给模型的 evidence。这样更能展示工程透明性和可 debug 能力。

### 5.4 `data/`：公开 demo 数据与 manifest

职责：

- `data/docs/source_documents/**/*.pdf`：40 个公开 PDF。
- `data/manifest/*.json/csv`：来源、失败记录、非 PDF 清理记录。
- 覆盖：宁德时代、贵州茅台、NVIDIA、台积电。

面试讲点：

> 我选公开合法来源的 PDF，而不是爬付费数据库或绕过验证码。这样面试展示更合规，也可以解释数据 provenance。

### 5.5 `docs/`：项目说明和面试材料

职责：

- 数据来源说明。
- 本面试讲解指南。
- 后续可补充评测报告、demo checklist、架构图。

---

## 6. 关键技术选型与替代方案比较

| 模块 | 当前选择 | 为什么适合 MVP | 替代方案 | 何时替换 |
|---|---|---|---|---|
| API | FastAPI | Python RAG 生态友好，SSE 简单，Pydantic schema 清晰 | Flask、Django、Node.js | 需要更复杂业务后端或已有技术栈约束时 |
| 前端 | React + TypeScript + Vite | 快速搭 demo，类型安全，流式 UI 好实现 | Next.js、Vue | 需要 SSR、权限系统或更完整产品化时 |
| PDF 抽取 | PyMuPDF / pymupdf4llm | 本地、稳定、适合文本层 PDF | pdfplumber、Unstructured、OCR | 表格质量要求更高或扫描件很多时 |
| Raw 格式 | Markdown + frontmatter | 人可读、可审计、可复跑、便于 manifest | 直接 JSON、数据库 | 大规模生产管线可转对象存储 + DB |
| Chunking | 约 900 字符，按段落/页码 | 简单稳定，能保留页码 | semantic chunking、section-aware chunking、table-aware chunking | 需要更高事实精度和表格问答时 |
| 关键词检索 | jieba + rank_bm25 | 中文词项、股票代码、财务科目命中稳定 | Elasticsearch/OpenSearch | 文档量大、需要复杂 filter/highlight 时 |
| 向量检索 | JSON vector store + cosine | 本地 demo 简单、可测 | FAISS、Milvus、pgvector、Pinecone | 文档量大或需要真实 ANN 性能时 |
| Embedding | Mock / Bailian provider | 默认离线稳定，真实 provider 可切换 | BGE-M3、本地模型、OpenAI embedding | 需要真实语义检索效果时 |
| 融合 | RRF | 不依赖分数归一化，工程稳 | 加权融合、Learning-to-rank | 有评测集可学习权重时 |
| Rerank | Mock / Bailian provider | Top5 证据质量可升级，失败可降级 | bge-reranker、Cohere Rerank、本地 cross-encoder | 对证据相关性要求更高时 |
| 生成 | Mock / Qwen-compatible provider | demo 稳定，真实模型可替换 | DeepSeek、OpenAI、Claude | 根据成本、延迟、合规选择 |
| 流式 | POST + text/event-stream | 查询要发 JSON，前端 fetch stream 可解析 | WebSocket、轮询 | 双向实时交互/多 agent 时用 WebSocket |
| 测试 | pytest + TestClient | API contract 和 retrieval 可回归 | Playwright、load test | 前端 E2E/性能压测阶段 |

---

## 7. 面试中应该重点展示哪些能力

### 7.1 RAG 工程能力

重点说：

- RAG 不是 prompt 工程，而是数据、检索、排序、生成、引用、评测的完整系统。
- 这个项目覆盖了：ingestion、chunking、indexing、hybrid retrieval、rerank、citation、SSE。

### 7.2 数据治理能力

重点说：

- PDF 先离线转换为 raw Markdown。
- 每个 raw 文件有 frontmatter 和 hash。
- import pipeline 生成统一 schema。
- chunk 继承 doc metadata，便于 filter、引用、审计。

### 7.3 检索可解释能力

重点说：

- 前端右栏能分开看 BM25、Vector、Rerank。
- 这对 debug 很重要：如果答案错，可以看是召回错、rerank 错还是生成错。

### 7.4 Provider 抽象和降级能力

重点说：

- embedding、rerank、text 都通过 provider 构建。
- 默认 mock 保证测试和面试稳定。
- rerank 失败 fallback 到 fused Top5。
- 真实 provider 通过 env 切换。

### 7.5 API contract 和前后端联调能力

重点说：

- 后端 SSE 事件模型明确。
- 前端 adapter 处理 backend → UI 的类型映射。
- API 不只是最终答案，还包含中间过程。

### 7.6 诚实表达局限的能力

面试官往往喜欢候选人能说清楚：

- 当前 demo 哪里是 mock。
- 哪些地方是 MVP 简化。
- 如果进生产，下一步怎么做。

---

## 8. 当前局限与改进路线

### 8.1 当前局限

1. **默认 mock embedding 不是生产级语义检索**  
   `MockEmbeddingProvider` 用 hash 生成 8 维向量，只保证 deterministic，不保证语义相似度。

2. **provider 一致性需要进一步梳理**  
   当前 index build 可用真实 embedding provider，但 `VectorStore.search()` 默认 query embedding 仍可能走 `MockEmbeddingProvider`。如果生产化，需要确保 build/search 使用同一 embedding provider、同一模型、同一维度和同一归一化策略。

3. **vector store 当前是 JSON 矩阵，不是 FAISS**  
   适合小规模 demo，但不是高性能向量数据库。

4. **rerank 输入和 evidence 展示目前偏短**  
   Rerank 当前主要基于 `preview`，而 preview 约 120 字；下一步应改成完整 chunk 或更合理的 passage。

5. **metadata 质量还有提升空间**  
   40 个 PDF 的公司、类型、日期可以用 manifest 补强，但标题规范、period、source_url、license/access_note 等还可进一步入 chunk metadata。

6. **TSMC / 台积电实体扩展不完整**  
   importer 能识别 `tsmc`，数据里有台积电；但 `query_analysis.py` 的 alias expansion 主要覆盖贵州茅台、宁德时代、NVIDIA，对台积电/TSMC 的 query rewrite 还需要补。

7. **引用校验还不够严格**  
   当前 done event 有 citation map，答案也有 citation span；但生产场景还应做 post-check：答案中的 citation 是否都存在、每个关键结论是否有 evidence 支撑。

8. **前端部分指标仍是展示占位**  
   如总耗时显示、准确度 98%、来源引用 5 个文档等，不应作为真实观测指标对外宣称。

9. **多轮会话 per-turn evidence 尚未完全落地**  
   `RetrievalSnapshot` 类型已存在，但 App 当前仍以全局 BM25/Vector/Rerank state 为主；旧答案的 evidence 可能被新查询覆盖。

10. **折叠交互与 v1.2 要求仍有差距**  
   右侧 retrieval panel 当前更像单开 accordion，不是独立折叠/all collapsed。

11. **评测体系还比较基础**  
   目前有 pytest contract/unit tests，但缺少一套金融问答 golden set、检索 Recall@K、citation accuracy、faithfulness 指标。

12. **PDF 表格抽取还不是强项**  
   当前以文本层提取为主。财报表格要做精准数值问答，未来应加入 table-aware extraction 或结构化表格解析。

### 8.2 改进路线

#### P0：让面试 demo 更可信

- 修复/标注前端硬编码指标，显示真实 `done.latency_ms` 和 citation count。
- Rerank Top5 展示完整 evidence，不只展示 preview。
- 将 `TSMC/台积电` 加入 query rewrite alias。
- 明确当前 provider 状态，在 UI 或 README 标注 mock/real mode。

#### P1：提升真实检索效果

- 统一 embedding provider：build index 和 query search 使用同一 provider。
- 切换真实 embedding（如 BGE-M3 或 Bailian text-embedding-v4）。
- 使用 FAISS/pgvector/Milvus 替代 JSON vector store。
- 引入 metadata filter：company、doc_type、date、period、source。

#### P2：提升金融问答质量

- 表格抽取：pdfplumber / camelot / layout parser / LLM table normalization。
- 建立 benchmark：事实题、风险题、推理题、拒答题、citation 题。
- 对答案做 faithfulness/citation post-check。
- 支持“资料中未提及”的严格拒答策略。

#### P3：生产化

- OpenTelemetry / Langfuse tracing。
- request_id 贯穿 query、retrieval、rerank、generation。
- 缓存 embedding、rerank、LLM 响应。
- 限流、超时、重试、熔断。
- 权限、PII/合规、安全审计。
- Docker 部署和灰度回滚。

---

## 9. 如果面试官追问 bug / 不足，怎么回答

### 9.1 被问：“你这个向量检索是不是假的？”

推荐回答：

> 当前默认配置确实是 mock embedding，我不会把它说成生产级语义检索。这样做的原因是面试 demo 和单元测试必须离线可重复，不依赖 API key、网络和 rate limit。工程上我已经把 embedding provider 抽象出来，`Settings` 支持 `embedding_provider=bailian`，后续切真实 embedding 不需要改 workflow 主链路。生产化时我会确保 index build 和 query search 使用同一个 embedding 模型，并替换成 FAISS/pgvector/Milvus 这类真正的向量检索后端。

### 9.2 被问：“当前结果不准怎么办？”

推荐回答：

> 我会先定位是哪一层问题。RAG 的好处是可以拆开 debug：看 BM25 有没有召回关键词证据，看 vector 有没有召回语义相关证据，看 RRF 后候选是否合理，看 rerank Top5 是否把正确证据排上来，最后再看 LLM 有没有忠实引用。如果召回层没命中，是 chunking/metadata/embedding 的问题；如果 Top20 有但 Top5 没有，是 rerank 问题；如果 evidence 对但答案错，是 generation/prompt/faithfulness 问题。这个项目右侧可视化就是为了支持这种定位。

### 9.3 被问：“为什么不用 LangChain / LlamaIndex？”

推荐回答：

> 这个项目面试重点是展示我理解 RAG 底层链路，所以我选择轻量自研，把 query rewrite、retrieval、fusion、rerank、generation、SSE 都显式拆出来。LangChain/LlamaIndex 很适合快速搭建复杂应用，但在面试场景中，我更希望能解释每一步的输入输出和失败降级。当然如果团队已有 LangChain/LlamaIndex 基础，我可以把这些模块封装成对应 retriever / node parser / reranker 组件。

### 9.4 被问：“为什么不用真正的数据库？”

推荐回答：

> 当前是本地 demo，40 篇 PDF、9303 chunks，用 JSON 文件足够让链路跑通且易审计。生产环境我会把 documents/chunks metadata 放到 Postgres，向量放 pgvector/Milvus/FAISS，原文和 raw Markdown 放对象存储。MVP 先用文件系统是为了降低部署复杂度，不是因为不知道数据库方案。

### 9.5 被问：“你怎么避免模型编造金融结论？”

推荐回答：

> 第一，prompt 明确要求只依据给定资料回答，资料没有就说“资料中未提及”。第二，答案必须带 citation，citation map 来自 rerank Top5。第三，下一步会增加 post-check，验证答案中每个 citation 是否存在、关键数字是否能在 evidence 中找到。生产环境还要加拒答策略、敏感投资建议边界和人工审核。

---

## 10. 高频面试问题与推荐回答（至少 20 个）

### Q1：这个项目解决什么问题？

**答：** 解决金融研究中“从大量财报/研报里快速找到依据并生成可引用分析”的问题。它不是通用聊天机器人，而是一个以文档证据为中心的 RAG 系统，强调可追溯、可观测和可替换 provider。

### Q2：为什么金融场景适合 RAG？

**答：** 金融问题知识密集、时效性强、数字敏感，纯 LLM 容易过时或编造。RAG 可以把回答限定在本地可控资料里，并通过 citation 追溯来源，更适合财报、研报、公告、新闻等场景。

### Q3：数据是怎么进入系统的？

**答：** 公开 PDF 先通过 `pdf2md --profile finrag` 转成 raw Markdown，保留 frontmatter、hash、page marker 和 manifest；再由 `import_corpus.py` 统一成 `documents.json` 和 `chunks.json`；最后 `build_index.py` 构建 BM25 和 vector index。

### Q4：为什么 PDF 不在查询时实时解析？

**答：** PDF 解析慢且不稳定，尤其金融 PDF 有表格、页眉页脚、扫描件等问题。离线 ingestion 可以复跑、记录失败、做质量检查，也能保证在线查询延迟稳定。

### Q5：chunking 怎么做？

**答：** 当前按段落和页码 marker 切分，目标长度约 900 字符，长段落按句子边界或 hard wrap 拆分。每个 chunk 继承文档 metadata 和 page number，便于检索和引用。未来会做 section-aware 和 table-aware chunking。

### Q6：为什么要 BM25 + 向量混合检索？

**答：** BM25 对公司名、股票代码、财务指标、季度等精确词很稳；向量检索适合“经营风险”“行业影响”这类语义表达。金融问答两类需求都有，所以用 hybrid retrieval 比单一路径更稳。

### Q7：RRF 是什么，为什么用它？

**答：** RRF 是 Reciprocal Rank Fusion，按排名而不是原始分数融合多个检索通道。因为 BM25 分数和向量相似度不在同一尺度，直接加权容易不稳定；RRF 工程上简单、鲁棒，适合 MVP。

### Q8：当前向量检索用的是什么？

**答：** 当前默认是 mock embedding，sha256 生成 deterministic vector，主要用于离线测试和 demo 稳定。代码预留了 Bailian embedding provider。生产化会换成真实 embedding，比如 BGE-M3/Bailian text-embedding-v4，并确保建库和查询用同一模型。

### Q9：为什么需要 rerank？

**答：** 初召回 Top20 通常有噪声，rerank 用更强的相关性模型从候选中选 Top5 evidence，减少无关 chunk 进入 prompt，提高答案质量和 citation 质量。

### Q10：rerank 失败怎么办？

**答：** `RerankService` 有 fallback。如果 provider 抛错，就退回 fused Top5，并记录 degraded/fallback_reason。这保证 demo 和服务不会因为 rerank API 挂掉而完全不可用。

### Q11：citation 怎么生成？

**答：** rerank Top5 分配 `citation_id` 1-5，生成阶段要求在关键结论后插入 `<span class="cite" data-id="1">[1]</span>`。done event 里返回 citation map，前端点击 citation 时可以高亮右侧对应 evidence。

### Q12：如何避免 citation drift？

**答：** 当前 citation map 来自 rerank Top5，答案中的 citation id 应该对应这些 evidence。下一步会做 post-check，检查答案中的 citation 是否都存在、引用结论是否能在 chunk 中找到，并做 per-turn snapshot 防止多轮覆盖。

### Q13：为什么使用 SSE？

**答：** RAG 查询天然有阶段：rewrite、retrieval、rerank、generation。SSE 适合服务端单向持续推送，前端可以实时展示每个阶段和 answer chunks。相比 WebSocket，SSE 更简单；相比普通 HTTP，用户体验更好。

### Q14：为什么前端用 fetch stream 而不是 EventSource？

**答：** `EventSource` 原生主要支持 GET，但查询接口需要 POST JSON body。前端用 fetch + ReadableStream 自己解析 SSE frame，既能保持 POST，又能流式处理。

### Q15：前后端 API contract 是什么？

**答：** 主要是三个接口：`GET /api/documents` 返回文档库；`POST /api/preview-rewrite` 返回输入预览关键词；`POST /api/query` 返回 SSE。SSE 事件包括 `query_rewrite`、`intent_detected`、`retrieval_complete`、`rerank_complete`、`answer_chunk`、`done`、`error`、`ping`。

### Q16：金融 PDF 表格怎么处理？

**答：** 当前主要是文本层抽取和段落 chunking，对复杂表格不是强保证。MVP 先保证端到端闭环。生产化会引入 table-aware extraction，例如 pdfplumber/Camelot/布局模型，或把关键财务表结构化成 JSON/SQL，再与文本 RAG 结合。

### Q17：metadata 在系统里有什么用？

**答：** metadata 用于文档列表展示、检索结果标题/公司/日期/页码、citation map、未来 filter 和评测。金融场景里 company、ticker、doc_type、period、publish_date、source_url 很重要，否则容易检索到错误公司或错误时期的文档。

### Q18：如何做评测？

**答：** 当前已有 pytest 验证 schema、检索、rerank、SSE 事件和导入管线。下一步要建金融 QA golden set，覆盖事实题、风险题、推理题、拒答题，指标包括 Recall@K、MRR、rerank hit rate、citation accuracy、faithfulness、latency 和 cost。

### Q19：如何优化性能？

**答：** 离线预构建索引，在线只做 query embedding、BM25 search、vector search、rerank、generation。下一步可加 embedding/query cache、FAISS/ANN、异步 provider 调用、rerank batch、LLM streaming、超时和熔断。

### Q20：如何控制成本？

**答：** 首先离线 embedding，避免重复计算；其次限制 TopK 和 prompt evidence 数量；第三缓存常见 query/rerank；第四根据问题类型选择模型，小问题用低成本模型，复杂分析用强模型；第五 provider 可替换，方便按成本和质量切换。

### Q21：如何处理安全和 prompt injection？

**答：** 检索文档和用户输入都视为不可信。系统 prompt 不能被文档覆盖。生产化要加 prompt injection 检测、文档内容隔离、敏感信息脱敏、工具调用 allowlist、日志最小化。目前项目主要是本地 demo，安全策略是下一步生产化重点。

### Q22：如何处理合规和投资建议风险？

**答：** 回答应定位为资料整理和研究辅助，不构成投资建议。对没有资料支撑的结论拒答或标注不确定性。生产环境需要合规提示、敏感问题策略、引用来源留存、审计日志和人工审核流程。

### Q23：为什么前端要显示检索过程？

**答：** 因为 RAG 系统最怕黑盒。显示 BM25、Vector、Rerank 可以让面试官看到答案来自哪里，也方便 debug。如果答案错，可以判断是召回问题、排序问题还是生成问题。

### Q24：如果数据量从 40 篇变成 10 万篇怎么办？

**答：** 文件 JSON 方案要替换。文档元数据放 Postgres，向量放 FAISS/Milvus/pgvector，原文放对象存储；索引构建走异步任务；查询加 metadata filter、分片、缓存和监控。当前架构模块边界已经为替换存储留了空间。

### Q25：为什么选择前后端分离？

**答：** RAG 后端和展示 UI 迭代节奏不同。后端关注数据管线、检索、生成和 SSE contract；前端关注交互、引用高亮、过程可视化。前后端分离使 API contract 清晰，也方便测试和替换 UI。

### Q26：你如何证明这是工程项目，而不是 demo 拼接？

**答：** 它有完整目录结构、Pydantic schema、导入脚本、索引构建脚本、provider abstraction、SSE contract、前端 adapter、pytest 测试和规划文档。并且我能说清楚每层的输入输出、失败模式和下一步生产化路径。

### Q27：如果面试现场网络断了怎么办？

**答：** 默认 mock provider 可以离线运行核心链路，前端也有 fallback mock documents。真实 provider 是增强，不是 demo 唯一依赖。这是我刻意做的面试稳定性设计。

### Q28：如果检索不到资料，系统怎么回答？

**答：** prompt 和 mock answer 都要求“资料中未提及”或明确说明当前本地资料没有可引用证据。生产化要进一步做 no-answer threshold，比如 TopK score 低于阈值就拒答，而不是强行生成。

### Q29：为什么有 query rewrite？

**答：** 金融实体有别名：宁德时代/CATL/300750，贵州茅台/茅台/600519，NVIDIA/NVDA/英伟达。Query rewrite 可以扩展召回词，提高 BM25 和向量检索覆盖率，也可以根据 intent 构造子问题。

### Q30：当前 query rewrite 有什么不足？

**答：** 规则化实现简单稳定，但覆盖有限，比如台积电/TSMC alias 还需要补全。生产化可结合实体词典、证券主数据、LLM rewrite 和 query classification，但要注意 rewrite 不应引入错误实体。

---

## 11. 5 分钟 Demo 演示脚本

> 目标：让面试官在 5 分钟内看到“数据管线 + 检索可视化 + 引用答案 + 工程取舍”。

### 0:00 - 0:40 项目定位

讲：

> 这是一个金融 RAG Agent demo，核心不是做一个聊天框，而是展示从公开 PDF 到可引用金融问答的完整链路。当前有 40 个公开 PDF，覆盖宁德时代、贵州茅台、NVIDIA、台积电，导入后生成 9303 个 chunks。

指给面试官看：

- 左侧文档库。
- 示例问题。
- 右侧检索过程面板。

### 0:40 - 1:30 数据管线

讲：

> PDF 不是在线解析，而是先由 `pdf2md --profile finrag` 转成 raw Markdown，保留 hash、source、page marker；再由 backend importer 生成统一 Document/Chunk schema；最后 build index。这样好处是可复跑、可审计、查询延迟稳定。

可以打开/展示路径：

- `backend/app/data/processed/documents.json`
- `backend/app/data/processed/chunks.json`
- `backend/app/data/index/`

### 1:30 - 2:30 发起事实型问题

点击左侧示例或输入：

```text
英伟达 FY2026Q3 最近一个季度总营收是多少？数据中心业务贡献多少？
```

讲：

> 先看 query rewrite，它会扩展 NVIDIA/NVDA/revenue/Data Center；然后后端分别做 BM25 和 vector 召回；右侧可以看到两个召回通道的结果；之后 rerank 选 Top5 evidence，最终答案里引用 [1][2] 对应右侧证据。

强调：

- 如果引用能点击，就点击 citation 看右侧高亮。
- 如果结果不完美，就顺势说明 mock embedding 和下一步真实 provider。

### 2:30 - 3:30 发起分析型问题

输入：

```text
宁德时代和贵州茅台近期经营表现分别有哪些值得关注的风险和亮点？
```

讲：

> 分析型问题不是只找一个数字，而是要聚合多段证据。这个时候 hybrid retrieval 和 rerank 的价值更明显。BM25 保证公司名和财务词命中，向量召回覆盖“风险/亮点”这类语义表达，rerank 控制最终进入 prompt 的证据质量。

强调：

- 当前 Top5 evidence 是系统真正喂给生成模块的上下文。
- 金融场景最重要的是 evidence-grounded，不是泛泛分析。

### 3:30 - 4:20 展示架构/代码点

快速打开这些文件说明：

- `backend/app/api/query.py`：SSE 事件顺序。
- `backend/app/core/retrieval/hybrid.py`：BM25 + Vector + RRF。
- `backend/app/core/retrieval/rerank_service.py`：rerank + fallback。
- `backend/app/core/agent/prompts.py`：只依据资料回答、资料无则拒答。
- `frontend/src/api/finrag.ts`：前端解析 POST SSE。

讲：

> 代码上我尽量把每层拆清楚，不依赖一个大框架魔法。这样面试时可以解释每一步，真实项目里也方便替换为 FAISS、Milvus 或真实模型 provider。

### 4:20 - 5:00 主动说局限和下一步

讲：

> 我也明确知道当前还有 MVP 简化：默认 embedding/rerank/text 是 mock，vector store 还是 JSON，不是生产级向量库；rerank 目前主要基于 preview，证据文本应扩展到完整 chunk；前端 per-turn evidence 还在 v1.2 路线里。下一步我会优先做真实 embedding provider 一致性、FAISS/pgvector、citation post-check、评测集和可观测 tracing。

最后收束：

> 所以这个项目展示的是我能把 LLM/RAG 能力工程化：不是只调模型，而是能从数据、检索、排序、生成、引用、前端可视化、测试和降级一起考虑。

---

## 12. Jamie 面试前优先背诵的章节

如果时间很少，优先看：

1. **第 0 章：项目一句话定位** — 先把项目讲清楚。
2. **第 1 章：1-2 分钟开场讲法** — 面试开场直接背这个。
3. **第 3 章：核心数据流** — 面试官问架构时按这个讲。
4. **第 8 章：当前局限与改进路线** — 展示诚实和工程成熟度。
5. **第 9 章：bug/不足怎么回答** — 防止被 mock embedding 追问时慌。
6. **第 10 章 Q6-Q14、Q18-Q24** — 高频 RAG、SSE、评测、性能问题。
7. **第 11 章：5 分钟 Demo 脚本** — 现场演示按这个走。

---

## 13. 一页速记版

### 项目本质

金融文档 RAG demo：公开 PDF → Markdown → chunks → BM25/vector index → hybrid retrieval → rerank Top5 → cited Markdown answer → React SSE 可视化。

### 三个亮点

1. **可追溯**：frontmatter、manifest、page marker、citation map。
2. **可观测**：前端展示 query rewrite、BM25、Vector、Rerank、answer stream。
3. **可替换**：embedding/rerank/text provider 抽象，mock 保稳定，real provider 可切换。

### 三个诚实局限

1. 当前默认 mock embedding，不是生产级语义检索。
2. 当前 vector store 是 JSON，小规模 demo OK，生产要 FAISS/pgvector/Milvus。
3. 当前 rerank/evidence 主要用 preview，生产要完整 chunk + citation post-check + 评测。

### 最佳收尾

> 这个项目我最想展示的是 RAG 工程闭环能力：我知道一个可用的 RAG 系统不只是“向量库 + 大模型”，还包括数据治理、检索策略、排序、引用、拒答、流式交互、测试、降级和可观测。当前 MVP 做了最小闭环，也明确留下了生产化升级路径。
