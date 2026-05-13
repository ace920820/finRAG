import { useState, useRef } from 'react';
import { Header } from './components/Header';
import { SidebarLeft } from './components/SidebarLeft';
import { ChatArea } from './components/ChatArea';
import { SidebarRight } from './components/SidebarRight';
import { Message, MessageStage } from './types';
import { mockBM25Docs, mockVectorDocs, mockRerankDocs, mockAnswerStream, mockKeywords } from './data/mock';

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeCitationId, setActiveCitationId] = useState<string | null>(null);
  const streamIntRef = useRef<NodeJS.Timeout | null>(null);

  const simulateRAGFlow = (query: string) => {
    // 1. Add user message
    const newMessage: Message = { id: Date.now().toString(), role: 'user', content: query };
    
    // 2. Add empty assistant message
    const assistantMsgId = (Date.now() + 1).toString();
    const initAssistantMessage: Message = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      stage: 'query'
    };

    setMessages(prev => [...prev, newMessage, initAssistantMessage]);

    // Timers for stages
    setTimeout(() => {
      setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, stage: 'retrieve', queryRewrite: mockKeywords } : m));
    }, 400);

    setTimeout(() => {
      setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, stage: 'rerank' } : m));
    }, 1300);

    setTimeout(() => {
      setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, stage: 'generate' } : m));
      
      // Simulate streaming
      let charIndex = 0;
      if (streamIntRef.current) clearInterval(streamIntRef.current);
      
      streamIntRef.current = setInterval(() => {
        charIndex += 4;
        if (charIndex >= mockAnswerStream.length) {
          charIndex = mockAnswerStream.length;
          setMessages(prev => prev.map(m => m.id === assistantMsgId ? { 
            ...m, 
            content: mockAnswerStream,
            stage: 'done',
            tokens: 1840
          } : m));
          if (streamIntRef.current) clearInterval(streamIntRef.current);
        } else {
          const currentContent = mockAnswerStream.substring(0, charIndex);
          setMessages(prev => prev.map(m => m.id === assistantMsgId ? { 
            ...m, 
            content: currentContent 
          } : m));
        }
      }, 50);

    }, 2500);
  };

  const handleReset = () => {
    if (streamIntRef.current) clearInterval(streamIntRef.current);
    setMessages([]);
    setActiveCitationId(null);
  };

  return (
    <div className="flex flex-col h-screen w-full bg-slate-50 text-slate-900 overflow-hidden font-sans">
      <Header onReset={handleReset} />
      <main className="flex flex-1 overflow-hidden">
        <SidebarLeft onSelectExample={simulateRAGFlow} />
        <ChatArea 
          messages={messages} 
          onSendMessage={simulateRAGFlow} 
          activeCitationId={activeCitationId}
          onCitationClick={(id) => {
            setActiveCitationId(prev => prev === id ? null : id);
          }}
        />
        <SidebarRight 
          bm25Docs={mockBM25Docs}
          vectorDocs={mockVectorDocs}
          rerankDocs={mockRerankDocs}
          activeCitationId={activeCitationId}
        />
      </main>
    </div>
  );
}
