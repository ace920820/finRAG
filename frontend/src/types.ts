import { IntentDetectedPayload, IterativeRetrievalTrace, MetadataRecord, RetrievalCascadeStage, RetrievalPlan } from './api/finrag';

export type MessageStage = 'idle' | 'query' | 'retrieve' | 'rerank' | 'generate' | 'done';

export type DocType = '财报' | '研报' | '新闻';

export interface Document {
  id: string;
  title: string;
  type: DocType;
  source: string;
  score: number;
  scoreSource?: 'rerank' | 'hybrid_fusion' | 'mock';
  degraded?: boolean;
  fallbackReason?: string;
  contentSnippet?: string;
  fullContent?: string;
  metadata?: MetadataRecord;
  isHigh?: boolean;
}

export interface LibraryDocument {
  id: string;
  title: string;
  type: DocType;
  openUrl: string;
  company?: string;
  date?: string;
}

export interface RetrievalSnapshot {
  bm25Docs: Document[];
  vectorDocs: Document[];
  rerankDocs: Document[];
  queryPlan?: RetrievalPlan | null;
  expandedTerms?: string[];
  subQueries?: string[];
  intent?: IntentDetectedPayload | null;
  retrievalCascade?: RetrievalCascadeStage[];
  rerankCascade?: RetrievalCascadeStage[];
  iterativeTrace?: IterativeRetrievalTrace | null;
  bm25Error?: string | null;
  vectorError?: string | null;
  citations?: Record<string, unknown>;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  stage?: MessageStage;
  queryRewrite?: string[];
  duration?: Record<MessageStage, number>;
  tokens?: number;
  retrievalSnapshot?: RetrievalSnapshot;
}
