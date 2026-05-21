import { useState, useRef, useEffect } from 'react';
import clsx from 'clsx';
import { Document, RetrievalSnapshot } from '../types';
import { RagProcessInspector } from './RagProcessInspector';

interface SidebarRightProps {
  snapshot: RetrievalSnapshot;
  activeCitationId: string | null;
  activeSnapshotLabel?: string;
}

type PanelKey = 'bm25' | 'vector' | 'rerank';

export function SidebarRight({ snapshot, activeCitationId, activeSnapshotLabel }: SidebarRightProps) {
  const { bm25Docs, vectorDocs, rerankDocs, bm25Error, vectorError } = snapshot;
  const [openPanels, setOpenPanels] = useState<Record<PanelKey, boolean>>({
    bm25: false,
    vector: false,
    rerank: true,
  });

  useEffect(() => {
    if (activeCitationId) {
      setOpenPanels(previous => ({ ...previous, rerank: true }));
    }
  }, [activeCitationId]);

  const togglePanel = (panel: PanelKey) => {
    setOpenPanels(previous => ({ ...previous, [panel]: !previous[panel] }));
  };

  const isDocActive = (doc: Document) => Boolean(activeCitationId && doc.id === activeCitationId);
  const allClosed = !openPanels.bm25 && !openPanels.vector && !openPanels.rerank;

  return (
    <aside className="w-[340px] border-l border-slate-200 bg-slate-50 overflow-y-auto flex flex-col shrink-0">
      <div className="p-4 border-b border-slate-200 bg-white sticky top-0 z-10 flex items-center justify-between font-bold text-xs text-slate-500 uppercase tracking-tight">
        <div className="min-w-0">
          <div>检索过程可视化</div>
          {activeSnapshotLabel && <div className="mt-1 truncate text-[10px] font-medium text-slate-400 normal-case">{activeSnapshotLabel}</div>}
        </div>
        <span className="text-blue-600">LIVE</span>
      </div>
      <div className="p-3 space-y-4">
        <RagProcessInspector snapshot={snapshot} />

        <RetrievalPanel title="BM25 关键词召回 (Top 10)" open={openPanels.bm25} onToggle={() => togglePanel('bm25')} tone="neutral">
          {bm25Error ? <ErrorPanel text={bm25Error} /> : bm25Docs.length ? bm25Docs.map(doc => (
            <DocItem key={doc.id} doc={doc} isActive={isDocActive(doc)} maxScore={Math.max(1, ...bm25Docs.map(item => item.score))} type="bm25" />
          )) : <EmptyPanel text="暂无 BM25 召回结果" />}
        </RetrievalPanel>

        <RetrievalPanel title="Vector 语义召回 (Top 10)" open={openPanels.vector} onToggle={() => togglePanel('vector')} tone="neutral">
          {vectorError ? <ErrorPanel text={vectorError} /> : vectorDocs.length ? vectorDocs.map(doc => (
            <DocItem key={doc.id} doc={doc} isActive={isDocActive(doc)} maxScore={Math.max(1, ...vectorDocs.map(item => item.score))} type="vector" />
          )) : <EmptyPanel text="暂无 Vector 召回结果" />}
        </RetrievalPanel>

        <RetrievalPanel title={rerankDocs.some(doc => doc.degraded) ? '降级融合结果 (Top 5)' : 'Rerank 精排推荐 (Top 5)'} open={openPanels.rerank} onToggle={() => togglePanel('rerank')} tone="primary">
          {rerankDocs.length ? rerankDocs.map((doc, index) => (
            <RerankItem key={`${doc.id}-${index}`} idx={`[${index + 1}]`} doc={doc} isActive={isDocActive(doc)} />
          )) : <EmptyPanel text="暂无 Rerank 精排结果" />}
        </RetrievalPanel>

        {allClosed && (
          <div className="rounded-lg border border-dashed border-slate-300 bg-white p-4 text-xs text-slate-400 text-center">
            三个检索面板均已收起，可点击标题右侧箭头重新展开。
          </div>
        )}
      </div>
    </aside>
  );
}

function RetrievalPanel({ title, open, onToggle, tone, children }: { title: string; open: boolean; onToggle: () => void; tone: 'neutral' | 'primary'; children: React.ReactNode }) {
  const isPrimary = tone === 'primary';
  return (
    <div className={clsx('bg-white rounded-lg overflow-hidden shadow-sm', isPrimary ? 'border border-blue-500 shadow-md' : 'border border-slate-200')}>
      <button
        type="button"
        className={clsx(
          'w-full p-3 text-xs font-semibold flex items-center justify-between cursor-pointer transition-colors',
          isPrimary ? 'bg-blue-600 text-white hover:bg-blue-700' : open ? 'bg-blue-50 text-slate-900' : 'bg-slate-100 hover:bg-blue-50 text-slate-900'
        )}
        onClick={onToggle}
        aria-expanded={open}
      >
        <span>{title}</span>
        <svg className={clsx('w-4 h-4 transition-transform', open && 'rotate-180')} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 9l-7 7-7-7" /></svg>
      </button>
      {open && <div className="p-2 space-y-2 text-[11px]">{children}</div>}
    </div>
  );
}

function EmptyPanel({ text }: { text: string }) {
  return <div className="p-3 text-center text-slate-400">{text}</div>;
}

function ErrorPanel({ text }: { text: string }) {
  return <div className="p-3 rounded border border-amber-200 bg-amber-50 text-amber-700 leading-relaxed break-words">召回降级：{text}</div>;
}

function DocItem({ doc, isActive, maxScore, type }: { doc: Document; isActive: boolean; maxScore: number; type: 'bm25' | 'vector' }) {
  const percent = Math.min(100, Math.max(0, maxScore ? (doc.score / maxScore) * 100 : 0));

  return (
    <div className={clsx('p-2 border rounded transition-colors', isActive ? 'bg-white border-blue-400' : 'bg-white border-slate-100 hover:border-blue-300 opacity-80 hover:opacity-100')}>
      <div className="flex justify-between gap-2 mb-1 text-slate-500">
        <span className="truncate pr-2">{doc.title}</span>
        <span className="shrink-0">{type === 'bm25' ? 'Score' : 'Sim'}: {formatScore(doc.score)}</span>
      </div>
      <div className="w-full bg-slate-100 h-1 rounded overflow-hidden">
        <div className={clsx('h-full', type === 'bm25' ? 'bg-blue-400' : 'bg-teal-400')} style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

function RerankItem({ doc, idx, isActive }: { doc: Document; idx: string; isActive: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const cardRef = useRef<HTMLButtonElement>(null);
  const evidenceText = doc.fullContent || doc.contentSnippet || '暂无证据文本';
  const scoreLabel = doc.degraded || doc.scoreSource === 'hybrid_fusion'
    ? `融合 ${formatScore(doc.score)} · rerank 降级`
    : `Rerank ${formatScore(doc.score)}`;

  useEffect(() => {
    if (isActive && cardRef.current) {
      setExpanded(true);
      cardRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [isActive]);

  return (
    <button
      ref={cardRef}
      type="button"
      onClick={() => setExpanded(value => !value)}
      className={clsx(
        'w-full text-left p-3 rounded transition-colors cursor-pointer relative',
        isActive ? 'border-l-4 border-blue-500 bg-blue-50 shadow-sm' : 'border-l-4 border-slate-300 bg-white hover:bg-slate-50'
      )}
    >
      <div className={clsx('flex items-start justify-between gap-3 font-bold mb-1', isActive ? 'text-blue-800' : 'text-slate-700')}>
        <span>{idx}</span>
        <span className="shrink-0 tabular-nums text-right">{scoreLabel}</span>
      </div>
      <div className="font-bold text-slate-700 break-words leading-snug mb-2">{doc.title}</div>
      <p className={clsx('text-slate-600 leading-relaxed whitespace-pre-wrap', expanded ? '' : 'line-clamp-3')}>
        {evidenceText}
      </p>
      <div className="mt-2 text-[10px] text-blue-500 font-medium">{expanded ? '收起证据文本' : '展开具体引用文本'}</div>
    </button>
  );
}

function formatScore(score: number | undefined): string {
  if (typeof score !== 'number' || Number.isNaN(score)) return '—';
  return score.toFixed(2);
}
