export interface PreviewRewriteResponse {
  original: string;
  expanded_terms: string[];
  sub_queries: string[];
  detected_entities: string[];
  intent: 'factual' | 'analytical' | 'reasoning';
}

export async function fetchRewritePreview(query: string, signal?: AbortSignal): Promise<PreviewRewriteResponse> {
  const response = await fetch('/api/preview-rewrite', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
    signal,
  });
  if (!response.ok) {
    throw new Error(`预览请求失败：${response.status}`);
  }
  return (await response.json()) as PreviewRewriteResponse;
}

export function formatPreviewKeywords(payload: PreviewRewriteResponse | null): string {
  if (!payload) return '';
  const keywords = [...payload.expanded_terms, ...payload.detected_entities];
  return Array.from(new Set(keywords)).filter(Boolean).join('、');
}
