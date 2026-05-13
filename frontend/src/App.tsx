import { useEffect, useRef, useState } from 'react';
import { Header } from './components/Header';
import { SidebarLeft } from './components/SidebarLeft';
import { ChatArea } from './components/ChatArea';
import { SidebarRight } from './components/SidebarRight';
import { Document, DocType, Message } from './types';
import { fetchDocuments, mapRerankResults, mapRetrievalResults, streamQuery } from './api/finrag';
import { mockBM25Docs, mockLeftDocuments, mockRerankDocs, mockVectorDocs } from './data/mock';

type LeftDocument = Array<{ id: string; title: string; type: DocType }>;

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeCitationId, setActiveCitationId] = useState<string | null>(null);
  const [leftDocuments, setLeftDocuments] = useState<LeftDocument>(mockLeftDocuments);
  const [bm25Docs, setBm25Docs] = useState<Document[]>(mockBM25Docs);
  const [vectorDocs, setVectorDocs] = useState<Document[]>(mockVectorDocs);
  const [rerankDocs, setRerankDocs] = useState<Document[]>(mockRerankDocs);
  const queryAbortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchDocuments(controller.signal)
      .then(setLeftDocuments)
      .catch(() => setLeftDocuments(mockLeftDocuments));
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
    setBm25Docs([]);
    setVectorDocs([]);
    setRerankDocs([]);

    const now = Date.now();
    const userMessage: Message = { id: `${now}`, role: 'user', content: query };
    const assistantMsgId = `${now + 1}`;
    const assistantMessage: Message = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      stage: 'query',
    };

    setMessages(prev => [...prev, userMessage, assistantMessage]);

    try {
      await streamQuery(query, {
        onQueryRewrite: payload => {
          updateAssistant(assistantMsgId, {
            stage: 'query',
            queryRewrite: [...payload.expanded, ...payload.sub_queries].filter(Boolean),
          });
        },
        onRetrievalComplete: payload => {
          setBm25Docs(mapRetrievalResults(payload.bm25_results));
          setVectorDocs(mapRetrievalResults(payload.vector_results));
          updateAssistant(assistantMsgId, { stage: 'retrieve' });
        },
        onRerankComplete: payload => {
          setRerankDocs(mapRerankResults(payload.top5));
          updateAssistant(assistantMsgId, { stage: 'rerank' });
        },
        onAnswerChunk: payload => {
          updateAssistant(assistantMsgId, message => ({
            stage: 'generate',
            content: message.content ? `${message.content}\n\n${payload.text}` : payload.text,
          }));
        },
        onDone: payload => {
          updateAssistant(assistantMsgId, {
            stage: 'done',
            tokens: payload.total_tokens,
          });
          if (queryAbortRef.current === controller) {
            queryAbortRef.current = null;
          }
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

  const handleReset = () => {
    queryAbortRef.current?.abort();
    setMessages([]);
    setActiveCitationId(null);
    setBm25Docs(mockBM25Docs);
    setVectorDocs(mockVectorDocs);
    setRerankDocs(mockRerankDocs);
  };

  return (
    <div className="flex flex-col h-screen w-full bg-slate-50 text-slate-900 overflow-hidden font-sans">
      <Header onReset={handleReset} />
      <main className="flex flex-1 overflow-hidden">
        <SidebarLeft documents={leftDocuments} onSelectExample={runRAGFlow} />
        <ChatArea 
          messages={messages} 
          onSendMessage={runRAGFlow} 
          activeCitationId={activeCitationId}
          onCitationClick={(id) => {
            setActiveCitationId(prev => prev === id ? null : id);
          }}
        />
        <SidebarRight 
          bm25Docs={bm25Docs}
          vectorDocs={vectorDocs}
          rerankDocs={rerankDocs}
          activeCitationId={activeCitationId}
        />
      </main>
    </div>
  );
}
