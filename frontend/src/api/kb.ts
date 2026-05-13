import { Document, KBStats, Task } from '../pages/knowledgeBaseTypes';

type KBOverviewResponse = {
  total_documents: number;
  total_chunks: number;
  last_import_at?: string | null;
  last_reindex_at?: string | null;
  status: 'ready' | 'importing' | 'failed' | 'not_initialized';
};

type KBDocumentResponse = {
  doc_id: string;
  title: string;
  company: string;
  doc_type: string;
  date: string;
  source?: string | null;
  source_path: string;
  chunk_count: number;
  status: 'active' | 'disabled' | 'failed';
  collection_name: string;
  error_message?: string | null;
  chunks?: Array<{ content: string }>;
};

type KBImportJobResponse = {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  success_count: number;
  fail_count: number;
  error_messages: string[];
  reindex_status: string;
  created_at: string;
  finished_at?: string | null;
};

export async function fetchKBStats(signal?: AbortSignal): Promise<KBStats> {
  const response = await fetch('/api/kb/overview', { signal });
  if (!response.ok) throw new Error('Failed to load KB overview');
  return mapStats(await response.json());
}

export async function fetchKBDocuments(query = '', signal?: AbortSignal): Promise<Document[]> {
  const params = new URLSearchParams({ page_size: '200' });
  if (query.trim()) params.set('q', query.trim());
  const response = await fetch(`/api/kb/documents?${params}`, { signal });
  if (!response.ok) throw new Error('Failed to load KB documents');
  const payload = await response.json();
  return payload.documents.map(mapDocument);
}

export async function fetchKBDocumentDetail(docId: string, signal?: AbortSignal): Promise<Document> {
  const response = await fetch(`/api/kb/documents/${encodeURIComponent(docId)}`, { signal });
  if (!response.ok) throw new Error('Failed to load KB document detail');
  return mapDocument(await response.json());
}

export async function uploadAndImportKnowledgeBase(input: { files: File[]; collectionName: string; defaultCompany: string; defaultDocType: string; rebuildIndex: boolean }): Promise<Task> {
  const form = new FormData();
  input.files.forEach(file => form.append('files', file));
  form.append('collection_name', input.collectionName);
  const uploadResponse = await fetch('/api/kb/upload', { method: 'POST', body: form });
  if (!uploadResponse.ok) throw new Error('Failed to upload files');
  const importResponse = await fetch('/api/kb/import', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      collection_name: input.collectionName,
      rebuild_index: input.rebuildIndex,
      default_company: input.defaultCompany || '未知',
      default_doc_type: input.defaultDocType,
    }),
  });
  if (!importResponse.ok) throw new Error('Failed to import files');
  return mapTask(await importResponse.json(), 'import');
}

export async function reindexKnowledgeBase(): Promise<Task> {
  const response = await fetch('/api/kb/reindex', { method: 'POST' });
  if (!response.ok) throw new Error('Failed to rebuild index');
  await response.json();
  return taskFromStatus('reindex', 'success');
}

export async function reimportDocument(docId: string): Promise<Task> {
  const response = await fetch(`/api/kb/documents/${encodeURIComponent(docId)}/reimport`, { method: 'POST' });
  if (!response.ok) throw new Error('Failed to reimport document');
  return mapTask(await response.json(), 'import');
}

export async function disableDocument(docId: string): Promise<void> {
  const response = await fetch(`/api/kb/documents/${encodeURIComponent(docId)}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to disable document');
}

function mapStats(payload: KBOverviewResponse): KBStats {
  return {
    documentCount: payload.total_documents,
    chunkCount: payload.total_chunks,
    lastImportTime: formatTime(payload.last_import_at),
    lastReindexTime: formatTime(payload.last_reindex_at),
    status: payload.status === 'ready' ? 'normal' : payload.status,
  };
}

function mapDocument(payload: KBDocumentResponse): Document {
  return {
    id: payload.doc_id,
    title: payload.title,
    company: payload.company,
    type: payload.doc_type,
    date: payload.date,
    source: payload.source ?? '',
    chunkCount: payload.chunk_count,
    status: payload.status === 'active' ? 'normal' : payload.status === 'disabled' ? 'not_initialized' : 'failed',
    metadata: payload,
    sourcePath: payload.source_path,
    chunkSummary: payload.chunks?.[0]?.content ?? '暂无 chunk 摘要',
    failureReason: payload.error_message ?? undefined,
    collectionName: payload.collection_name,
  };
}

function mapTask(payload: KBImportJobResponse, type: Task['type']): Task {
  return {
    id: payload.job_id,
    type,
    status: payload.status === 'completed' ? 'success' : payload.status === 'pending' ? 'pending' : payload.status,
    progress: payload.status === 'completed' ? 100 : payload.status === 'failed' ? 100 : 50,
    successCount: payload.success_count,
    failedCount: payload.fail_count,
    errorMessage: payload.error_messages.join('; ') || undefined,
    isIndexRebuilt: payload.reindex_status === 'completed',
    createdAt: formatTime(payload.created_at),
    updatedAt: formatTime(payload.finished_at ?? payload.created_at),
  };
}

function taskFromStatus(type: Task['type'], status: Task['status']): Task {
  const now = new Date().toLocaleString();
  return { id: `${type}-${Date.now()}`, type, status, progress: 100, successCount: 0, failedCount: 0, isIndexRebuilt: type === 'reindex', createdAt: now, updatedAt: now };
}

function formatTime(value?: string | null): string {
  return value ? new Date(value).toLocaleString() : '暂无';
}
