import { useEffect, useState, type ReactNode } from 'react';
import { 
  FileText, 
  Layers, 
  Clock, 
  RefreshCw, 
  Activity, 
  Search, 
  Filter, 
  Upload, 
  Database, 
  ChevronRight, 
  AlertCircle,
  CheckCircle2,
  XCircle,
  Trash2,
  MoreVertical,
  Settings,
  X,
  Info,
  ChevronDown,
  RotateCw,
  SlidersHorizontal
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { Document, Task, KBStats, DocStatus } from './knowledgeBaseTypes';
import { disableDocument, fetchKBDocumentDetail, fetchKBDocuments, fetchKBStats, reimportDocument, reindexKnowledgeBase, uploadAndImportKnowledgeBase } from '../api/kb';

// Mock Data
const MOCK_STATS: KBStats = {
  documentCount: 42,
  chunkCount: 1250,
  lastImportTime: '2024-05-13 10:30',
  lastReindexTime: '2024-05-13 11:00',
  status: 'normal'
};

const MOCK_DOCS: Document[] = [
  {
    id: '1',
    title: '300750SZ catl annual report 2023',
    company: 'CATL',
    type: 'Annual Report',
    date: '2024-03-15',
    source: 'Official Site',
    chunkCount: 120,
    status: 'normal',
    collectionName: 'financial_reports',
    sourcePath: '/raw/reports/catl_2023.pdf',
    chunkSummary: 'Comprehensive annual financial performance, battery technology roadmap, and market share analysis for 2023.',
    metadata: { author: 'Finance Dept', pages: 156 }
  },
  {
    id: '2',
    title: 'Nvidia Q3 FY2026 Earnings',
    company: 'NVIDIA',
    type: 'Earnings Release',
    date: '2024-11-19',
    source: 'Investor Relations',
    chunkCount: 45,
    status: 'importing',
    collectionName: 'news_earnings',
    sourcePath: '/raw/earnings/nvda_q3_2026.pdf',
    chunkSummary: 'Quarterly financial results highlighting Data Center revenue growth and AI chip demand.',
    metadata: { ticker: 'NVDA', quarter: 'Q3' }
  },
  {
    id: '3',
    title: 'Apple Sustainability Report 2024',
    company: 'Apple',
    type: 'Sustainability',
    date: '2024-04-20',
    source: 'ESG Portal',
    chunkCount: 0,
    status: 'failed',
    collectionName: 'esg_data',
    sourcePath: '/raw/esg/apple_esg_2024.pdf',
    chunkSummary: 'Environmental impact and social responsibility initiatives.',
    failureReason: 'PDF parsing encoding error at page 42.',
    metadata: { focus: 'Carbon Neutrality' }
  }
];

const MOCK_TASKS: Task[] = [
  {
    id: 'TASK-001',
    type: 'import',
    status: 'success',
    progress: 100,
    successCount: 12,
    failedCount: 1,
    isIndexRebuilt: true,
    createdAt: '2024-05-13 09:00',
    updatedAt: '2024-05-13 09:30'
  }
];

export function KnowledgeBaseManager({ onBackToChat }: { onBackToChat: () => void }) {
  const [activeTab, setActiveTab] = useState<'overview' | 'docs' | 'tasks'>('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [stats, setStats] = useState<KBStats>(MOCK_STATS);
  const [docs, setDocs] = useState<Document[]>(MOCK_DOCS);
  const [tasks, setTasks] = useState<Task[]>(MOCK_TASKS);
  const [apiError, setApiError] = useState<string | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [collectionName, setCollectionName] = useState('financial_reports');
  const [defaultDocType, setDefaultDocType] = useState('research_report');
  const [defaultCompany, setDefaultCompany] = useState('');
  const [rebuildAfterImport, setRebuildAfterImport] = useState(true);

  const loadData = async (query = searchTerm) => {
    try {
      const [nextStats, nextDocs] = await Promise.all([fetchKBStats(), fetchKBDocuments(query)]);
      setStats(nextStats);
      setDocs(nextDocs);
      setApiError(null);
    } catch (error) {
      setApiError(error instanceof Error ? error.message : '知识库接口连接失败，正在展示示例数据');
    }
  };

  useEffect(() => {
    void loadData('');
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadData(searchTerm);
    }, 300);
    return () => window.clearTimeout(timer);
  }, [searchTerm]);

  const getStatusIcon = (status: DocStatus) => {
    switch (status) {
      case 'normal': return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
      case 'importing': return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'failed': return <XCircle className="w-4 h-4 text-rose-500" />;
      default: return <AlertCircle className="w-4 h-4 text-slate-400" />;
    }
  };

  const handleReindex = async () => {
    try {
      const task = await reindexKnowledgeBase();
      setTasks(prev => [task, ...prev]);
      await loadData();
    } catch (error) {
      setApiError(error instanceof Error ? error.message : '索引重建失败');
    }
  };

  const handleSelectDoc = async (doc: Document) => {
    setSelectedDoc(doc);
    try {
      setSelectedDoc(await fetchKBDocumentDetail(doc.id));
      setApiError(null);
    } catch {
      setSelectedDoc(doc);
    }
  };

  const handleReimportDoc = async (doc: Document) => {
    try {
      const task = await reimportDocument(doc.id);
      setTasks(prev => [task, ...prev]);
      setSelectedDoc(null);
      await loadData();
    } catch (error) {
      setApiError(error instanceof Error ? error.message : '重新导入失败');
    }
  };

  const handleDisableDoc = async (doc: Document) => {
    try {
      await disableDocument(doc.id);
      setDocs(prev => prev.filter(item => item.id !== doc.id));
      setSelectedDoc(null);
    } catch (error) {
      setApiError(error instanceof Error ? error.message : '删除文档失败');
    }
  };

  const handleUploadAndImport = async () => {
    if (!selectedFiles.length) {
      setApiError('请先选择要导入的文件');
      return;
    }
    try {
      const task = await uploadAndImportKnowledgeBase({ files: selectedFiles, collectionName, defaultCompany, defaultDocType, rebuildIndex: rebuildAfterImport });
      setTasks(prev => [task, ...prev]);
      setSelectedFiles([]);
      setIsImportModalOpen(false);
      await loadData();
    } catch (error) {
      setApiError(error instanceof Error ? error.message : '资料导入失败');
    }
  };

  const getStatusText = (status: DocStatus) => {
    switch (status) {
      case 'normal': return '正常';
      case 'importing': return '导入中';
      case 'failed': return '失败';
      default: return '未初始化';
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Header */}
      <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-10 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-xl">F</div>
          <h1 className="text-xl font-semibold tracking-tight">FinRAG · 知识库管理</h1>
        </div>
        <div className="flex items-center gap-4">
          <button 
            onClick={() => setActiveTab('docs')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'docs' ? 'bg-blue-50 text-blue-600' : 'text-slate-600 hover:bg-slate-50'}`}
          >
            文档管理
          </button>
          <button 
             onClick={() => setActiveTab('tasks')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'tasks' ? 'bg-blue-50 text-blue-600' : 'text-slate-600 hover:bg-slate-50'}`}
          >
            任务状态
          </button>
          <button
            onClick={() => setIsSettingsModalOpen(true)}
            className="px-4 py-2 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors flex items-center gap-2"
          >
            <Settings className="w-4 h-4" />
            设置
          </button>
          <button
            onClick={onBackToChat}
            className="px-4 py-2 rounded-md text-sm font-medium text-blue-700 hover:bg-blue-50 border border-blue-200 transition-colors"
          >
            返回对话
          </button>
        </div>
      </header>

      <main className="p-6 max-w-7xl mx-auto space-y-8">
        {apiError && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800">
            {apiError}
          </div>
        )}
        {/* F-1 Overview Section */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between group">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-500 text-sm font-medium">文档总数</span>
              <FileText className="w-5 h-5 text-blue-600 opacity-80" />
            </div>
            <div className="text-2xl font-bold">{stats.documentCount}</div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between group">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-500 text-sm font-medium">Chunk 总数</span>
              <Layers className="w-5 h-5 text-indigo-600 opacity-80" />
            </div>
            <div className="text-2xl font-bold">{stats.chunkCount}</div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between group">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-500 text-sm font-medium">最近导入</span>
              <Clock className="w-5 h-5 text-emerald-600 opacity-80" />
            </div>
            <div className="text-sm font-semibold">{stats.lastImportTime}</div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between group">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-500 text-sm font-medium">最近索引重建</span>
              <RefreshCw className="w-5 h-5 text-amber-600 opacity-80" />
            </div>
            <div className="text-sm font-semibold">{stats.lastReindexTime}</div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between group">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-500 text-sm font-medium">当前状态</span>
              <Activity className="w-5 h-5 text-slate-600 opacity-80" />
            </div>
            <div className="flex items-center gap-2">
              {getStatusIcon(stats.status)}
              <span className="text-sm font-bold">{getStatusText(stats.status)}</span>
            </div>
          </div>
        </section>

        {/* F-2 Document List Section */}
        {activeTab === 'docs' && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
              <div className="relative w-full md:w-96">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input 
                  type="text" 
                  placeholder="搜索文档标题、公司..." 
                  className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm transition-all shadow-sm"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              <div className="flex items-center gap-3 w-full md:w-auto">
                <div className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-600 cursor-pointer hover:bg-slate-50 transition-colors shadow-sm">
                  <Filter className="w-4 h-4" />
                  <span>筛选器</span>
                </div>
                <button
                  type="button"
                  onClick={() => void handleReindex()}
                  className="flex-1 md:flex-none px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors shadow-sm flex items-center justify-center gap-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  重建索引
                </button>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200">
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">文档标题</th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">公司</th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">类型</th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Chunk</th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">状态</th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-sm">
                    {docs.map((doc) => (
                      <tr 
                        key={doc.id} 
                        className="hover:bg-slate-50/50 transition-colors cursor-pointer group"
                        onClick={() => void handleSelectDoc(doc)}
                      >
                        <td className="px-6 py-4">
                          <div className="flex flex-col">
                            <span className="font-semibold text-slate-700 group-hover:text-blue-600 transition-colors">{doc.title}</span>
                            <span className="text-xs text-slate-400 mt-0.5">{doc.source} · {doc.date}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-slate-600">{doc.company}</td>
                        <td className="px-6 py-4">
                          <span className="px-2 py-1 bg-slate-100 text-slate-600 rounded text-[10px] font-bold uppercase">
                            {doc.type}
                          </span>
                        </td>
                        <td className="px-6 py-4 font-mono text-slate-500">{doc.chunkCount}</td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(doc.status)}
                            <span className="text-xs font-medium">{getStatusText(doc.status)}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <button className="p-1 hover:bg-slate-200 rounded transition-colors">
                            <MoreVertical className="w-4 h-4 text-slate-400" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </motion.div>
        )}

        {/* F-7 Task Status Section */}
        {activeTab === 'tasks' && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="grid gap-4">
              {tasks.map((task) => (
                <div key={task.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className={`p-3 rounded-lg ${task.status === 'success' ? 'bg-emerald-50 text-emerald-600' : 'bg-blue-50 text-blue-600'}`}>
                      {task.type === 'import' ? <Upload className="w-6 h-6" /> : <RefreshCw className="w-6 h-6" />}
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-bold text-slate-700">#{task.id}</span>
                        <span className={`text-[10px] uppercase font-black px-1.5 py-0.5 rounded ${task.status === 'success' ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700'}`}>
                          {task.status === 'success' ? '已完成' : '进行中'}
                        </span>
                      </div>
                      <p className="text-sm text-slate-500 mb-3">创建于 {task.createdAt}</p>
                      <div className="flex items-center gap-6 text-sm">
                        <div className="flex items-center gap-1.5">
                          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                          <span className="text-slate-600">成功: <span className="font-bold">{task.successCount}</span></span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <XCircle className="w-4 h-4 text-rose-500" />
                          <span className="text-slate-600">失败: <span className="font-bold">{task.failedCount}</span></span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <Database className="w-4 h-4 text-slate-400" />
                          <span className="text-slate-600">索引重建: <span className={`font-bold ${task.isIndexRebuilt ? 'text-emerald-600' : 'text-slate-400'}`}>
                            {task.isIndexRebuilt ? '是' : '否'}
                          </span></span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <button className="text-blue-600 hover:text-blue-700 font-medium text-sm transition-colors mt-1">查看日志</button>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Welcome Section / Default view */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-gradient-to-br from-blue-600 to-indigo-700 p-8 rounded-2xl text-white shadow-lg relative overflow-hidden group">
                <div className="relative z-10">
                  <h2 className="text-2xl font-bold mb-2">欢迎回来, 管理员</h2>
                  <p className="text-blue-100 max-w-md">金融智能研究 Agent 知识库正在平稳运行中。您可以在此管理文档资料、监控导入任务以及维护向量索引。</p>
                  <button 
                    onClick={() => setIsImportModalOpen(true)}
                    className="mt-6 bg-white text-blue-600 px-6 py-2.5 rounded-lg font-bold hover:bg-blue-50 transition-all flex items-center gap-2 group"
                  >
                    开始导入新资料
                    <ChevronRight className="w-4 h-4 translate-x-0 group-hover:translate-x-1 transition-transform" />
                  </button>
                </div>
                <div className="absolute top-1/2 -right-12 -translate-y-1/2 w-64 h-64 bg-white/10 rounded-full blur-3xl group-hover:scale-110 transition-transform duration-1000" />
              </div>
              
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="font-bold text-lg">快速维护</h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <button onClick={handleReindex} className="flex items-center gap-4 p-4 rounded-xl border border-slate-100 hover:border-blue-200 hover:bg-blue-50/30 transition-all text-left">
                    <div className="p-3 bg-blue-100 text-blue-600 rounded-lg">
                      <RefreshCw className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="font-bold text-slate-800">全量索引重建</div>
                      <div className="text-xs text-slate-500">重新处理所有文档块</div>
                    </div>
                  </button>
                  <button className="flex items-center gap-4 p-4 rounded-xl border border-slate-100 hover:border-amber-200 hover:bg-amber-50/30 transition-all text-left">
                    <div className="p-3 bg-amber-100 text-amber-600 rounded-lg">
                      <Layers className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="font-bold text-slate-800">清理冗余数据</div>
                      <div className="text-xs text-slate-500">移除无关联的矢量分块</div>
                    </div>
                  </button>
                </div>
              </div>
            </div>

            <div className="space-y-6">
               <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <h3 className="font-bold text-lg mb-4">系统健康状态</h3>
                <div className="space-y-4">
                  {[
                    { label: '向量数据库 (Milvus)', status: 'online' },
                    { label: '嵌入模型 (Embedding)', status: 'online' },
                    { label: '大型语言模型 (LLM)', status: 'online' },
                    { label: '文件服务 (OSS)', status: 'online' }
                  ].map((item, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-b border-slate-50 last:border-0">
                      <span className="text-sm text-slate-600">{item.label}</span>
                      <span className="flex items-center gap-1.5 text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                        <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                        Running
                      </span>
                    </div>
                  ))}
                </div>
               </div>
            </div>
          </div>
        )}
      </main>

      {/* F-3 Document Detail Modal Overlay */}
      <AnimatePresence>
        {selectedDoc && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedDoc(null)}
              className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl overflow-hidden overflow-y-auto max-h-[90vh]"
            >
              <div className="p-8 space-y-6">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                       <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-[10px] font-black uppercase rounded">
                        {selectedDoc.type}
                      </span>
                      {getStatusIcon(selectedDoc.status)}
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 leading-tight">{selectedDoc.title}</h2>
                  </div>
                  <button 
                    onClick={() => setSelectedDoc(null)}
                    className="p-2 hover:bg-slate-100 rounded-full transition-colors"
                  >
                    <XCircle className="w-6 h-6 text-slate-400" />
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-6 py-6 border-y border-slate-100">
                  <div className="space-y-1">
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">所属公司</p>
                    <p className="font-semibold text-slate-800">{selectedDoc.company}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">导入日期</p>
                    <p className="font-semibold text-slate-800">{selectedDoc.date}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">来源集合</p>
                    <p className="font-semibold text-slate-800">{selectedDoc.collectionName}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">分块数量</p>
                    <p className="font-mono font-bold text-blue-600">{selectedDoc.chunkCount}</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-bold text-slate-800 mb-2">原始来源路径</h4>
                    <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg text-xs font-mono text-slate-500 break-all">
                      {selectedDoc.sourcePath}
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-bold text-slate-800 mb-2">Chunk 摘要</h4>
                    <p className="text-sm text-slate-600 leading-relaxed bg-blue-50/30 p-4 rounded-xl border border-blue-50 italic">
                      “{selectedDoc.chunkSummary}”
                    </p>
                  </div>

                  {selectedDoc.status === 'failed' && (
                    <div className="p-4 bg-rose-50 border border-rose-100 rounded-xl">
                      <h4 className="text-sm font-bold text-rose-800 mb-1 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />
                        错误详情
                      </h4>
                      <p className="text-sm text-rose-700">{selectedDoc.failureReason}</p>
                    </div>
                  )}
                </div>

                <div className="flex gap-3 pt-4">
                  <button onClick={() => void handleReimportDoc(selectedDoc)} className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl transition-all shadow-md shadow-blue-200">
                    重新导入
                  </button>
                  <button onClick={() => void handleDisableDoc(selectedDoc)} className="flex items-center gap-2 px-6 py-3 border border-slate-200 text-slate-600 font-bold rounded-xl hover:bg-slate-50 transition-all">
                    <Trash2 className="w-4 h-4 text-rose-500" />
                    删除文档
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>


      {/* Settings Dialog */}
      <AnimatePresence>
        {isSettingsModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsSettingsModalOpen(false)}
              className="absolute inset-0 bg-slate-900/30 backdrop-blur-[1px]"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.96, y: 12 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.96, y: 12 }}
              className="relative w-full max-w-[500px] max-h-[88vh] rounded-lg bg-white shadow-2xl border border-slate-200 flex flex-col overflow-hidden"
            >
              <div className="h-12 px-5 border-b border-slate-100 flex items-center justify-between shrink-0">
                <h3 className="text-base font-medium text-slate-900">知识库设置</h3>
                <button onClick={() => setIsSettingsModalOpen(false)} className="p-1 rounded-md hover:bg-slate-100 transition-colors">
                  <X className="w-5 h-5 text-slate-400" />
                </button>
              </div>

              <div className="px-6 py-4 overflow-y-auto space-y-6">
                <SettingSelect label="嵌入模型" value="BAAI/bge-m3 | 硅基流动" />
                <SettingInput label="嵌入维度" value="1024" trailing={<RotateCw className="w-4 h-4 text-slate-500" />} />
                <SettingSlider label="请求文档片段数量" min="1" mid="默认" value="30" max="50" />

                <div className="border-t border-slate-100 pt-5 space-y-6">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium text-slate-900">高级设置</h4>
                    <span className="text-[11px] text-slate-400">仅前端展示，暂未连接后端</span>
                  </div>
                  <SettingSelect label="文档处理" value="选择一个文档处理服务商" muted />
                  <SettingSelect label="重排模型" value="BAAI/bge-reranker-v2-m3 | 硅基流动" />
                  <SettingInput label="分段大小" value="默认值（不建议修改）" muted />
                  <SettingInput label="重叠大小" value="默认值（不建议修改）" muted />
                  <SettingInput label="匹配度阈值" value="未设置" muted />
                </div>
              </div>

              <div className="h-14 px-5 border-t border-slate-100 flex items-center justify-between bg-white shrink-0">
                <button className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md border border-slate-200 text-sm font-medium text-slate-700 hover:bg-slate-50">
                  <SlidersHorizontal className="w-4 h-4" />
                  高级设置
                </button>
                <div className="flex items-center gap-2">
                  <button onClick={() => setIsSettingsModalOpen(false)} className="px-3 py-1.5 rounded-md border border-slate-200 text-sm text-slate-700 hover:bg-slate-50">取消</button>
                  <button onClick={() => setIsSettingsModalOpen(false)} className="px-3 py-1.5 rounded-md bg-emerald-500 text-sm font-medium text-white hover:bg-emerald-600">保存</button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* F-4 Import Dialog/Popup Overlay */}
      <AnimatePresence>
        {isImportModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsImportModalOpen(false)}
              className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-lg bg-white rounded-2xl shadow-2xl flex flex-col max-h-[90vh]"
            >
              <div className="p-6 border-b border-slate-100 flex items-center justify-between">
                <h3 className="text-xl font-bold text-slate-800">导入新资料</h3>
                <button onClick={() => setIsImportModalOpen(false)} className="p-1 hover:bg-slate-100 rounded-full transition-colors">
                  <XCircle className="w-6 h-6 text-slate-300" />
                </button>
              </div>
              <div className="p-8 overflow-y-auto space-y-6">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">选择文件</label>
                  <label className="block border-2 border-dashed border-slate-200 rounded-2xl p-8 text-center hover:border-blue-400 hover:bg-blue-50/30 transition-all cursor-pointer group">
                    <Upload className="w-10 h-10 text-slate-300 mx-auto mb-3 group-hover:text-blue-500 transition-colors" />
                    <p className="text-sm font-bold text-slate-600 mb-1">点击选择文件</p>
                    <p className="text-xs text-slate-400 font-medium">支持 PDF, MD, TXT (Max 50MB)</p>
                    <input type="file" multiple accept=".pdf,.md,.txt" className="hidden" onChange={(event) => setSelectedFiles(Array.from(event.target.files ?? []))} />
                    {selectedFiles.length > 0 && <p className="mt-3 text-xs font-bold text-blue-600">已选择 {selectedFiles.length} 个文件</p>}
                  </label>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="block text-xs font-black text-slate-500 uppercase">Collection 集合</label>
                    <select value={collectionName} onChange={(event) => setCollectionName(event.target.value)} className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500">
                      <option value="financial_reports">financial_reports</option>
                      <option value="market_news">market_news</option>
                      <option value="internal_research">internal_research</option>
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="block text-xs font-black text-slate-500 uppercase">文档类型</label>
                    <select value={defaultDocType} onChange={(event) => setDefaultDocType(event.target.value)} className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500">
                      <option value="financial_report">financial_report</option>
                      <option value="research_report">research_report</option>
                      <option value="news">news</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-black text-slate-500 uppercase">关联公司 (可选)</label>
                  <input type="text" value={defaultCompany} onChange={(event) => setDefaultCompany(event.target.value)} placeholder="例如: NVIDIA, CATL" className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500" />
                </div>

                <div className="flex items-center gap-3 pt-4">
                  <input type="checkbox" id="reindex" checked={rebuildAfterImport} onChange={(event) => setRebuildAfterImport(event.target.checked)} className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500" />
                  <label htmlFor="reindex" className="text-sm font-medium text-slate-600">完成后自动触发索引重建</label>
                </div>
              </div>

              <div className="p-6 border-t border-slate-100 flex gap-4">
                <button 
                  onClick={() => setIsImportModalOpen(false)}
                  className="flex-1 py-3 px-4 border border-slate-200 rounded-xl font-bold text-slate-600 hover:bg-slate-50 transition-all text-sm"
                >
                  取消
                </button>
                <button 
                  onClick={() => void handleUploadAndImport()}
                  className="flex-[2] py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold shadow-lg shadow-blue-200 transition-all text-sm"
                >
                  确认导入
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
function FieldLabel({ label }: { label: string }) {
  return (
    <label className="mb-2 flex items-center gap-1.5 text-sm font-medium text-slate-800">
      {label}
      <Info className="w-3.5 h-3.5 text-slate-400" />
    </label>
  );
}

function SettingSelect({ label, value, muted = false }: { label: string; value: string; muted?: boolean }) {
  return (
    <div>
      <FieldLabel label={label} />
      <div className={`h-9 rounded-md border border-slate-200 px-3 flex items-center justify-between text-sm ${muted ? 'text-slate-400 bg-white' : 'text-slate-700 bg-white'}`}>
        <span className="flex items-center gap-2 truncate">
          {!muted && <Database className="w-4 h-4 text-blue-500" />}
          {value}
        </span>
        <ChevronDown className="w-4 h-4 text-slate-300" />
      </div>
    </div>
  );
}

function SettingInput({ label, value, muted = false, trailing }: { label: string; value: string; muted?: boolean; trailing?: ReactNode }) {
  return (
    <div>
      <FieldLabel label={label} />
      <div className={`h-9 rounded-md border border-slate-200 px-3 flex items-center justify-between text-sm ${muted ? 'text-slate-400' : 'text-slate-700'}`}>
        <span>{value}</span>
        {trailing}
      </div>
    </div>
  );
}

function SettingSlider({ label, min, mid, value, max }: { label: string; min: string; mid: string; value: string; max: string }) {
  return (
    <div>
      <FieldLabel label={label} />
      <div className="pt-2">
        <div className="relative h-2 rounded-full bg-slate-100">
          <div className="absolute left-0 top-0 h-2 w-[18%] rounded-full bg-emerald-200" />
          <div className="absolute left-[18%] top-1/2 h-4 w-4 -translate-y-1/2 rounded-full border-2 border-emerald-200 bg-white shadow" />
        </div>
        <div className="mt-2 grid grid-cols-4 text-xs text-slate-500">
          <span>{min}</span>
          <span>{mid}</span>
          <span className="text-center">{value}</span>
          <span className="text-right">{max}</span>
        </div>
      </div>
    </div>
  );
}

