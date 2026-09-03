'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, Cpu, Database, Network, Zap } from 'lucide-react';
import { ParticleBackground } from './ParticleBackground';
import { ChatInterface } from './ChatInterface';
import { VoiceControl } from './VoiceControl';
import { Dashboard } from './Dashboard';
import { DeviceDashboard } from './DeviceDashboard';
import { KnowledgeManager } from './KnowledgeManager';
import { HitlConfirmationModal } from './HitlConfirmationModal';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useVoice } from '@/hooks/useVoice';
import { fetchGreeting, fetchMetrics, sendChatMessage, type ChatMessage } from '@/lib/api';

const SESSION_ID = 'default';

export function MentorDashboard() {
  const [activeTab, setActiveTab] = useState<'assistant' | 'devices' | 'knowledge'>('assistant');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [greeting, setGreeting] = useState('');
  const [showGreeting, setShowGreeting] = useState(true);
  const [followUpQuestions, setFollowUpQuestions] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [metrics, setMetrics] = useState<Record<string, unknown>>({});
  const [useRestFallback, setUseRestFallback] = useState(false);

  // HITL State for Chat Commands
  const [hitlModal, setHitlModal] = useState<{
    isOpen: boolean;
    pendingCommand: string;
    description: string;
  }>({
    isOpen: false,
    pendingCommand: '',
    description: '',
  });

  const speakRef = useRef<(text: string) => void>(() => {});
  const sendChatRef = useRef<(message: string, sessionId: string) => void>(() => {});
  const isConnectedRef = useRef(false);

  const appendAssistantMessage = useCallback(
    (
      content: string,
      agent?: string,
      commandResults?: Array<{ success: boolean; message: string; requires_confirmation?: boolean }>
    ) => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: 'assistant',
          content,
          agent,
          timestamp: new Date(),
          commandResults,
        },
      ]);
      speakRef.current(content);

      // Check if any command requires HITL confirmation
      const needsConfirm = commandResults?.find((r) => r.requires_confirmation);
      if (needsConfirm) {
        setHitlModal({
          isOpen: true,
          pendingCommand: needsConfirm.message,
          description: `Action requires elevated authorization: ${needsConfirm.message}`,
        });
      }
    },
    []
  );

  const handleWsMessage = useCallback(
    (data: { type: string; payload: Record<string, unknown> }) => {
      if (data.type === 'greeting') {
        const payload = data.payload as { greeting: string; proactive_suggestions: string[] };
        setGreeting(payload.greeting);
        setSuggestions(payload.proactive_suggestions || []);
        setShowGreeting(true);
        setTimeout(() => setShowGreeting(false), 5000);
      }

      if (data.type === 'response') {
        const payload = data.payload as {
          response: string;
          agent: string;
          follow_up_questions: string[];
          suggestions: string[];
          command_results: Array<{ success: boolean; message: string; requires_confirmation?: boolean }>;
        };
        setFollowUpQuestions(payload.follow_up_questions || []);
        setSuggestions(payload.suggestions || []);
        appendAssistantMessage(payload.response, payload.agent, payload.command_results);
      }
    },
    [appendAssistantMessage]
  );

  const { isConnected, isThinking, sendChat, requestGreeting } = useWebSocket({
    onMessage: handleWsMessage,
    onConnect: () => {
      setUseRestFallback(false);
      isConnectedRef.current = true;
    },
    onDisconnect: () => {
      setUseRestFallback(true);
      isConnectedRef.current = false;
    },
  });

  sendChatRef.current = sendChat;
  isConnectedRef.current = isConnected;

  const handleSendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return;

      setMessages((prev) => [
        ...prev,
        { id: Date.now().toString(), role: 'user', content: text, timestamp: new Date() },
      ]);
      setFollowUpQuestions([]);

      if (isConnectedRef.current && !useRestFallback) {
        sendChatRef.current(text, SESSION_ID);
        return;
      }

      try {
        const result = await sendChatMessage(text, SESSION_ID);
        setFollowUpQuestions(result.follow_up_questions || []);
        setSuggestions(result.suggestions || []);
        appendAssistantMessage(result.response, result.agent, result.command_results);
      } catch {
        appendAssistantMessage(
          'I apologize, sir. I am unable to connect to my core systems. Please ensure the backend is running on port 8000.'
        );
      }
    },
    [useRestFallback, appendAssistantMessage]
  );

  const { isListening, isSpeaking, isSupported, startListening, stopListening, speak, stopSpeaking } =
    useVoice({
      onTranscript: handleSendMessage,
      onWakeWord: () => speakRef.current('Yes, sir?'),
      wakeWords: ['hey mentor', 'jarvis'],
      continuous: true,
    });

  speakRef.current = speak;

  useEffect(() => {
    const init = async () => {
      try {
        const greetingData = await fetchGreeting();
        setGreeting(greetingData.greeting);
        setSuggestions(greetingData.proactive_suggestions);
        setShowGreeting(true);
        speak(greetingData.greeting);
        setTimeout(() => setShowGreeting(false), 6000);

        const metricsData = await fetchMetrics();
        setMetrics(metricsData.metrics || {});
      } catch {
        requestGreeting();
      }
    };
    init();
  }, [speak, requestGreeting]);

  return (
    <div className="relative h-screen flex flex-col overflow-hidden">
      <ParticleBackground />

      {/* Top Header & Navigation */}
      <header className="relative z-10 flex items-center justify-between px-6 py-3 border-b border-white/10 glass-panel">
        <div className="flex items-center gap-4">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
            className="p-2 rounded-full border border-cyan-glow/30"
          >
            <Cpu className="w-7 h-7 text-cyan-glow" />
          </motion.div>
          <div>
            <h1 className="font-display text-lg tracking-widest glow-text">PROJECT MENTOR AI</h1>
            <p className="text-[10px] text-white/40 tracking-wider">
              JARVIS-INSPIRED AUTONOMOUS ECOSYSTEM
            </p>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center gap-1.5 p-1 glass-panel rounded-xl border border-white/10">
          <button
            onClick={() => setActiveTab('assistant')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-display tracking-wider transition-all ${
              activeTab === 'assistant'
                ? 'bg-cyan-500 text-black font-semibold shadow-md shadow-cyan-500/20'
                : 'text-white/60 hover:text-white hover:bg-white/5'
            }`}
          >
            <Bot className="w-3.5 h-3.5" />
            ASSISTANT CORE
          </button>

          <button
            onClick={() => setActiveTab('devices')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-display tracking-wider transition-all ${
              activeTab === 'devices'
                ? 'bg-cyan-500 text-black font-semibold shadow-md shadow-cyan-500/20'
                : 'text-white/60 hover:text-white hover:bg-white/5'
            }`}
          >
            <Network className="w-3.5 h-3.5" />
            DEVICES & IOT
          </button>

          <button
            onClick={() => setActiveTab('knowledge')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-display tracking-wider transition-all ${
              activeTab === 'knowledge'
                ? 'bg-cyan-500 text-black font-semibold shadow-md shadow-cyan-500/20'
                : 'text-white/60 hover:text-white hover:bg-white/5'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            KNOWLEDGE (RAG)
          </button>
        </div>

        {/* System Online Status */}
        <div className="flex items-center gap-2">
          <Zap className={`w-4 h-4 ${isConnected ? 'text-green-400' : 'text-red-400'}`} />
          <span className="text-xs font-display tracking-wider">
            {isConnected ? 'SYSTEMS ONLINE' : 'OFFLINE MODE'}
          </span>
        </div>
      </header>

      {/* Proactive Greeting Overlay */}
      <AnimatePresence>
        {showGreeting && greeting && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="relative z-20 mx-auto mt-4 px-8 py-3 glass-panel rounded-xl glow-border max-w-2xl text-center"
          >
            <p className="font-display text-base text-cyan-glow glow-text animate-float">
              {greeting}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Workspace Area */}
      <main className="relative z-10 flex-1 flex p-4 min-h-0 overflow-hidden">
        {activeTab === 'assistant' && (
          <div className="flex-1 flex gap-4 min-h-0 w-full">
            <aside className="w-72 hidden lg:block glass-panel rounded-xl p-4 overflow-y-auto">
              <Dashboard
                metrics={
                  metrics as {
                    total_conversations?: number;
                    decisions_made?: number;
                    tasks_completed?: number;
                    project_phase?: string;
                  }
                }
                suggestions={suggestions}
                isConnected={isConnected}
              />
            </aside>
            <section className="flex-1 glass-panel rounded-xl flex flex-col min-h-0">
              <ChatInterface
                messages={messages}
                onSend={handleSendMessage}
                isThinking={isThinking}
                followUpQuestions={followUpQuestions}
              />
            </section>
          </div>
        )}

        {activeTab === 'devices' && <DeviceDashboard />}

        {activeTab === 'knowledge' && <KnowledgeManager />}
      </main>

      {/* Voice Control Bar */}
      <footer className="relative z-10 px-6 py-3 border-t border-white/10 glass-panel">
        <VoiceControl
          isListening={isListening}
          isSpeaking={isSpeaking}
          isSupported={isSupported}
          onToggleListen={() => (isListening ? stopListening() : startListening())}
          onStopSpeaking={stopSpeaking}
        />
      </footer>

      {/* Security Confirmation Modal */}
      <HitlConfirmationModal
        isOpen={hitlModal.isOpen}
        title="Security Confirmation"
        description={hitlModal.description}
        onConfirm={() => {
          setHitlModal((prev) => ({ ...prev, isOpen: false }));
          handleSendMessage(`confirm ${hitlModal.pendingCommand}`);
        }}
        onCancel={() => setHitlModal((prev) => ({ ...prev, isOpen: false }))}
      />
    </div>
  );
}
