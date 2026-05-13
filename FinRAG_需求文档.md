# FinRAG 金融智能研究 Agent — 需求文档

**版本**：v1.0  
**目标**：面试演示用 MVP，两天内完成  
**核心定位**：面向金融研究与投顾分析场景的智能 RAG Agent 系统，而非通用问答机器人

---

## 一、项目总览

### 1.1 项目背景
本项目是一个金融领域 RAG 系统的最小可运行原型，用于演示完整的"多源异构数据治理 → 混合检索 → Rerank → Agent 分析 → 可溯源生成"全链路能力。目标用户是金融研究员、投顾分析师。

### 1.2 核心演示场景
用户输入金融问题，系统输出带溯源的结构化分析。重点演示三个递进的查询：

1. **事实型查询**：「贵州茅台 2023 年营业收入是多少？同比增长率？」
2. **分析型查询**：「宁德时代近期有哪些潜在经营风险？」
3. **推理型查询**：「美联储加息对 A 股新能源板块可能产生什么影响？」

### 1.3 技术栈总览

| 层 | 技术选型 | 说明 |
|---|---|---|
| 前端 | React 18 + TypeScript + Vite | 使用 SSE 接收流式数据 |
| UI 框架 | Ant Design 或 shadcn/ui | 任选其一，含 Markdown 渲染 |
| Markdown 渲染 | react-markdown + remark-gfm | 支持表格、列表 |
| 后端 | Python 3.10 + FastAPI | 提供 SSE 流式接口 |
| 向量库 | FAISS | 本地索引，10万级别向量 |
| 关键词检索 | rank_bm25 | Python 原生 BM25 |
| Embedding | BGE-M3（API 调用） | 硅基流动 / 阿里云灵积 |
| Rerank | bge-reranker-large | API 调用 |
| LLM | DeepSeek / Qwen / OpenAI | API 调用 |
| PDF 解析 | pdfplumber + PyMuPDF | 表格抽取 + 文本提取 |

### 1.4 总体分工

- **前端团队**：UI 界面、SSE 接收与渲染、Markdown 展示、可视化检索过程
- **后端团队**：数据治理 Pipeline、混合检索、Rerank、Agent Workflow、SSE 推送
- **联调点**：仅 1 个 HTTP SSE 接口 + 1 个文档列表查询接口

---

## 二、系统整体架构

```
[前端 React] 
    ↓ POST /query (SSE)
[FastAPI 后端]
    ↓
[Query Rewrite 模块] → 别名扩展、子问题拆分
    ↓
[Hybrid Retrieval 模块]
    ├── FAISS 向量检索 (Top 20)
    └── BM25 关键词检索 (Top 20)
    ↓ RRF / 加权融合
[Rerank 模块] → Cross-encoder 精排 (Top 5)
    ↓
[Agent Workflow 模块]
    ├── 意图识别 (事实型 / 分析型 / 推理型)
    └── 结构化 Prompt 生成
    ↓
[LLM 生成 + 溯源标注]
    ↓ SSE 流式返回
[前端渲染]
```

---

## 三、前端需求文档

### 3.1 UI 总体布局

**单页应用，三栏布局**（桌面端 1440px 优先）：

```
┌────────────────────────────────────────────────────────┐
│  Header: FinRAG · 金融智能研究 Agent              [示例] │
├──────────┬────────────────────────────┬────────────────┤
│          │                            │                │
│  左栏    │     中间栏：会话区          │   右栏:        │
│  示例    │     (输入框 + 答案流)       │   检索过程     │
│  问题    │                            │   可视化       │
│  + 文档  │                            │                │
│  库      │                            │                │
│          │                            │                │
└──────────┴────────────────────────────┴────────────────┘
   240px              主区域 flex-1            400px
```

### 3.2 左栏：示例与文档库（P0）

#### 3.2.1 示例问题区
- 显示 3 个预置的演示问题，点击直接发送到中间栏
  - 「贵州茅台 2023 年营收和增长率？」（事实型 · 蓝标签）
  - 「宁德时代近期有哪些经营风险？」（分析型 · 橙标签）
  - 「美联储加息对新能源板块的影响？」（推理型 · 紫标签）
- 每个示例右上角有标签标注查询类型

#### 3.2.2 知识库面板
- 调用 `GET /api/documents` 接口，列出已入库文档
- 字段：文档名 · 类型（财报 / 研报 / 新闻）· 公司 · 日期
- 仅展示，不可编辑（演示用）

### 3.3 中间栏：对话与答案（P0）

#### 3.3.1 输入框组件
- 多行输入框（textarea），最多 3 行
- 下方有「发送」按钮（Enter 也可发送，Shift+Enter 换行）
- 输入时启用 Query Rewrite 预览模式（P1）：
  - 用户停止输入 500ms 后，前端可调用 `/api/preview-rewrite`（可选）展示扩展后的 Query
  - 显示形式：「检索关键词：宁德时代、CATL、300750、锂电池龙头」

#### 3.3.2 答案流展示区（核心）
按 SSE 推送的事件类型分阶段渲染：

**阶段一：Query 处理**
- 显示 Loading 动画 + "正在理解你的问题..."
- 收到 `query_rewrite` 事件后展示扩展词

**阶段二：检索召回**
- 显示 "正在检索 N 篇相关文档..."
- 收到 `retrieval_complete` 事件后显示召回数量统计

**阶段三：Rerank**
- 显示 "正在精排筛选最相关内容..."
- 收到 `rerank_complete` 事件后显示 Top 5 文档预览（标题 + 评分）

**阶段四：生成答案**
- 收到 `answer_chunk` 事件后逐字流式渲染
- 使用 `react-markdown` 渲染 Markdown 格式
- **溯源引用样式**：答案中出现的 `[1]`、`[2]` 等标记应为可点击的角标，hover 显示来源详情，点击高亮右栏对应文档

**阶段五：完成**
- 收到 `done` 事件后显示总耗时、Token 用量

#### 3.3.3 Markdown 渲染要求
- 支持标题（H1-H4）、列表、加粗、代码块、表格
- 引用角标 `[1]`、`[2]` 需自定义渲染器，转为可点击的徽章组件
- 数字、百分比、金额等可加轻量高亮（可选）

### 3.4 右栏：检索过程可视化（P1，强烈推荐）

#### 3.4.1 三阶段对比面板
垂直排列三个折叠面板，每个面板展示对应阶段的文档列表：

**面板 1：BM25 召回 Top 10**
- 列表每项：文档片段标题 · 来源 · BM25 分值
- 分值用横向小条形图展示

**面板 2：向量召回 Top 10**
- 同上结构，分值改为 Cosine 相似度

**面板 3：Rerank 后 Top 5**
- 同上，分值为 Rerank 得分
- 每项可展开查看完整片段内容（点击展开）

#### 3.4.2 文档片段卡片
每个片段卡片包含：
- 文档名 + 页码 / 段落号
- 文档类型徽章（财报 / 研报 / 新闻）
- 日期
- 内容预览（前 100 字）
- 评分数值（精确到 2 位小数）

#### 3.4.3 联动效果
- 当中间栏答案中的 `[1]` 角标被点击时，右栏对应文档卡片高亮（边框变色 + 滚动到可视区）

### 3.5 全局组件需求

#### 3.5.1 顶部 Header
- 左侧：项目名 + Logo
- 右侧：「重置会话」按钮、「关于」按钮

#### 3.5.2 加载状态
- 所有异步阶段都需要骨架屏或进度条
- SSE 断开时显示 Toast 提示并允许重连

#### 3.5.3 错误处理
- 后端错误：显示错误信息 + 重试按钮
- 网络错误：自动重连最多 3 次

### 3.6 前端目录结构建议

```
finrag-web/
├── src/
│   ├── api/
│   │   ├── sse.ts           # SSE 客户端封装
│   │   └── documents.ts     # 文档列表 API
│   ├── components/
│   │   ├── ChatInput.tsx
│   │   ├── AnswerStream.tsx
│   │   ├── RetrievalPanel.tsx
│   │   ├── DocumentCard.tsx
│   │   └── CitationBadge.tsx
│   ├── hooks/
│   │   └── useFinRAG.ts     # SSE 状态管理
│   ├── pages/
│   │   └── Home.tsx
│   ├── types/
│   │   └── api.ts           # 接口类型定义
│   └── App.tsx
├── package.json
└── vite.config.ts
```

### 3.7 前端验收标准

- [ ] 三个示例问题可正常发送并接收响应
- [ ] SSE 流式渲染分阶段可见，每阶段有视觉反馈
- [ ] Markdown 答案正确渲染，引用角标可点击
- [ ] 右栏三阶段检索结果完整展示
- [ ] 引用联动效果正常
- [ ] 错误处理与重连机制有效

---

## 四、后端需求文档

### 4.1 后端模块划分

```
backend/
├── app/
│   ├── main.py                 # FastAPI 入口
│   ├── api/
│   │   ├── query.py            # SSE 查询接口
│   │   └── documents.py        # 文档列表接口
│   ├── core/
│   │   ├── ingestion/          # 数据治理
│   │   │   ├── pdf_parser.py
│   │   │   ├── news_parser.py
│   │   │   ├── chunker.py
│   │   │   └── normalizer.py   # 统一 Schema
│   │   ├── retrieval/          # 检索
│   │   │   ├── vector_store.py
│   │   │   ├── bm25_store.py
│   │   │   ├── hybrid.py
│   │   │   └── reranker.py
│   │   ├── agent/              # Agent Workflow
│   │   │   ├── query_rewrite.py
│   │   │   ├── intent_classifier.py
│   │   │   └── workflow.py
│   │   └── generation/         # 生成
│   │       ├── prompt_templates.py
│   │       └── llm_client.py
│   ├── models/
│   │   ├── schemas.py          # Pydantic 模型
│   │   └── events.py           # SSE 事件类型
│   └── data/
│       ├── raw/                # 原始 PDF/新闻
│       ├── processed/          # 处理后 JSON
│       └── index/              # FAISS + BM25 索引
├── scripts/
│   ├── build_index.py          # 离线建索引脚本
│   └── seed_data.py            # 准备演示数据
└── requirements.txt
```

### 4.2 数据治理 Pipeline（P0）

#### 4.2.1 统一文档 Schema

所有数据源最终都要归一化为以下结构：

```python
class Document:
    doc_id: str              # 文档唯一 ID
    company: str             # 公司名（标准化，如"贵州茅台"）
    company_aliases: list    # 别名 ["茅台", "贵州茅台", "600519"]
    doc_type: str            # "financial_report" | "research_report" | "news"
    title: str
    date: str                # ISO 格式 "2024-03-15"
    source: str              # 来源 "贵州茅台2023年报"
    content: str             # 全文

class Chunk:
    chunk_id: str
    doc_id: str
    section: str             # "主要会计数据" | "管理层讨论" 等
    page_num: int
    chunk_index: int
    content: str
    embedding: list[float]   # 1024 维（BGE-M3）
    metadata: dict           # 透传 company/date/doc_type
```

#### 4.2.2 数据准备（演示数据）
准备至少 5 份数据：
- 2 份 A 股财报 PDF（贵州茅台 2023 年报、宁德时代 2023 年报）
- 1 份券商研报 PDF（任意宁德时代深度研报）
- 5-10 条对应公司的近期新闻文本（手工准备 JSON 即可）

#### 4.2.3 结构化 Chunk 策略

**关键点：不要用 LangChain 默认的 512 token 固定切分**

- **财报**：按章节切分
  - 一级标题：「重要提示」「主要会计数据」「管理层讨论」「财务报表附注」等
  - 表格独立成 chunk（保留行列结构，转为 Markdown 表格存储）
- **研报**：按段落语义切分
  - 优先按「投资逻辑」「风险提示」「盈利预测」等标题切
  - 每个 chunk 控制在 300-800 字
- **新闻**：整篇一个 chunk（一般 500-1000 字以内）

#### 4.2.4 实体抽取（轻量级，P1）
- 用 LLM 或简单规则抽取 chunk 中提到的公司列表
- 存入 chunk metadata 用于结构化检索

### 4.3 检索模块（P0）

#### 4.3.1 向量检索
- FAISS IndexFlatIP（内积，配合归一化的 embedding 即等价于余弦相似度）
- Embedding 调用 BGE-M3 API
- 检索时返回 Top 20，附带 chunk_id 和分值

#### 4.3.2 BM25 关键词检索
- 使用 `rank_bm25` 库的 `BM25Okapi`
- 中文分词用 jieba
- 检索时返回 Top 20，附带 chunk_id 和分值

#### 4.3.3 混合检索融合
采用 RRF（Reciprocal Rank Fusion）：

```
final_score(d) = Σ 1 / (k + rank_i(d))
其中 k = 60，rank_i 为文档在第 i 路召回中的排名
```

或简单加权（备选）：
```
final_score = 0.6 * normalize(semantic_score) + 0.4 * normalize(bm25_score)
```

返回融合后的 Top 20 用于后续 Rerank。

### 4.4 Rerank 模块（P0）

- 调用 `bge-reranker-large` API（硅基流动可用）
- 输入：Query + Top 20 候选 chunk 内容
- 输出：Top 5 重排序结果 + 相关性分值
- **金融场景加权调整**：在 Rerank 后对时效性敏感的 query 应用时效衰减权重
  - 衰减公式：`adjusted_score = rerank_score * exp(-λ * days_old / 365)`
  - λ 可配置，默认 0.3

### 4.5 Query Rewrite 模块（P1，重要）

#### 4.5.1 实体别名扩展
- 维护一个公司别名词典（JSON 文件，手工准备 30-50 条主流公司即可）：
  ```json
  {
    "宁德时代": ["CATL", "300750", "宁德时代新能源"],
    "贵州茅台": ["茅台", "600519", "贵州茅台酒"]
  }
  ```
- 查询时检测命中实体，自动注入别名

#### 4.5.2 子问题拆分（LLM 调用）
- 对于复杂查询（如「美联储加息对新能源的影响」），用 LLM 拆分为子问题：
  - 「美联储加息历史与最新动态」
  - 「加息对企业融资成本的影响」
  - 「新能源行业现金流敏感性」
- 子问题分别检索后合并候选集

### 4.6 Agent Workflow 模块（P1，决胜点）

#### 4.6.1 意图分类
用 LLM 把 Query 分为三类：
- `factual`：事实型查询，需要精确数字
- `analytical`：分析型查询，需要多维归因
- `reasoning`：推理型查询，需要跨领域推断

#### 4.6.2 分类对应的输出模板

**factual 型**：
```markdown
**[直接答案]**：xxx

**数据来源**：[1]
**计算细节**（如适用）：xxx
```

**analytical 型**：
```markdown
## [主题] 分析

### 1. [维度一]
内容...[1][2]

### 2. [维度二]
内容...[3]

### 3. [维度三]
内容...[4]

## 综合判断
xxx
```

**reasoning 型**：
```markdown
## 推理路径

### 前提一：[事实A]
[1][2]

### 前提二：[事实B]
[3]

### 推理结论
基于以上事实，xxx
```

#### 4.6.3 Workflow 执行流程
```python
async def run_workflow(query: str):
    # 1. Query Rewrite
    rewritten = await rewrite_query(query)
    yield SSEEvent("query_rewrite", rewritten)
    
    # 2. Hybrid Retrieval
    candidates = await hybrid_retrieve(rewritten, top_k=20)
    yield SSEEvent("retrieval_complete", candidates)
    
    # 3. Rerank
    top5 = await rerank(query, candidates, top_k=5)
    yield SSEEvent("rerank_complete", top5)
    
    # 4. Intent Classification
    intent = await classify_intent(query)
    
    # 5. Generate with template
    async for chunk in generate_answer(query, top5, intent):
        yield SSEEvent("answer_chunk", chunk)
    
    yield SSEEvent("done", {"latency_ms": xxx, "tokens": yyy})
```

### 4.7 生成与溯源（P0）

#### 4.7.1 Prompt 设计核心要求
- 系统 Prompt 中明确要求：
  - 仅基于提供的资料回答，不臆测
  - 每个事实陈述后必须附引用编号 `[N]`
  - 数字必须与原文一致
  - 拒答原则：资料不足时明确说"资料中未提及"

#### 4.7.2 引用规范
- LLM 输出形如 `贵州茅台2023年营收为1505亿元[1]`
- 后端在生成完成后将 `[1]` 映射为对应 chunk 的元数据，前端可点击查看

#### 4.7.3 幻觉检测（轻量级，P2）
- 数字一致性校验：从答案中提取所有数字，检查是否能在检索到的 chunk 中找到
- 不一致时在答案末尾追加警告标记

---

## 五、接口契约（前后端联调核心）

### 5.1 接口一：流式查询（SSE）

**Endpoint**：`POST /api/query`

**请求**：
```json
{
  "query": "宁德时代近期有哪些经营风险？",
  "session_id": "uuid-xxx"  // 可选，用于会话上下文
}
```

**响应**：`Content-Type: text/event-stream`

**SSE 事件类型**：

#### 事件 1：query_rewrite
```
event: query_rewrite
data: {"original": "宁德时代近期风险", "expanded": ["宁德时代", "CATL", "300750"], "sub_queries": ["经营风险", "舆情风险", "财务风险"]}
```

#### 事件 2：retrieval_complete
```
event: retrieval_complete
data: {
  "bm25_results": [
    {"chunk_id": "c001", "title": "宁德时代2023年报-风险因素", "doc_type": "financial_report", "company": "宁德时代", "date": "2024-03-15", "page": 23, "preview": "...", "score": 0.87}
  ],
  "vector_results": [...],
  "fused_top20": [...]
}
```

#### 事件 3：rerank_complete
```
event: rerank_complete
data: {
  "top5": [
    {
      "chunk_id": "c001",
      "rank": 1,
      "rerank_score": 0.95,
      "title": "...",
      "doc_type": "...",
      "company": "...",
      "date": "...",
      "page": 23,
      "content": "完整片段内容...",
      "citation_id": 1
    }
  ]
}
```

#### 事件 4：intent_detected（可选）
```
event: intent_detected
data: {"intent": "analytical", "template": "multi_dimensional_analysis"}
```

#### 事件 5：answer_chunk（多次推送）
```
event: answer_chunk
data: {"text": "## 经营风险分析\n\n### 1. 原材料风险\n", "is_final": false}
```

#### 事件 6：done
```
event: done
data: {"latency_ms": 4523, "total_tokens": 2150, "citations": {"1": {"chunk_id": "c001", "...": "..."}, "2": {...}}}
```

#### 事件 7：error
```
event: error
data: {"code": "LLM_TIMEOUT", "message": "生成超时，请重试"}
```

### 5.2 接口二：文档列表

**Endpoint**：`GET /api/documents`

**响应**：
```json
{
  "total": 8,
  "documents": [
    {
      "doc_id": "d001",
      "title": "贵州茅台 2023 年年度报告",
      "doc_type": "financial_report",
      "company": "贵州茅台",
      "date": "2024-03-28",
      "chunk_count": 42
    }
  ]
}
```

### 5.3 接口三：Query Rewrite 预览（可选，P1）

**Endpoint**：`POST /api/preview-rewrite`

**请求**：`{"query": "..."}`  
**响应**：`{"expanded_terms": [...], "detected_entities": [...]}`

### 5.4 联调约定
- 后端启动后默认监听 `http://localhost:8000`
- 前端开发期通过 Vite 代理转发 `/api` 请求
- 所有时间字段统一为 ISO 8601 格式
- 所有 ID 字段为字符串
- SSE 心跳：后端每 15s 发送一次 `event: ping`

---

## 六、开发与交付时间表

### 周三晚（今晚）
- [x] 需求文档评审
- [ ] 前后端各自搭建项目脚手架
- [ ] 后端：准备演示数据，跑通最简单的 PDF 解析

### 周四（核心 P0 开发日）
**前端**：
- 上午：UI 三栏布局 + 输入框 + 基础组件
- 下午：SSE 客户端 + 各阶段渲染 + Markdown 展示

**后端**：
- 上午：数据治理 Pipeline + FAISS + BM25 双库建好
- 下午：Hybrid Retrieval + Rerank + SSE 接口骨架 + LLM 生成

**晚上联调一次**：跑通 query → 答案的最小闭环

### 周五上午（P1 升级日）
**前端**：右栏检索可视化 + 引用联动效果  
**后端**：Query Rewrite + 意图分类 + 模板化生成

### 周五下午（演示准备）
- 完整联调三个演示 case
- 准备 PPT（架构图 + P2/P3 设计思路 + 优化方向）
- 录制备份视频（防止现场网络问题）
- 演示话术排练

---

## 七、风险与降级方案

| 风险 | 概率 | 降级方案 |
|---|---|---|
| LLM API 速率限制 | 中 | 准备 2 个不同厂商的 Key，故障时切换 |
| Rerank API 不可用 | 低 | 降级为只用 Hybrid Retrieval 的 Top 5 |
| PDF 表格解析失败 | 高 | 手工补一份关键数据 JSON 兜底 |
| 现场网络问题 | 中 | 提前录制演示视频 + 截屏备份 |
| 前后端联调延期 | 中 | 提前约定 Mock 数据，前端可独立用 Mock 开发 |

---

## 八、面试演示要点（开发期请同步思考）

虽然这部分不影响开发，但请前后端团队理解这些点，避免技术选择偏离演示目标：

1. **可视化检索过程是杀手锏**：右栏的三阶段对比是为了让面试官"看到"系统在做什么，前端必须把这部分做出彩
2. **溯源不是装饰，是核心**：金融场景下幻觉是死罪，引用必须精确到段落
3. **Agent 不是聊天**：分析型 query 必须输出结构化 Markdown，不能像 ChatGPT 那样平铺直叙
4. **不要追求功能多**：宁可少而精，每个功能都能讲透
5. **未实现的部分写在架构图**：实时增量索引、知识图谱多跳推理等 P2 内容画在架构图上，演示时说明"由于时间限制本期未实现，但设计已就绪"

---

**文档结束**

如有疑问联系：[你的名字 / 联系方式]
