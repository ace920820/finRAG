import { useEffect, useRef, useState } from 'react';
import { Header } from './components/Header';
import { SidebarLeft } from './components/SidebarLeft';
import { ChatArea } from './components/ChatArea';
import { SidebarRight } from './components/SidebarRight';
import { Document, LibraryDocument, Message, RetrievalSnapshot } from './types';
import { fetchDocuments, mapRerankResults, mapRetrievalResults, streamQuery } from './api/finrag';
import { fetchRewritePreview, formatPreviewKeywords, PreviewRewriteResponse } from './api/preview';
import { mockBM25Docs, mockLeftDocuments, mockRerankDocs, mockVectorDocs } from './data/mock';
import { KnowledgeBaseManager } from './pages/KnowledgeBaseManager';

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeCitationId, setActiveCitationId] = useState<string | null>(null);
  const [activeAssistantId, setActiveAssistantId] = useState<string | null>(null);
  const [leftDocuments, setLeftDocuments] = useState<LibraryDocument[]>(mockLeftDocuments.map(doc => ({ ...doc, openUrl: '#' })));
  const [previewText, setPreviewText] = useState('宁德时代、CATL、300750、经营风险');
  const [previewLoading, setPreviewLoading] = useState(false);
  const queryAbortRef = useRef<AbortController | null>(null);
  const previewAbortRef = useRef<AbortController | null>(null);
  const previewTimerRef = useRef<NodeJS.Timeout | null>(null);
  const [currentPage, setCurrentPage] = useState<'chat' | 'knowledge-base'>(() => window.location.hash === '#/knowledge-base' ? 'knowledge-base' : 'chat');

  useEffect(() => {
    const handleHashChange = () => setCurrentPage(window.location.hash === '#/knowledge-base' ? 'knowledge-base' : 'chat');
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchDocuments(controller.signal)
      .then(setLeftDocuments)
      .catch(() => setLeftDocuments(mockLibraryDocuments()));
    return () => controller.abort();
  }, []);

  const updateAssistant = (assistantMsgId: string, patch: Partial<Message> | ((message: Message) => Partial<Message>)) => {
    setMessages(prev => prev.map(message => {
      if (message.id !== assistantMsgId) return message;
      const nextPatch = typeof patch === 'function' ? patch(message) : patch;
      return { ...message, ...nextPatch };
    }));
  };

  const runRAGFlow = async (query: string) => {
    queryAbortRef.current?.abort();
    const controller = new AbortController();
    queryAbortRef.current = controller;
    setActiveCitationId(null);

    const now = Date.now();
    const userMessage: Message = { id: `${now}`, role: 'user', content: query };
    const assistantMsgId = `${now + 1}`;
    const assistantMessage: Message = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      stage: 'query',
      retrievalSnapshot: emptySnapshot(),
    };

    setMessages(prev => [...prev, userMessage, assistantMessage]);
    setActiveAssistantId(assistantMsgId);

    try {
      await streamQuery(query, {
        onQueryRewrite: payload => {
          const queryTerms = [...payload.expanded, ...payload.sub_queries].filter(Boolean);
          updateAssistant(assistantMsgId, message => ({
            stage: 'query',
            queryRewrite: queryTerms,
            retrievalSnapshot: {
              ...(message.retrievalSnapshot ?? emptySnapshot()),
              queryPlan: payload.plan ?? null,
              expandedTerms: payload.expanded,
              subQueries: payload.sub_queries,
            },
          }));
        },
        onIntentDetected: payload => {
          updateAssistant(assistantMsgId, message => ({
            retrievalSnapshot: {
              ...(message.retrievalSnapshot ?? emptySnapshot()),
              intent: payload,
            },
          }));
        },
        onRetrievalComplete: payload => {
          const bm25Docs = mapRetrievalResults(payload.bm25_results);
          const vectorDocs = mapRetrievalResults(payload.vector_results);
          updateAssistant(assistantMsgId, { stage: 'retrieve' });
          updateAssistant(assistantMsgId, message => ({
            retrievalSnapshot: {
              ...(message.retrievalSnapshot ?? emptySnapshot()),
              bm25Docs,
              vectorDocs,
              bm25Error: payload.bm25_error ?? null,
              vectorError: payload.vector_error ?? null,
              retrievalCascade: payload.cascade_trace ?? [],
              iterativeTrace: payload.iterative_trace ?? null,
            },
          }));
        },
        onRerankComplete: payload => {
          const rerankDocs = mapRerankResults(payload.top5);
          updateAssistant(assistantMsgId, { stage: 'rerank' });
          updateAssistant(assistantMsgId, message => ({
            retrievalSnapshot: {
              ...(message.retrievalSnapshot ?? emptySnapshot()),
              rerankDocs,
              rerankCascade: payload.cascade_trace ?? [],
            },
          }));
        },
        onAnswerChunk: payload => {
          updateAssistant(assistantMsgId, message => ({
            stage: 'generate',
            content: message.content ? `${message.content}\n\n${payload.text}` : payload.text,
          }));
        },
        onDone: payload => {
          updateAssistant(assistantMsgId, message => ({
            stage: 'done',
            tokens: payload.total_tokens,
            retrievalSnapshot: {
              ...(message.retrievalSnapshot ?? emptySnapshot()),
              citations: payload.citations,
            },
          }));
        },
        onError: payload => {
          updateAssistant(assistantMsgId, {
            stage: 'done',
            content: `后端查询失败：${payload.message}`,
          });
        },
      }, controller.signal);
    } catch (error) {
      if (controller.signal.aborted) return;
      const message = error instanceof Error ? error.message : '未知错误';
      updateAssistant(assistantMsgId, {
        stage: 'done',
        content: `后端连接失败：${message}`,
      });
    } finally {
      if (queryAbortRef.current === controller) {
        queryAbortRef.current = null;
      }
    }
  };

  const requestPreview = async (value: string) => {
    previewAbortRef.current?.abort();
    const controller = new AbortController();
    previewAbortRef.current = controller;
    if (!value.trim()) {
      setPreviewText('');
      setPreviewLoading(false);
      return;
    }
    setPreviewLoading(true);
    try {
      const payload: PreviewRewriteResponse = await fetchRewritePreview(value, controller.signal);
      if (controller.signal.aborted) return;
      setPreviewText(formatPreviewKeywords(payload));
    } catch {
      if (!controller.signal.aborted) {
        setPreviewText('');
      }
    } finally {
      if (previewAbortRef.current === controller) {
        previewAbortRef.current = null;
      }
      if (!controller.signal.aborted) {
        setPreviewLoading(false);
      }
    }
  };

  const handlePreviewChange = (value: string) => {
    if (previewTimerRef.current) clearTimeout(previewTimerRef.current);
    if (!value.trim()) {
      previewAbortRef.current?.abort();
      setPreviewText('');
      setPreviewLoading(false);
      return;
    }
    setPreviewLoading(true);
    previewTimerRef.current = setTimeout(() => {
      void requestPreview(value);
    }, 500);
  };

  const handleReset = () => {
    queryAbortRef.current?.abort();
    previewAbortRef.current?.abort();
    if (previewTimerRef.current) clearTimeout(previewTimerRef.current);
    setMessages([]);
    setActiveCitationId(null);
    setActiveAssistantId(null);
    setPreviewText('宁德时代、CATL、300750、经营风险');
    setPreviewLoading(false);
  };

  const handleAssistantSelect = (messageId: string) => {
    setActiveAssistantId(messageId);
    setActiveCitationId(null);
  };

  const handleCitationClick = (messageId: string, citationId: string) => {
    setActiveAssistantId(messageId);
    setActiveCitationId(prev => (activeAssistantId === messageId && prev === citationId ? null : citationId));
  };

  const activeAssistant = [...messages].reverse().find(message => message.role === 'assistant' && message.id === activeAssistantId)
    ?? [...messages].reverse().find(message => message.role === 'assistant');
  const activeSnapshot = activeAssistant?.retrievalSnapshot ?? defaultSnapshot();
  const activeSnapshotLabel = activeAssistant ? `当前显示：回答 ${assistantTurnNumber(messages, activeAssistant.id)}` : '当前显示：示例数据';

  if (currentPage === 'knowledge-base') {
    return <KnowledgeBaseManager onBackToChat={() => { window.location.hash = '#/chat'; setCurrentPage('chat'); }} />;
  }

  return (
    <div className="flex flex-col h-screen w-full bg-slate-50 text-slate-900 overflow-hidden font-sans">
      <Header onReset={handleReset} onOpenKnowledgeBase={() => { window.location.hash = '#/knowledge-base'; setCurrentPage('knowledge-base'); }} />
      <main className="flex flex-1 overflow-hidden">
        <SidebarLeft documents={leftDocuments} onSelectExample={runRAGFlow} />
        <ChatArea 
          messages={messages} 
          onSendMessage={runRAGFlow} 
          activeCitationId={activeCitationId}
          activeAssistantId={activeAssistant?.id ?? null}
          onAssistantSelect={handleAssistantSelect}
          onCitationClick={handleCitationClick}
          onPreviewChange={handlePreviewChange}
          previewText={previewText}
          previewLoading={previewLoading}
        />
        <SidebarRight 
          snapshot={activeSnapshot}
          activeCitationId={activeCitationId}
          activeSnapshotLabel={activeSnapshotLabel}
        />
      </main>
    </div>
  );
}

function emptySnapshot(): RetrievalSnapshot {
  return {
    bm25Docs: [],
    vectorDocs: [],
    rerankDocs: [],
    bm25Error: null,
    vectorError: null,
    retrievalCascade: [],
    rerankCascade: [],
    iterativeTrace: null,
  };
}

function defaultSnapshot(): RetrievalSnapshot {
  return {
    bm25Docs: mockBM25Docs,
    vectorDocs: mockVectorDocs,
    rerankDocs: mockRerankDocs,
    bm25Error: null,
    vectorError: null,
    retrievalCascade: [],
    rerankCascade: [],
    iterativeTrace: null,
  };
}

function mockLibraryDocuments(): LibraryDocument[] {
  return mockLeftDocuments.map(doc => ({ ...doc, openUrl: '#' }));
}

function assistantTurnNumber(messages: Message[], messageId: string): number {
  return messages.filter(message => message.role === 'assistant').findIndex(message => message.id === messageId) + 1;
}
