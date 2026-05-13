export type MessageStage = 'idle' | 'query' | 'retrieve' | 'rerank' | 'generate' | 'done';

export type DocType = '财报' | '研报' | '新闻';

export interface Document {
  id: string;
  title: string;
  type: DocType;
  source: string;
  score: number;
  contentSnippet?: string;
  isHigh?: boolean;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  stage?: MessageStage;
  queryRewrite?: string[];
  duration?: Record<MessageStage, number>;
  tokens?: number;
}
