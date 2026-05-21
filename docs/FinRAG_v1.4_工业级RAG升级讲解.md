# FinRAG v1.4 — 工业级 RAG 升级讲解

> **目标读者**：项目作者本人，用于复盘 v1.4 milestone 全套改动 + 在面试中清晰讲解
> **时间范围**：Phase 17 ~ Phase 22（2026-05-21 起的 14 个 commit）
> **核心目标**：把一个"直接 hybrid retrieval + LLM"的 RAG demo，升级为**可追溯、可路由、可迭代、可下钻**的工业级 RAG 架构

---

## 0. 一句话总览

v1.4 把检索从"一个黑盒函数 `retrieve(query) → top-k`" 重构为**七个可观测、可降级、可解释的阶段**，并在前端把每个阶段的输入/输出/降级原因都可视化出来。

```
原始查询
  │
  ▼ Phase 17 · 结构化查询理解
RetrievalPlan { intent, task_type, entities, metrics, time_range, strategy, filters, signals }
  │
  ▼ Phase 18 · 路由 + 元数据预过滤
选定 route + 应用 metadata_filters（必要时松弛）
  │
  ▼ Phase 19 · 级联追踪
每个阶段都记录 input_count / output_count / degraded / fallback_reason
  │
  ▼ Phase 21 · 迭代检索（仅 risk/causal/trend/comparison 类）
3 步检索：background_facts → risk_or_driver → cross_check
  │
  ▼ Phase 22 · 层级下钻
命中 section/table 父级 → 自动扩展子 chunk
  │
  ▼ Phase 20 · 证据压缩
EvidencePack：去重 + 字段保留 + 文本截断
  │
  ▼ LLM 生成（保持原有 prompt + 引用逻辑）
```

---

## 1. 为什么要做这次升级

### 1.1 原有 demo 的局限

| 局限 | 现象 | 工业级要求 |
|------|------|----------|
| 查询语义丢失 | `analyze_query()` 只返回简单的 expanded terms 和 intent，下游无法基于查询语义优化 | 需要结构化的 query plan 让路由层决策 |
| 路由单一 | 所有查询走同一套 BM25+vector hybrid，财务表格查询和分析类查询用同样的召回策略 | 不同任务类型应走不同检索路径 |
| 过程不可见 | 一个 `retrieve(query) → list` 调用，召回多少、过滤多少、为何掉粒度全是黑盒 | 每个阶段需要 input/output count + 降级原因 |
| 上下文污染 | 直接把 top-5 chunk 全文喂给 LLM，长文本+重复源拉低生成质量 | 需要证据级去重和字段级保留 |
| 缺乏深度 | "宁德时代经营风险" 这种复杂分析问题，单次检索召回不出"驱动+反向"全景 | 需要 agentic 多步检索 |
| 粒度死板 | 所有 chunk 都是 paragraph 级，命中段落后无法看到所属章节上下文 | 需要 section/table 父级与子级关联 |

### 1.2 v1.4 milestone 设计原则

1. **可观测 > 性能优化**：演示型项目，每一步要能在前端看到，便于面试讲解
2. **向后兼容**：`analyze_query()`、`retrieve()`、SSE 事件顺序全部保留，新功能通过可选字段追加
3. **多层降级**：任何新增能力都必须有 fallback 到原有路径的兜底
4. **规则优先 LLM 兜底**：演示场景下确定性 > 智能性，避免每次跑出不同结果
5. **测试驱动**：每个 Phase 先写测试再实现，最终 116 个测试全部通过

---

## 2. Phase 17 — 结构化查询理解（QUERY-01/02/03）

### 2.1 解决的问题

之前 `analyze_query()` 只产出 `expanded_terms` 和 `intent`，下游路由层拿不到"这是个 NVIDIA 营收数字查询" vs "这是个 CATL 风险分析" 的语义区别。

### 2.2 核心新增

**新文件**：
- `backend/app/core/agent/query_ontology.py` — 本体匹配器
- `backend/app/models/schemas.py` 新增 `RetrievalPlan`、`QueryEntity`、`QueryMetric`、`QueryTimeRange` 等 Pydantic 模型

**关键设计**：
```python
class RetrievalPlan(BaseModel):
    original_query: str
    normalized_query: str
    intent: QueryIntent              # factual / analytical / reasoning
    task_type: QueryTaskType         # metric_lookup / causal_analysis / risk_analysis / ...
    entities: list[QueryEntity]      # 规范化实体（"英伟达" → "NVIDIA"）
    metrics: list[QueryMetric]       # 规范化度量（"营收" → "revenue"）
    time_range: Optional[QueryTimeRange]
    preferred_doc_types: list[DocType]
    retrieval_strategy: RetrievalStrategy  # table_fact_first / research_report_analysis / ...
    filters: dict[str, Any]          # 投影成下游可消费的过滤约束
    signals: list[str]               # 调试信号：entity:NVIDIA, metric:revenue, time_fallback:dateparser
```

### 2.3 技术选型

| 模块 | 选型 | 理由 |
|------|------|------|
| 实体/度量匹配 | `flashtext-i18n` + stdlib fallback | 工业级 CJK 友好关键词匹配，性能优于纯 regex；fallback 保证测试可重现 |
| 时间解析 | 两层：财务期规则 + `dateparser` | 财报场景以"FY2026Q3"等优先，普通日期 fallback 到 dateparser |
| 任务分类 | 规则 + 优先级 | causal > risk > trend > comparison > metric_lookup > general，确保确定性 |

### 2.4 测试覆盖

- NVIDIA 营收（metric_lookup）
- 贵州茅台净利润变化（causal_analysis）
- 宁德时代经营风险（risk_analysis）
- 宏观消费变化影响白酒（reasoning + causal_analysis）
- 台积电财报营收（financial_report_first 路由触发条件）
- 普通日期 fallback（`November 19 2025`）

### 2.5 面试讲点

- **"为什么不用 LLM 做查询理解？"**：演示场景需要确定性 + 低延迟，规则系统 + 词典本体覆盖 80% 财经场景；LLM 作为未来扩展点
- **"FlashText vs 正则？"**：FlashText 基于 Aho-Corasick trie，单次扫描匹配所有关键词，比 N 次 regex 快 O(N) 倍，对 CJK 边界处理也更稳
- **"规范化为什么重要？"**：让下游所有模块（路由、过滤、表格事实查询）共享同一份实体词典，避免 `"英伟达" vs "NVIDIA"` 的别名漂移

---

## 3. Phase 18 — 知识路由与元数据预过滤（ROUTE-01/02/03/04）

### 3.1 解决的问题

不同类型的查询应该走不同检索路径：
- "NVIDIA Q3 营收是多少" → 应优先查表格事实（精确数字）
- "宁德时代经营风险" → 应优先查研报正文（分析叙述）
- 全局过滤可以提前砍掉无关公司/期间的 chunk

### 3.2 核心新增

**新文件**：
- `backend/app/core/retrieval/router.py` — `choose_route(plan, query) → RouteDecision`
- `backend/app/core/retrieval/filters.py` — `build_metadata_filters(plan)` + `apply_metadata_filters()`

**四种路由**：
| 路由 | 适用场景 | preferred_doc_types |
|------|---------|---------------------|
| `table_fact_first` | metric_lookup + 有实体+有度量 | financial_report |
| `financial_report_first` | 有实体+有期间+"财报"关键词 + 无度量 | financial_report, research_report |
| `research_report_analysis` | causal / risk / trend / comparison | research_report, financial_report |
| `general_hybrid` | 兜底 | research_report, financial_report, news |

**元数据过滤的三层兜底**（这是工业级 RAG 的关键设计）：
```python
def apply_metadata_filters(items, filters, minimum_count=1):
    1. 严格过滤 → 如果结果 ≥ minimum_count，直接返回
    2. 松弛过滤 → 去掉 chunk_type/year/quarter 约束再试
    3. 全量兜底 → 都不行就返回所有候选，并标记 fallback_reason="metadata_filters_relaxed_to_all"
```

### 3.3 面试讲点

- **"为什么是 post-recall filter 而不是真正的 pre-filter？"**：现有 BM25/向量索引不支持 attribute-based filter pushdown（需要换成 Qdrant/Pinecone 这类向量库才有原生支持）。当前实现是召回后再过滤，但**保留 metadata `"applied_at": "post_recall"` 标注**，让阅读者一眼知道实际语义
- **"为什么需要松弛兜底？"**：财经语料命名不规范，严格过滤经常返回 0 个结果；松弛后能保证至少有结果，并通过 `filters_relaxed` 标志告诉前端"我做了让步"
- **"router 和 filter 怎么分工？"**：router 决定召回策略（用哪个 store/index），filter 决定候选的留存。两个正交关注点分开实现，方便后续替换其中任何一个

---

## 4. Phase 19 — 检索级联追踪（CASCADE-01/02/03/04）

### 4.1 解决的问题

之前一个 `retrieve()` 调用返回 fused list，没人知道：
- BM25 召回了多少？
- 向量召回了多少？
- 元数据过滤掉了多少？
- 是否触发了降级？

### 4.2 核心新增

**新模型**：
```python
class RetrievalCascadeStage(BaseModel):
    name: RetrievalCascadeStageName   # query_plan / coarse_recall / metadata_filter / ...
    method: str                        # 实际用的算法/路由
    input_count: int
    output_count: int
    degraded: bool = False
    fallback_reason: Optional[str]
    metadata: dict[str, Any]           # 阶段特定信息
```

**七个标准阶段**（每次检索都按这个顺序追加）：
1. `query_plan` — Phase 17 产出 plan
2. `coarse_recall` — BM25+向量+supplemental 三路召回
3. `metadata_filter` — Phase 18 过滤（标注 `applied_at: "post_recall"`）
4. `hierarchy_drill_down` — Phase 22 父级下钻（可选）
5. `fusion` — RRF 融合
6. `rerank` — reranker 模型打分
7. `final_evidence` — Phase 20 证据压缩

### 4.3 面试讲点

- **"为什么把 trace 设计成数据而不是日志？"**：日志只能事后看，数据可以推到前端实时可视化，也能写入 done event 给评测系统用
- **"为什么 input/output 都是 count 而不是详细 ids？"**：演示足够 + 不污染 SSE payload。需要详细列表时可以走 `/api/debug/retrieval` 拿完整对象
- **"trace 的执行顺序是怎么定的？"**：严格按代码实际执行顺序排，而不是按"概念顺序"排——这样新人读代码可以直接对照 trace 验证理解

---

## 5. Phase 20 — 证据压缩（EVIDENCE-01/02/03/04）

### 5.1 解决的问题

之前 top-5 chunk 直接喂 prompt，问题：
- 同一份 10-Q 报告可能产出多个相似 chunk，重复浪费 token
- 表格事实如 `revenue=57,006` 经过 chunk 化后会丢失单位/期间/source_pdf 等关键 metadata
- 长文本 chunk 没有截断策略

### 5.2 核心新增

**新文件**：`backend/app/core/agent/context_builder.py`

```python
class EvidencePackItem(BaseModel):
    citation_id: int
    chunk_id: str
    ...
    content: str              # 原始全文
    compact_content: str      # 压缩后用于 prompt
    preserved_fields: dict    # 表格事实的结构化字段（value/unit/period/...）保留

class EvidencePack(BaseModel):
    items: list[EvidencePackItem]
    original_count: int       # 输入 top-k 数
    compressed_count: int     # 压缩后数（去重后）
    dropped_duplicate_count: int
```

**压缩策略**：
1. **去重**：按 chunk_id 优先；表格事实按 `(source_pdf, table_id, metric, period, raw_value)` 元组；文本按 `(title, page, content[:160])`
2. **字段保留**：table_fact 类型直接用结构化模板渲染 `metric=revenue | value=57006 | period=FY2026Q3 | unit=USD millions | source=...`
3. **文本截断**：普通文本超过 700 字符截断，加 `"..."` 标记
4. **citation_id 保留**：压缩前后 citation_id 一一对应，引用不会错位

### 5.3 面试讲点

- **"为什么不直接让 LLM 做 context 压缩？"**：成本+延迟。表格事实有结构化模板可以无损渲染，文本截断对长尾问答影响有限
- **"去重 key 怎么设计的？"**：三段降级 fallback。chunk_id 是最强 key，table_fact 元组保证不同表/期间不被误合并，文本兜底用前 160 字符避免完全相同的段落入选两次
- **"compact_content 和 content 都保留的意义？"**：`content` 喂给前端显示完整原文，`compact_content` 喂给 LLM 节省 token。两者通过同一个 EvidencePackItem 关联，不会脱节

---

## 6. Phase 21 — 迭代检索 Demo 模式（ITER-01/02/03/04）

### 6.1 解决的问题

"宁德时代经营风险"这种问题，单次检索召回的可能都是基础事实，缺少"驱动因素"和"反向论据"。需要 agentic 多步检索。

### 6.2 核心新增

**新文件**：`backend/app/core/agent/retrieval_planner.py`

```python
def should_use_iterative_retrieval(plan):
    # 仅 risk/causal/trend/comparison 任务且非 table_fact_first 时启用
    if plan.retrieval_strategy == "table_fact_first":
        return False
    return plan.task_type in {"risk_analysis", "causal_analysis", "trend_analysis", "comparison"}

def plan_iterative_retrieval(query, plan) -> IterativeRetrievalTrace:
    # 确定性 3 步：
    # 1. background_facts — 召回基础事实
    # 2. risk_or_driver_evidence — 根据 task_type 拼后缀（"经营风险"/"原因 影响"/"趋势变化"）
    # 3. cross_check — 对于 comparison/causal/risk 追加交叉验证步
```

**多层降级**（这是迭代检索的关键工业级特性）：
```
plan_iterative_retrieval() 抛异常 → "iterative_planning_failed"
    → 回退到 single_pass

iterative_trace.steps 为空 → "iterative_planning_failed"
    → 回退到 single_pass

每步 retriever.retrieve() 抛异常 → "iterative_step_failed"
    → 回退到 single_pass

3 步全成功但合并去重后 candidates 为空 → "iterative_no_evidence"
    → 回退到 single_pass
```

无论哪种降级，**用户都能拿到 single_pass 的完整答案**，只是 `degraded=True` 提示降级了。

### 6.3 面试讲点

- **"为什么是规则规划而不是 LLM 规划？"**：演示场景下，规则规划的查询步骤可以复现、可以测试；LLM 规划每次输出不同，无法调试。规则版本作为 baseline，未来可以 swap 为 LLM
- **"为什么先跑 single_pass 再决定迭代？"**：single_pass 是 fallback 保险，不管迭代怎么失败都不会让用户等空。代价是多一次检索调用，但演示场景下可接受
- **"step 的 query 拼接为什么有重复词？"**：BM25 是 term-frequency based 的，重复词等于隐式 boost。比如第 2 步把"经营风险"作为后缀，相当于告诉召回器"这次重点找风险相关的"
- **"迭代检索和 RAG agent 的关系？"**：这是 agent 的简化版——agent 应该根据每步结果决定下一步，我们这个版本是预先规划。下一阶段可以接入真正的 ReAct loop

---

## 7. Phase 22 — 层级分块与下钻（HIER-01/02/03/04）

### 7.1 解决的问题

之前 chunk 只有"段落"一种粒度：
- 命中段落后看不到它属于哪个章节
- 命中表格行后看不到表格全貌
- 检索器无法"先找到章节再钻进段落"

### 7.2 核心新增

**Import 阶段**（`corpus_importer.py` + `chunker.py`）：
1. chunker 识别 markdown heading（`#`/`##`/`###`）作为 section 边界
2. 每个 section 产出一个 `chunk_type=section` 的父 chunk，content 是子段落拼接（截断到 700 字符 + `[truncated]` 标记）
3. 父 chunk 通过 `child_ids` 列出所有子段落
4. 子段落通过 `parent_id` 指向父 section
5. 同样的逻辑用于 table → table_row

**Retrieve 阶段**（`hybrid.py`）：
```python
def _hierarchy_drill_down_hits(parent_hits, existing_ids, plan):
    # 1. 从召回结果中挑出 chunk_type ∈ {section, table} 的"父级"命中
    # 2. 通过缓存的 children_by_parent 反向索引拿到子 chunk
    # 3. 跳过已经在候选集中的子 chunk（去重）
    # 4. 每父最多 3 个子，全局最多 8 个
    # 5. 子 chunk 固定分 0.12 进入 supplemental_hits
```

**触发条件**：仅 `research_report_analysis` / `financial_report_first` 路径 + analytical/reasoning intent 启用，避免污染 metric_lookup 等精确查询。

### 7.3 性能优化

第一版 `_hierarchy_drill_down_hits` 每次查询都遍历全 corpus 构建 `parent_id → children` 反向索引，14k chunks 下显著延迟。

**优化**：把反向索引懒构建到 `self._children_by_parent`，首次构建后 O(1) 查表：
```python
def _get_children_by_parent(self):
    if self._children_by_parent is not None:
        return self._children_by_parent
    # 一次构建并缓存
    ...
```

### 7.4 面试讲点

- **"为什么不在召回时就做层级感知？"**：会破坏现有 BM25/vector store 接口。当前实现把"层级"作为后召回的扩展层，召回器本身保持简单，扩展是可插拔的
- **"父 chunk 截断到 700 字符的依据？"**：演示语料的 section 平均长度，确保 LLM context budget 不被父 chunk 占满。生产场景应根据 corpus 统计动态调整
- **"hierarchy_drill_down 0→0 是 bug 吗？"**：不是。截图里的查询直接命中了 `table_fact` 类型而不是 `section/table` 父级，所以没有可下钻的父级。这是预期行为，trace 中显式记录"探查了 0 个父级"

---

## 8. 前端可视化（SHOWCASE-01/02/03/04）

前端把 SSE/debug 响应的关键字段分成 5 个面板，便于在面试或演示中逐步讲解。

### 8.1 QUERY PLAN 面板

展示 Phase 17 的 `RetrievalPlan` 内容：
- 三个 chip：intent / task_type / retrieval_strategy
- Entities / Metrics / Doc Types / Time / Expanded / Sub queries

### 8.2 ROUTE & FILTERS 面板

展示 Phase 18 的路由决策和元数据过滤：
- Route + Reason
- Filter Count（过滤前→后）
- 松弛标志 `metadata_filters_relaxed_to_all`
- 应用的过滤约束（company/doc_type/metric/year/chunk_type）

### 8.3 CASCADE 面板（核心）

展示 Phase 19 的七个阶段，每个阶段一张卡片显示：
- 阶段名 + method
- input_count → output_count
- 降级标志（橙色徽章 `metadata_filters_relaxed_to_all`）

### 8.4 ITERATIVE STEPS 面板

展示 Phase 21 的多步检索（仅启用时显示）：
- 每步：purpose + retrieval_query + route + evidence chip 列表

### 8.5 HIERARCHY & DRILL-DOWN 面板

展示 Phase 22 的下钻详情：
- `parents/candidates → child evidence` 数量

---

## 9. 关键设计决策与权衡

### 9.1 向后兼容是硬约束

每个 Phase 都新增**可选字段**而不修改既有契约：
- `QueryRewriteEvent.plan` 可选
- `RetrievalCompleteEvent.cascade_trace` 默认空 list
- `RetrievalCompleteEvent.iterative_trace` 可选
- `HybridRetriever.retrieve()` 新参数 `plan=None`

带来的好处：老前端代码不改也能跑；新前端可以渐进接入新字段。

### 9.2 规则系统 + LLM 兜底

所有"智能"决策都用规则实现：
- 查询理解 → FlashText + 规则
- 路由 → 6 个 if-else
- 迭代规划 → 固定 3 步

LLM 留作未来扩展点（reasoning_planner.py 已经预留接口形态）。

### 9.3 多层降级是工业级标志

任何新增能力都不能让用户拿不到结果：
- 元数据过滤 → 严格 → 松弛 → 全量
- 迭代检索 → 规划失败/步骤失败/无证据 → single_pass
- 向量维度不匹配 → 降级到 BM25/table_fact，不卡死请求

### 9.4 一次构建 vs 每次查询

性能优化原则：
- `_children_by_parent` 反向索引 → 懒构建 + 实例缓存
- `_default_retriever` → 全局单例 + 显式 `clear_default_retriever_cache()` 重置
- 启动预加载 → daemon 线程，不阻塞 FastAPI 启动

---

## 10. 面试讲解模板

### 10.1 30 秒电梯版

> FinRAG v1.4 把一个"直接 hybrid retrieval"的演示项目升级为可观测的工业级 RAG 架构。核心做了 6 件事：**结构化查询理解**让下游知道"这是个什么类型的问题"；**路由 + 元数据过滤**让不同类型的问题走不同检索路径；**级联追踪**让每个检索阶段的 input/output 和降级都可见；**证据压缩**避免 LLM 上下文污染；**迭代检索**让分析类问题做多步召回；**层级分块**让段落能扩展到所属章节。每个新功能都有多层降级兜底，保证演示稳定。

### 10.2 3 分钟详细版

按以下结构讲：

1. **问题背景**（30s）：原 demo 是个 `retrieve()` 黑盒，过程不可见、策略单一、上下文易污染、缺乏深度
2. **整体架构**（30s）：用上面的数据流图，强调"7 个可观测阶段"
3. **关键模块**（90s）：
   - Phase 17 RetrievalPlan（结构化语义）
   - Phase 18 Router + Filter（差异化路径）
   - Phase 19 Cascade Trace（可观测性）
   - Phase 20 EvidencePack（压缩 + 去重）
   - Phase 21 Iterative（agentic demo）
   - Phase 22 Hierarchy（层级下钻）
4. **工程亮点**（30s）：向后兼容、多层降级、规则优先、性能优化（缓存反向索引）
5. **未来扩展**（30s）：LLM agentic planner、向量库原生 filter、稀疏神经检索、graph memory

### 10.3 常见追问应对

| 追问 | 应对要点 |
|------|---------|
| "为什么不用 LangChain/LlamaIndex 现成的？" | 演示项目需要每个组件可控、可改、可讲。框架封装的过程不可见，且无法满足"演示每个阶段"的要求 |
| "和 Anthropic Contextual Retrieval 比较？" | 我们的层级分块（Phase 22）和它的 contextual chunking 思路一致，但保留了原始 chunk 不修改，通过 parent_id 关联，避免数据冗余 |
| "工业级和这个 demo 的差距？" | (1) 向量库原生 metadata filter；(2) 索引异步更新 + 增量；(3) 真正的 LLM agentic loop；(4) 离线评测体系；(5) 多租户隔离 |
| "trace 数据量大了怎么办？" | 当前每次响应 ~5KB cascade trace，可接受；如果上百级 cascade 可以改为 SSE 单独推 stage 事件，前端流式渲染 |
| "迭代检索为什么不是真正的 ReAct？" | 规则规划是为了演示确定性。代码已经把每步抽成独立函数，swap 成 LLM-driven 只需替换 `plan_iterative_retrieval()` |

---

## 11. 关键文件清单

| 文件 | 角色 | Phase |
|------|------|-------|
| `backend/app/models/schemas.py` | 全部新增 Pydantic 契约（RetrievalPlan、CascadeStage、IterativeTrace） | 17/19/21 |
| `backend/app/models/events.py` | SSE 事件追加 plan/cascade_trace/iterative_trace 字段 | 17/19/21 |
| `backend/app/core/agent/query_ontology.py` | FlashText 本体匹配器 + stdlib fallback | 17 |
| `backend/app/core/agent/query_analysis.py` | analyze_query() + build_retrieval_plan() | 17 |
| `backend/app/core/agent/retrieval_planner.py` | 迭代检索规则规划 | 21 |
| `backend/app/core/agent/context_builder.py` | EvidencePack 去重 + 压缩 | 20 |
| `backend/app/core/agent/workflow.py` | run_retrieval_pipeline() 统一三条路径 | 19/20/21 |
| `backend/app/core/retrieval/router.py` | choose_route() | 18 |
| `backend/app/core/retrieval/filters.py` | build_metadata_filters() + apply_metadata_filters() | 18 |
| `backend/app/core/retrieval/hybrid.py` | HybridRetriever 主流程 + 层级下钻 | 18/19/22 |
| `backend/app/core/retrieval/trace.py` | rerank_trace() 辅助 | 19/20 |
| `backend/app/core/ingestion/chunker.py` | markdown heading 识别 + section_path | 22 |
| `backend/app/core/ingestion/corpus_importer.py` | 父子 chunk 关联 + child_ids | 22 |
| `backend/app/api/debug.py` | /api/debug/retrieval 暴露全部 trace | 19/21 |
| `backend/app/api/query.py` | /api/query SSE 追加 trace 字段 | 19/20/21 |

---

## 12. 数字说明体系健康

- **测试数量**：116 个测试全部通过
- **代码新增**：~1700 行（含规划文档）/ ~900 行（纯生产代码）
- **新增接口**：0 个（全部通过既有 `/api/query`、`/api/debug/retrieval` 暴露）
- **破坏性变更**：0 个（向后兼容）
- **新依赖**：2 个（`flashtext-i18n`、`dateparser`）

---

> 写完这一份，整个 v1.4 的"为什么、是什么、怎么做、怎么讲"就完整了。面试时按"问题→架构图→关键模块→工程亮点→未来扩展"这个结构展开即可。
