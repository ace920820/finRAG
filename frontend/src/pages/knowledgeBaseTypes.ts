export type DocStatus = 'normal' | 'importing' | 'failed' | 'not_initialized';
export type TaskStatus = 'pending' | 'running' | 'success' | 'failed';

export interface Document {
  id: string;
  title: string;
  company: string;
  type: string;
  date: string;
  source: string;
  chunkCount: number;
  status: DocStatus;
  metadata: Record<string, any>;
  sourcePath: string;
  chunkSummary: string;
  failureReason?: string;
  collectionName: string;
}

export interface Task {
  id: string;
  type: 'import' | 'reindex';
  status: TaskStatus;
  progress: number; // 0-100
  successCount: number;
  failedCount: number;
  errorMessage?: string;
  isIndexRebuilt: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface KBStats {
  documentCount: number;
  chunkCount: number;
  lastImportTime: string;
  lastReindexTime: string;
  status: DocStatus;
}
