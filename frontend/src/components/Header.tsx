export function Header({ onReset, onOpenKnowledgeBase }: { onReset: () => void; onOpenKnowledgeBase: () => void }) {
  return (
    <header className="h-16 flex items-center justify-between px-6 border-b border-slate-200 bg-white flex-shrink-0 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-xl">F</div>
        <h1 className="text-xl font-semibold tracking-tight">FinRAG · 金融智能研究系统</h1>
      </div>
      <div className="flex items-center gap-4">
        <button
          onClick={onOpenKnowledgeBase}
          className="px-4 py-2 text-sm font-medium text-blue-700 hover:bg-blue-50 rounded-md border border-blue-200 cursor-pointer transition-colors"
        >
          知识库管理
        </button>
        <button 
          onClick={onReset}
          className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 rounded-md border border-slate-200 cursor-pointer transition-colors"
        >
          重置会话
        </button>
        <button className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md cursor-pointer transition-colors">
          关于
        </button>
      </div>
    </header>
  );
}
