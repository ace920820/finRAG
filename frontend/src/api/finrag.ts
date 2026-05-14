import { Document, DocType, LibraryDocument } from '../types';

export type BackendDocType = 'financial_report' | 'research_report' | 'news';
export type QueryIntent = 'factual' | 'analytical' | 'reasoning';

export interface BackendDocumentListItem {
  doc_id: string;
  title: string;
  doc_type: BackendDocType;
  company: string;
  date: string;
  chunk_count: number;
  source?: string | null;
}

export interface BackendDocumentListResponse {
  total: number;
  documents: BackendDocumentListItem[];
}

export interface BackendRetrievalResultItem {
  chunk_id: string;
  title: string;
  doc_type: BackendDocType;
  company: string;
  date: string;
  page: number | null;
  preview: string;
  score: number;
}

export interface BackendRerankResultItem {
  chunk_id: string;
  rank: number;
  rerank_score: number | null;
  relevance_score?: number | null;
  fusion_score?: number | null;
  degraded: boolean;
  fallback_reason?: string | null;
  score_source: 'rerank' | 'hybrid_fusion' | 'mock';
  title: string;
  doc_type: BackendDocType;
  company: string;
  date: string;
  page: number | null;
  content: string;
  citation_id: number;
}

export interface QueryRewritePayload {
  original: string;
  expanded: string[];
  sub_queries: string[];
}

export interface IntentDetectedPayload {
  intent: QueryIntent;
  template: string;
}

export interface RetrievalCompletePayload {
  bm25_results: BackendRetrievalResultItem[];
  vector_results: BackendRetrievalResultItem[];
  fused_top20: BackendRetrievalResultItem[];
}

export interface RerankCompletePayload {
  top5: BackendRerankResultItem[];
  degraded: boolean;
  fallback_reason?: string | null;
  score_source: 'rerank' | 'hybrid_fusion' | 'mock';
}

export interface AnswerChunkPayload {
  text: string;
  is_final: boolean;
}

export interface CitationMetadata {
  chunk_id: string;
  title: string;
  doc_type: BackendDocType;
  company: string;
  date: string;
  page: number | null;
  source?: string | null;
  section?: string | null;
}

export interface DonePayload {
  latency_ms: number;
  total_tokens: number;
  citations: Record<string, CitationMetadata>;
}

export interface ErrorPayload {
  code: string;
  message: string;
}

export interface StreamQueryHandlers {
  onQueryRewrite?: (payload: QueryRewritePayload) => void;
  onIntentDetected?: (payload: IntentDetectedPayload) => void;
  onRetrievalComplete?: (payload: RetrievalCompletePayload) => void;
  onRerankComplete?: (payload: RerankCompletePayload) => void;
  onAnswerChunk?: (payload: AnswerChunkPayload) => void;
  onDone?: (payload: DonePayload) => void;
  onError?: (payload: ErrorPayload) => void;
  onPing?: () => void;
}

interface SseEvent {
  event: string;
  data: unknown;
}

const DOC_TYPE_MAP: Record<BackendDocType, DocType> = {
  financial_report: '财报',
  research_report: '研报',
  news: '新闻',
};

export async function fetchDocuments(signal?: AbortSignal): Promise<LibraryDocument[]> {
  const response = await fetch('/api/documents', { signal });
  if (!response.ok) {
    throw new Error(`文档列表加载失败：${response.status}`);
  }
  const payload = (await response.json()) as BackendDocumentListResponse;
  return payload.documents.map(mapDocumentListItem);
}

export async function streamQuery(query: string, handlers: StreamQueryHandlers, signal?: AbortSignal): Promise<void> {
  const response = await fetch('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
    signal,
  });
  if (!response.ok) {
    throw new Error(`查询请求失败：${response.status}`);
  }
  if (!response.body) {
    throw new Error('当前浏览器不支持流式响应');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parsed = drainSseBuffer(buffer);
    buffer = parsed.remaining;
    parsed.events.forEach(event => dispatchSseEvent(event, handlers));
  }

  buffer += decoder.decode();
  const parsed = drainSseBuffer(buffer, true);
  parsed.events.forEach(event => dispatchSseEvent(event, handlers));
}

export function mapRetrievalResults(items: BackendRetrievalResultItem[]): Document[] {
  // RRF-fused scores are typically small reciprocal-rank sums (~0.01-0.05),
  // so a fixed score threshold rarely triggers. Mark the top 2 by rank instead.
  return items.map((item, index) => ({
    id: item.chunk_id,
    title: item.title,
    type: mapDocType(item.doc_type),
    source: formatSource(item.page, item.date, item.company),
    score: item.score,
    contentSnippet: item.preview,
    isHigh: index < 2,
  }));
}

export function mapRerankResults(items: BackendRerankResultItem[]): Document[] {
  return items.map(item => ({
    id: String(item.citation_id),
    title: item.title,
    type: mapDocType(item.doc_type),
    source: formatSource(item.page, item.date, item.company),
    score: item.score_source === 'hybrid_fusion' ? item.fusion_score ?? 0 : item.rerank_score ?? item.relevance_score ?? 0,
    scoreSource: item.score_source,
    degraded: item.degraded,
    fallbackReason: item.fallback_reason ?? undefined,
    contentSnippet: item.content,
    isHigh: item.rank <= 2,
  }));
}

export function mapDocType(docType: BackendDocType): DocType {
  return DOC_TYPE_MAP[docType] ?? '新闻';
}

function mapDocumentListItem(item: BackendDocumentListItem): LibraryDocument {
  return {
    id: item.doc_id,
    title: item.title,
    type: mapDocType(item.doc_type),
    company: item.company,
    date: item.date,
    openUrl: `/api/documents/${encodeURIComponent(item.doc_id)}/view`,
  };
}

function formatSource(page: number | null, date: string, company: string): string {
  const pageText = page ? `P.${page}` : '片段';
  return `${pageText} · ${company} · ${date}`;
}

function drainSseBuffer(buffer: string, flush = false): { events: SseEvent[]; remaining: string } {
  const events: SseEvent[] = [];
  const normalized = buffer.replace(/\r\n/g, '\n');
  const frames = normalized.split('\n\n');
  const completeFrames = flush ? frames : frames.slice(0, -1);
  const remaining = flush ? '' : frames[frames.length - 1];

  completeFrames.forEach(frame => {
    const event = parseSseFrame(frame);
    if (event) events.push(event);
  });

  return { events, remaining };
}

function parseSseFrame(frame: string): SseEvent | null {
  const lines = frame.split('\n').filter(Boolean);
  let event = 'message';
  const dataLines: string[] = [];

  lines.forEach(line => {
    if (line.startsWith('event:')) {
      event = line.slice('event:'.length).trim();
    }
    if (line.startsWith('data:')) {
      dataLines.push(line.slice('data:'.length).trim());
    }
  });

  if (!dataLines.length) return null;
  const dataText = dataLines.join('\n');
  try {
    return { event, data: JSON.parse(dataText) };
  } catch {
    return { event, data: dataText };
  }
}

function dispatchSseEvent({ event, data }: SseEvent, handlers: StreamQueryHandlers): void {
  switch (event) {
    case 'query_rewrite':
      handlers.onQueryRewrite?.(data as QueryRewritePayload);
      break;
    case 'intent_detected':
      handlers.onIntentDetected?.(data as IntentDetectedPayload);
      break;
    case 'retrieval_complete':
      handlers.onRetrievalComplete?.(data as RetrievalCompletePayload);
      break;
    case 'rerank_complete':
      handlers.onRerankComplete?.(data as RerankCompletePayload);
      break;
    case 'answer_chunk':
      handlers.onAnswerChunk?.(data as AnswerChunkPayload);
      break;
    case 'done':
      handlers.onDone?.(data as DonePayload);
      break;
    case 'error':
      handlers.onError?.(data as ErrorPayload);
      break;
    case 'ping':
      handlers.onPing?.();
      break;
    default:
      break;
  }
}
