export function Header({ onReset }: { onReset: () => void }) {
  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-slate-200 bg-white flex-shrink-0 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center text-white font-bold">F</div>
        <h1 className="font-semibold text-lg tracking-tight">FinRAG · 金融智能研究 Agent</h1>
      </div>
      <div className="flex gap-3">
        <button 
          onClick={onReset}
          className="px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-md border border-slate-200 cursor-pointer"
        >
          重置会话
        </button>
        <button className="px-3 py-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md cursor-pointer">
          关于
        </button>
      </div>
    </header>
  );
}
