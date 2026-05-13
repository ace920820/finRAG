import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import clsx from 'clsx';
import { Message } from '../types';

interface ChatAreaProps {
  messages: Message[];
  onSendMessage: (content: string) => void;
  activeCitationId: string | null;
  onCitationClick: (id: string) => void;
  onPreviewChange?: (value: string) => void;
  previewText?: string;
  previewLoading?: boolean;
}

export function ChatArea({ messages, onSendMessage, activeCitationId, onCitationClick, onPreviewChange, previewText, previewLoading }: ChatAreaProps) {
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setInput(value);
    onPreviewChange?.(value);
    
    if (value.trim() !== '') {
      setIsTyping(true);
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = setTimeout(() => {
        setIsTyping(false);
      }, 500);
    } else {
      setIsTyping(false);
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    }
  };

  const submitInput = () => {
    if (!input.trim()) return;
    onSendMessage(input.trim());
    setInput('');
    onPreviewChange?.('');
    setIsTyping(false);
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitInput();
    }
  };

  const showRewritePreview = !isTyping && input.trim() !== '';

  return (
    <section className="flex-1 flex flex-col bg-white overflow-hidden">
      <div className="flex-1 p-6 overflow-y-auto space-y-8 scroll-smooth" ref={scrollRef}>
        <div className="max-w-3xl mx-auto space-y-6">
        {messages.map((msg, idx) => (
          <div key={msg.id} className={clsx("flex items-start gap-3")}>
            {msg.role === 'user' ? (
              <>
                <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center flex-shrink-0 text-slate-500">U</div>
                <div className="bg-slate-100 px-4 py-2.5 rounded-2xl rounded-tl-none text-sm text-slate-800">
                  {msg.content}
                </div>
              </>
            ) : (
              <>
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 text-white font-bold">AI</div>
                <div className="flex-1 space-y-4">
                {/* Stages tracking */}
                {msg.stage && msg.stage !== 'idle' && (
                  <div className="space-y-3">
                    <StageItem 
                      title="STAGE 01 · QUERY 处理" 
                      active={msg.stage === 'query'} 
                      done={['retrieve', 'rerank', 'generate', 'done'].includes(msg.stage)}
                      duration="0.4s"
                    >
                      {msg.queryRewrite && (
                        <div className="text-[10px] text-slate-500 mt-1">
                          检索关键词：{msg.queryRewrite.join('、')}
                        </div>
                      )}
                    </StageItem>

                    <StageItem 
                      title="STAGE 02 · 召回 · 24 篇 → 候选 18" 
                      active={msg.stage === 'retrieve'} 
                      done={['rerank', 'generate', 'done'].includes(msg.stage)}
                      duration="0.9s"
                    />

                    <StageItem 
                      title="STAGE 03 · RERANK · TOP 5" 
                      active={msg.stage === 'rerank'} 
                      done={['generate', 'done'].includes(msg.stage)}
                      duration="1.2s"
                    />

                    <StageItem 
                      title={msg.stage === 'done' ? "STAGE 04 · 生成完成" : "STAGE 04 · 生成中…"} 
                      active={msg.stage === 'generate'} 
                      done={msg.stage === 'done'}
                      duration={msg.stage === 'done' ? "3.1s" : "streaming"}
                    />
                  </div>
                )}

                {/* Markdown content */}
                {(['generate', 'done'].includes(msg.stage!) || msg.content) && (
                  <>
                    <div className="prose prose-sm prose-slate max-w-none text-slate-700 leading-relaxed markdown-override">
                      <ReactMarkdown 
                        rehypePlugins={[rehypeRaw]}
                        components={{
                          span: ({ node, className, children, ...props }) => {
                            if (className && className.includes('cite')) {
                              let content = String(children);
                              let idMatch = content.match(/\d+/);
                              const datasetId = (props as any)['data-id'];
                              
                              const id = datasetId || (idMatch ? idMatch[0] : content);
                              const isActive = activeCitationId === id;
                              
                              return (
                                <span 
                                  className={clsx("inline-flex items-center justify-center w-4 h-4 text-[9px] rounded cursor-pointer font-bold mx-0.5", isActive ? "bg-blue-600 text-white" : "bg-blue-100 text-blue-600 hover:bg-blue-200")} 
                                  onClick={() => onCitationClick(id)}
                                  {...props}
                                >
                                  {children}
                                </span>
                              );
                            }
                            return <span className={className} {...props}>{children}</span>;
                          }
                        }}
                      >
                        {msg.content.replace(/\[(\d+)\]/g, '<span class="cite" data-id="$1">$1</span>')}
                      </ReactMarkdown>

                      {msg.stage === 'generate' && (
                        <div className="animate-pulse space-y-2 mt-4">
                          <div className="h-2 bg-slate-200 rounded w-[90%]"></div>
                          <div className="h-2 bg-slate-200 rounded w-[70%]"></div>
                          <div className="h-2 bg-slate-200 rounded w-[50%]"></div>
                        </div>
                      )}
                    </div>
                    {msg.stage === 'done' && msg.tokens && (
                      <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400 mt-2">
                        <span>总耗时：4.5s · Token 用量：{msg.tokens}</span>
                        <div className="flex gap-4">
                          <span>准确度：98%</span>
                          <span>来源引用：5个文档</span>
                        </div>
                      </div>
                    )}
                  </>
                )}
                </div>
              </>
            )}
          </div>
        ))}
        </div>
      </div>

      <div className="p-4 border-t border-slate-200 bg-white">
        <div className="max-w-3xl mx-auto relative">
          <textarea 
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            className="w-full p-3 pr-24 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none text-sm"
            placeholder="输入您的金融研究问题... (Shift + Enter 换行)"
            rows={1}
          />
          <div className="absolute right-2 bottom-2 flex items-center gap-2">
            <span className="text-[10px] text-slate-400">Enter 发送</span>
            <button 
              onClick={submitInput}
              disabled={!input.trim()}
              className="p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
            </button>
          </div>
        </div>
        
        {showRewritePreview ? (
          <div className="max-w-3xl mx-auto mt-2 text-[10px] text-blue-500 font-mono min-h-[16px]">
            {previewLoading ? '正在分析输入...' : `检索关键词预览：${previewText || '暂无预览'}`}
          </div>
        ) : (
          <div className="max-w-3xl mx-auto mt-2 text-[10px] text-slate-400 font-mono min-h-[16px]">
            {isTyping ? "正在分析输入..." : "将在停止输入 500ms 后展示关键词预览"}
          </div>
        )}
      </div>
    </section>
  );
}

function StageItem({ title, active, done, duration, children }: { title: string, active: boolean, done: boolean, duration: string, children?: React.ReactNode }) {
  if (!active && !done) return null;
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2 text-[10px] items-center text-slate-400">
        <span className="flex items-center gap-1">
          <div className={clsx("w-1.5 h-1.5 rounded-full", done || active ? "bg-green-500" : "bg-slate-300")}></div>
          <span className={clsx(active ? "text-blue-600 font-medium" : "")}>{title}</span>
        </span>
        <span className="text-slate-200">|</span>
        <span>耗时: {duration}</span>
      </div>
      {(active || done) && children && (
        <div className="pl-4 border-l-2 border-slate-100 ml-1">
          {children}
        </div>
      )}
    </div>
  );
}
