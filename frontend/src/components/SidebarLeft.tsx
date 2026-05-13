import { DocType } from '../types';
import { mockLeftDocuments } from '../data/mock';

interface SidebarLeftProps {
  onSelectExample: (text: string) => void;
}

export function SidebarLeft({ onSelectExample }: SidebarLeftProps) {
  return (
    <aside className="w-60 border-r border-slate-200 bg-white flex flex-col overflow-y-auto shrink-0">
      <div className="p-4 flex flex-col gap-6">
        <section>
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">示例问题</h2>
          <div className="space-y-3">
            <div 
              className="p-3 text-xs border border-slate-100 bg-slate-50 rounded-lg cursor-pointer hover:border-blue-300 transition-colors relative"
              onClick={() => onSelectExample('贵州茅台 2023 年营业收入是多少？同比增长率？')}
            >
              <span className="absolute -top-2 right-2 px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px] font-semibold">事实型</span>
              <p className="mt-1">贵州茅台 2023 年营业收入是多少？同比增长率？</p>
            </div>
            <div 
              className="p-3 text-xs border border-slate-100 bg-slate-50 rounded-lg cursor-pointer hover:border-orange-300 transition-colors relative"
              onClick={() => onSelectExample('宁德时代近期有哪些潜在经营风险？')}
            >
              <span className="absolute -top-2 right-2 px-1.5 py-0.5 bg-orange-100 text-orange-700 rounded text-[10px] font-semibold">分析型</span>
              <p className="mt-1">宁德时代近期有哪些潜在经营风险？</p>
            </div>
            <div 
              className="p-3 text-xs border border-slate-100 bg-slate-50 rounded-lg cursor-pointer hover:border-purple-300 transition-colors relative"
              onClick={() => onSelectExample('美联储加息对 A 股新能源板块可能产生什么影响？')}
            >
              <span className="absolute -top-2 right-2 px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded text-[10px] font-semibold">推理型</span>
              <p className="mt-1">美联储加息对 A 股新能源板块可能产生什么影响？</p>
            </div>
          </div>
        </section>
        <section>
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
            文档库 ({mockLeftDocuments.length} 篇)
          </h2>
          <div className="space-y-2">
            {mockLeftDocuments.map(doc => (
              <div key={doc.id} className="p-2 hover:bg-slate-50 rounded border-l-2 border-transparent hover:border-blue-500 cursor-default">
                <p className="text-xs font-medium truncate">{doc.title}</p>
                <p className="text-[10px] text-slate-500">{doc.type}</p>
              </div>
            ))}
            <div className="p-2 hover:bg-slate-50 rounded border-l-2 border-transparent hover:border-blue-500 cursor-default">
              <p className="text-xs font-medium truncate">⋯ 仅展示 · 不可编辑</p>
              <p className="text-[10px] text-slate-500">—</p>
            </div>
          </div>
        </section>
      </div>
    </aside>
  );
}
