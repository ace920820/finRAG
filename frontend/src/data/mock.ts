import { Document, DocType } from '../types';

export const mockLeftDocuments: Array<{ id: string; title: string; type: DocType }> = [
  { id: 'l1', title: '贵州茅台 2023 年报', type: '财报' },
  { id: 'l2', title: '宁德时代 2023 Q3', type: '财报' },
  { id: 'l3', title: '中信 · 白酒行业深度', type: '研报' },
  { id: 'l4', title: '国泰君安 · 锂电拐点', type: '研报' },
  { id: 'l5', title: 'FOMC 5 月会议纪要', type: '新闻' },
  { id: 'l6', title: '华泰 · 新能源车月报', type: '研报' },
  { id: 'l7', title: '茅台经销商座谈纪要', type: '新闻' },
  { id: 'l8', title: 'CATL 投资者活动记录', type: '新闻' },
];

export const mockBM25Docs: Document[] = [
  { id: 'b1', title: 'CATL 2023Q3 · 经营情况讨论', type: '财报', source: 'P.12 §3.2 · 2023-10-26', score: 28.41, isHigh: false },
  { id: 'b2', title: '国泰君安 · 锂电拐点确立', type: '研报', source: 'P.04 §1 · 2024-03-18', score: 24.92, isHigh: true },
  { id: 'b3', title: 'CATL 投资者活动纪要 5月', type: '新闻', source: '§Q&A · 2024-05-09', score: 20.13, isHigh: false },
  { id: 'b4', title: '华泰 · 新能源车 4 月销量点评', type: '研报', source: 'P.07 · 2024-05-12', score: 16.40, isHigh: false },
];

export const mockVectorDocs: Document[] = [
  { id: 'v1', title: '国泰君安 · 锂电拐点确立', type: '研报', source: 'P.04 §1 · 2024-03-18', score: 0.94, isHigh: true },
  { id: 'v2', title: 'CATL 2023Q3 · 经营情况讨论', type: '财报', source: 'P.12 §3.2 · 2023-10-26', score: 0.89, isHigh: false },
  { id: 'v3', title: '华泰 · 新能源车 4 月销量点评', type: '研报', source: 'P.07 · 2024-05-12', score: 0.82, isHigh: false },
  { id: 'v4', title: 'CATL 投资者活动纪要 5月', type: '新闻', source: '§Q&A · 2024-05-09', score: 0.77, isHigh: false },
];

export const mockRerankDocs: Document[] = [
  { 
    id: '1', 
    title: 'CATL 2023Q3 · 经营情况讨论', 
    type: '财报', 
    source: 'P.12 §3.2 · 2023-10-26', 
    score: 0.92,
    contentSnippet: '公司面临原材料价格大幅波动、海外产能爬坡进度不及预期、关键客户订单集中等多重经营风险，管理层已通过套期保值与多元化客户布局进行对冲⋯',
    isHigh: false 
  },
  { 
    id: '2', 
    title: '国泰君安 · 锂电拐点确立', 
    type: '研报', 
    source: 'P.04 §1 · 2024-03-18', 
    score: 0.88,
    contentSnippet: '宁德时代德国图林根工厂自 2023 年下半年量产以来，良率仍低于国内基线约 4–6 个百分点，主要由于设备调试与本地化供应链磨合周期较长。我们预计 2024 H2 才能逐步接近国内水平⋯',
    isHigh: true 
  },
  { 
    id: '3', 
    title: 'CATL 投资者活动纪要 5月', 
    type: '新闻', 
    source: '§Q&A · 2024-05-09', 
    score: 0.81,
    contentSnippet: '前五大客户占比 48.3%，公司正在积极拓展海外客户...',
    isHigh: false 
  },
  { 
    id: '4', 
    title: '华泰 · 新能源车 4 月销量点评', 
    type: '研报', 
    source: 'P.07 · 2024-05-12', 
    score: 0.76,
    contentSnippet: '钠电、半固态加速发展，需要警惕技术路线更替风险...',
    isHigh: false 
  },
  { 
    id: '5', 
    title: '中信 · 固态电池前瞻', 
    type: '研报', 
    source: 'P.10 · 2024-05-10', 
    score: 0.74,
    contentSnippet: '竞争对手在半固态和固态电池的技术上不断突破...',
    isHigh: false 
  },
];

export const mockAnswerStream = `#### 宁德时代 · 经营风险简评

综合 2023 Q3 财报与近期券商研报，潜在风险集中在以下四个维度：

* **原材料价格波动**：碳酸锂均价较年初下滑 <span class="text-blue-600 font-semibold font-mono">62%</span>，存货跌价压力上升 [1]
* **海外产能爬坡**：德国图林根工厂良率仍低于国内基线 [2]
* **大客户集中度**：前五大客户占比 <span class="text-blue-600 font-semibold font-mono">48.3%</span>，议价话语权下降 [3]
* **技术路线竞争**：钠电、半固态加速，面临技术迭代压力 [4][5]

综合来看：基本面已度过最差阶段，估值修复需关注 Q4 单 Wh 净利改善节奏。`;

export const mockKeywords = ['宁德时代', 'CATL', '300750', '锂电池', '经营风险'];
