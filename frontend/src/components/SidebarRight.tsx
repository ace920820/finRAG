import { useState, useRef, useEffect } from 'react';
import clsx from 'clsx';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { Document } from '../types';

interface SidebarRightProps {
  bm25Docs: Document[];
  vectorDocs: Document[];
  rerankDocs: Document[];
  activeCitationId: string | null;
}

export function SidebarRight({ bm25Docs, vectorDocs, rerankDocs, activeCitationId }: SidebarRightProps) {
  const [openPanel, setOpenPanel] = useState<'bm25' | 'vector' | 'rerank'>('bm25');
  const [expandedDocIdx, setExpandedDocIdx] = useState<string | null>(null);

  // When a citation is clicked, automatically open the rerank panel 
  // since that contains the actual cited docs usually
  useEffect(() => {
    if (activeCitationId) {
      setOpenPanel('rerank');
    }
  }, [activeCitationId]);

  const isDocActive = (doc: Document) => {
    if (!activeCitationId) return false;
    return doc.id === activeCitationId;
  };

  return (
    <aside className="w-[340px] border-l border-slate-200 bg-slate-50 overflow-y-auto flex flex-col shrink-0">
      <div className="p-4 border-b border-slate-200 bg-white sticky top-0 z-10 flex items-center justify-between font-bold text-xs text-slate-500 uppercase tracking-tight">
        <span>检索过程可视化</span>
        <span className="text-blue-600">LIVE</span>
      </div>
      <div className="p-3 space-y-4">
        
        {/* Panel 1: BM25 */}
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-sm">
          <div 
            className={clsx("p-3 text-xs font-semibold flex items-center justify-between cursor-pointer", openPanel === 'bm25' ? "bg-blue-50" : "bg-slate-100 hover:bg-blue-50")} 
            onClick={() => setOpenPanel('bm25')}
          >
            <span>BM25 关键词召回 (Top 10)</span>
            <svg className={clsx("w-4 h-4 transition-transform", openPanel === 'bm25' && "rotate-180")} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 9l-7 7-7-7"/></svg>
          </div>
          {openPanel === 'bm25' && (
            <div className="p-2 space-y-2 text-[11px]">
              {bm25Docs.map((doc) => (
                <DocItem key={doc.id} doc={doc} isActive={isDocActive(doc)} maxScore={30} type="bm25" />
              ))}
            </div>
          )}
        </div>

        {/* Panel 2: Vector */}
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-sm">
          <div 
            className={clsx("p-3 text-xs font-semibold flex items-center justify-between cursor-pointer", openPanel === 'vector' ? "bg-blue-50" : "bg-slate-100 hover:bg-blue-50")} 
            onClick={() => setOpenPanel('vector')}
          >
            <span>Vector 语义召回 (Top 10)</span>
            <svg className={clsx("w-4 h-4 transition-transform", openPanel === 'vector' && "rotate-180")} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 9l-7 7-7-7"/></svg>
          </div>
          {openPanel === 'vector' && (
            <div className="p-2 space-y-2 text-[11px]">
              {vectorDocs.map((doc) => (
                <DocItem key={doc.id} doc={doc} isActive={isDocActive(doc)} maxScore={1} type="vector" />
              ))}
            </div>
          )}
        </div>

        {/* Panel 3: Rerank */}
        <div className="bg-white rounded-lg border border-blue-500 overflow-hidden shadow-md">
          <div 
            className="p-3 text-xs font-semibold flex items-center justify-between cursor-pointer bg-blue-600 text-white"
            onClick={() => setOpenPanel('rerank')}
          >
            <span>Rerank 精排推荐 (Top 5)</span>
            <svg className={clsx("w-4 h-4 transition-transform", openPanel === 'rerank' && "rotate-180")} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 9l-7 7-7-7"/></svg>
          </div>
          {openPanel === 'rerank' && (
            <div className="p-2 space-y-2 text-[11px]">
              {rerankDocs.map((doc, i) => (
                <RerankItem 
                  key={doc.id} 
                  idx={`[${i+1}]`} 
                  doc={doc} 
                  isActive={isDocActive(doc)}
                />
              ))}
            </div>
          )}
        </div>

      </div>
    </aside>
  );
}

function DocItem({ doc, isActive, maxScore, type }: { doc: Document, isActive: boolean, maxScore: number, type: 'bm25'|'vector' }) {
  const percent = Math.min(100, Math.max(0, (doc.score / maxScore) * 100));
  
  return (
    <div className={clsx("p-2 border rounded transition-colors", isActive ? "bg-white border-blue-400" : "bg-white border-slate-100 hover:border-blue-300 opacity-80 hover:opacity-100")}>
      <div className="flex justify-between mb-1 text-slate-500">
        <span className="truncate pr-2">{doc.title}</span>
        <span>{type === 'bm25' ? 'Score' : 'Sim'}: {doc.score.toFixed(2)}</span>
      </div>
      <div className="w-full bg-slate-100 h-1 rounded overflow-hidden">
        <div className={clsx("h-full", type === 'bm25' ? "bg-blue-400" : "bg-teal-400")} style={{ width: `${percent}%` }}></div>
      </div>
    </div>
  );
}

function RerankItem({ doc, idx, isActive }: { doc: Document, idx: string, isActive: boolean }) {
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isActive && cardRef.current) {
      cardRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [isActive]);

  return (
    <div 
      ref={cardRef}
      className={clsx(
        "p-3 rounded transition-colors cursor-pointer relative",
        isActive ? "border-l-4 border-blue-500 bg-blue-50 shadow-sm" : "border-l-4 border-slate-300 bg-white hover:bg-slate-50"
      )}
    >
      <div className={clsx("flex justify-between font-bold mb-1", isActive ? "text-blue-800" : "text-slate-700")}>
        <span>{idx} {doc.title}</span>
        <span>{doc.score.toFixed(2)}</span>
      </div>
      {doc.contentSnippet && (
        <p className="text-slate-600 line-clamp-3 leading-relaxed mt-1">{doc.contentSnippet}</p>
      )}
    </div>
  );
}
