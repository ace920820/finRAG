import { LibraryDocument } from '../types';

interface SidebarLeftProps {
  documents: LibraryDocument[];
  onSelectExample: (text: string) => void;
}

const EXAMPLES = [
  {
    label: '事实型',
    color: 'blue',
    question: '英伟达 FY2026Q3 最近一个季度总营收是多少？数据中心业务贡献多少？',
  },
  {
    label: '分析型',
    color: 'orange',
    question: '宁德时代和贵州茅台近期经营表现分别有哪些值得关注的风险和亮点？',
  },
  {
    label: '推理型',
    color: 'purple',
    question: '结合台积电先进制程与英伟达数据中心需求，AI 算力链条对两家公司业绩可能产生什么影响？',
  },
];

const COLOR_CLASSES: Record<string, { border: string; badge: string }> = {
  blue: { border: 'hover:border-blue-300', badge: 'bg-blue-100 text-blue-700' },
  orange: { border: 'hover:border-orange-300', badge: 'bg-orange-100 text-orange-700' },
  purple: { border: 'hover:border-purple-300', badge: 'bg-purple-100 text-purple-700' },
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
