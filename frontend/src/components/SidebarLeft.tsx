import { LibraryDocument } from '../types';

interface SidebarLeftProps {
  documents: LibraryDocument[];
  onSelectExample: (text: string) => void;
}

const EXAMPLES = [
  {
    label: '事实型',
    color: 'blue',
    question: '宁德时代 2024 年营业收入是多少？同比变化如何？',
  },
  {
    label: '分析型',
    color: 'orange',
    question: '根据交银国际研报，宁德时代 2026 年一季度业绩为什么被认为“超预期且盈利有韧性”？',
  },
  {
    label: '综合总结型',
    color: 'green',
    question: '结合宁德时代 2024 年年报和 2026 年交银国际研报，概括公司增长驱动和需要关注的压力。',
  },
];

const COLOR_CLASSES: Record<string, { border: string; badge: string }> = {
  blue: { border: 'hover:border-blue-300', badge: 'bg-blue-100 text-blue-700' },
  orange: { border: 'hover:border-orange-300', badge: 'bg-orange-100 text-orange-700' },
  purple: { border: 'hover:border-purple-300', badge: 'bg-purple-100 text-purple-700' },
  green: { border: 'hover:border-emerald-300', badge: 'bg-emerald-100 text-emerald-700' },
};

export function SidebarLeft({ documents, onSelectExample }: SidebarLeftProps) {
  const openDocument = (doc: LibraryDocument) => {
    window.open(doc.openUrl, '_blank', 'noopener,noreferrer');
  };

  return (
    <aside className="w-60 border-r border-slate-200 bg-white flex flex-col overflow-y-auto shrink-0">
      <div className="p-4 flex flex-col gap-6">
        <section>
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">示例问题</h2>
          <div className="space-y-3">
            {EXAMPLES.map(example => {
              const classes = COLOR_CLASSES[example.color];
              return (
                <div
                  key={example.label}
                  className={`p-3 text-xs border border-slate-100 bg-slate-50 rounded-lg cursor-pointer ${classes.border} transition-colors relative`}
                  onClick={() => onSelectExample(example.question)}
                >
                  <span className={`absolute -top-2 right-2 px-1.5 py-0.5 rounded text-[10px] font-semibold ${classes.badge}`}>{example.label}</span>
                  <p className="mt-1">{example.question}</p>
                </div>
              );
            })}
          </div>
        </section>
        <section>
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
            文档库 ({documents.length} 篇)
          </h2>
          <div className="space-y-2">
            {documents.map(doc => (
              <button
                key={doc.id}
                type="button"
                className="w-full text-left p-2 hover:bg-slate-50 rounded border-l-2 border-transparent hover:border-blue-500 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-200"
                onClick={() => openDocument(doc)}
                title={`打开文档：${doc.title}`}
              >
                <p className="text-xs font-medium truncate">{doc.title}</p>
                <p className="text-[10px] text-slate-500 truncate">{doc.type}{doc.company ? ` · ${doc.company}` : ''}</p>
              </button>
            ))}
            <div className="p-2 rounded border-l-2 border-transparent">
              <p className="text-xs font-medium truncate text-slate-400">⋯ 点击文档可打开详情</p>
              <p className="text-[10px] text-slate-400">—</p>
            </div>
          </div>
        </section>
      </div>
    </aside>
  );
}
