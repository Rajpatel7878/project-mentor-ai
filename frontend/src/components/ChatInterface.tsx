'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Sparkles, Zap, ChevronDown, ChevronUp } from 'lucide-react';
import { AgentBadge } from './AgentBadge';
import type { ChatMessage } from '@/lib/api';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSend: (message: string) => void;
  isThinking: boolean;
  followUpQuestions: string[];
}

const GUIDED_ACTIONS = [
  {
    id: 'sprint',
    label: 'Sprint Planning',
    icon: '🚀',
    prompt: 'Jarvis, guide me through our Sprint Planning and ask me the necessary questions to build our task roadmap.',
  },
  {
    id: 'architecture',
    label: 'Architecture Review',
    icon: '🛠️',
    prompt: 'Jarvis, I need a technical architecture review. Please ask me about our system parameters and requirements.',
  },
  {
    id: 'phone',
    label: 'Ring My Phone',
    icon: '📱',
    prompt: 'Jarvis, ring my phone at maximum volume so I can locate it.',
  },
  {
    id: 'pitch',
    label: 'Pitch Deck Review',
    icon: '📈',
    prompt: 'Jarvis, act as our venture capital advisor. Ask me the key questions needed to pressure-test our investor deck.',
  },
  {
    id: 'diagnostic',
    label: 'System Diagnostic',
    icon: '🛡️',
    prompt: 'Jarvis, run a complete diagnostic across our host telemetry, IoT hardware, and cognitive pipelines.',
  },
];

export function ChatInterface({ messages, onSend, isThinking, followUpQuestions }: ChatInterfaceProps) {
  const [showActions, setShowActions] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);


  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const input = inputRef.current;
    if (input?.value.trim()) {
      onSend(input.value.trim());
      input.value = '';
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto space-y-4 p-4 min-h-0">
        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-lg p-4 ${
                msg.role === 'user'
                  ? 'bg-cyan-glow/10 border border-cyan-glow/30'
                  : 'glass-panel'
              }`}
            >
              {msg.role === 'assistant' && msg.agent && (
                <div className="mb-2">
                  <AgentBadge agent={msg.agent} />
                </div>
              )}
              <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '');
                      const code = String(children).replace(/\n$/, '');
                      if (match) {
                        return (
                          <SyntaxHighlighter style={vscDarkPlus} language={match[1]} PreTag="div">
                            {code}
                          </SyntaxHighlighter>
                        );
                      }
                      return (
                        <code className="bg-white/10 px-1 py-0.5 rounded text-cyan-glow" {...props}>
                          {children}
                        </code>
                      );
                    },
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              </div>
              {msg.commandResults && msg.commandResults.length > 0 && (
                <div className="mt-3 pt-3 border-t border-white/10">
                  {msg.commandResults.map((cmd, i) => (
                    <div key={i} className={`text-xs flex items-center gap-2 ${cmd.success ? 'text-green-400' : 'text-red-400'}`}>
                      <span>{cmd.success ? '✓' : '✗'}</span>
                      {cmd.message}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        ))}

        {isThinking && (
          <div className="flex justify-start">
            <div className="glass-panel rounded-lg p-4 flex items-center gap-2">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  className="w-2 h-2 rounded-full bg-cyan-glow"
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
                />
              ))}
              <span className="text-sm text-white/50 ml-2">Mentor is thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {followUpQuestions.length > 0 && (
        <div className="px-4 pb-2 flex flex-wrap gap-2">
          {followUpQuestions.map((q, i) => (
            <button
              key={i}
              onClick={() => onSend(q)}
              className="text-xs px-3 py-1.5 rounded-full border border-cyan-glow/30 text-cyan-glow/80 hover:bg-cyan-glow/10 transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Interactive Guided Action Triggers */}
      <div className="px-4 py-2 border-t border-white/5 bg-black/20">
        <div className="flex items-center justify-between mb-1.5">
          <div className="flex items-center gap-1.5 text-[10px] font-display font-semibold uppercase tracking-wider text-white/50">
            <Sparkles className="w-3 h-3 text-cyan-glow" />
            <span>Interactive Guided Actions</span>
          </div>
          <button
            type="button"
            onClick={() => setShowActions((prev) => !prev)}
            className="text-[10px] text-white/40 hover:text-white flex items-center gap-0.5"
          >
            <span>{showActions ? 'Hide' : 'Show Actions'}</span>
            {showActions ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />}
          </button>
        </div>

        <AnimatePresence>
          {showActions && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar"
            >
              {GUIDED_ACTIONS.map((action) => (
                <button
                  key={action.id}
                  type="button"
                  disabled={isThinking}
                  onClick={() => onSend(action.prompt)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/5 hover:bg-cyan-500/20 hover:border-cyan-500/40 border border-white/10 text-xs text-white/80 hover:text-white shrink-0 transition-all group"
                >
                  <span className="text-sm">{action.icon}</span>
                  <span className="font-display font-medium text-[11px] group-hover:text-cyan-glow">
                    {action.label}
                  </span>
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t border-white/10">

        <div className="flex gap-3">
          <input
            ref={inputRef}
            type="text"
            placeholder="Ask your mentor anything, sir..."
            className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-cyan-glow/50 focus:ring-1 focus:ring-cyan-glow/30 transition-all"
          />
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={isThinking}
            className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 rounded-lg font-display text-sm tracking-wider disabled:opacity-50 hover:from-cyan-500 hover:to-blue-500 transition-all glow-border"
          >
            SEND
          </motion.button>
        </div>
      </form>
    </div>
  );
}
