'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Cpu, Zap } from 'lucide-react';
import { ParticleBackground } from './ParticleBackground';
import { ChatInterface } from './ChatInterface';
import { VoiceControl } from './VoiceControl';
import { Dashboard } from './Dashboard';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useVoice } from '@/hooks/useVoice';
import { fetchGreeting, fetchMetrics, sendChatMessage, type ChatMessage } from '@/lib/api';

const SESSION_ID = 'default';

export function MentorDashboard() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [greeting, setGreeting] = useState('');
  const [showGreeting, setShowGreeting] = useState(true);
  const [followUpQuestions, setFollowUpQuestions] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [metrics, setMetrics] = useState<Record<string, unknown>>({});
  const [useRestFallback, setUseRestFallback] = useState(false);

  const speakRef = useRef<(text: string) => void>(() => {});
  const sendChatRef = useRef<(message: string, sessionId: string) => void>(() => {});
  const isConnectedRef = useRef(false);

  const appendAssistantMessage = useCallback(
    (content: string, agent?: string, commandResults?: Array<{ success: boolean; message: string }>) => {
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
    },
    []
  );

  const handleWsMessage = useCallback((data: { type: string; payload: Record<string, unknown> }) => {
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
        command_results: Array<{ success: boolean; message: string }>;
      };
      setFollowUpQuestions(payload.follow_up_questions || []);
      setSuggestions(payload.suggestions || []);
      appendAssistantMessage(payload.response, payload.agent, payload.command_results);
    }
  }, [appendAssistantMessage]);

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

  const handleSendMessage = useCallback(async (text: string) => {
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
  }, [useRestFallback, appendAssistantMessage]);

  const { isListening, isSpeaking, isSupported, startListening, stopListening, speak, stopSpeaking } = useVoice({
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

      <header className="relative z-10 flex items-center justify-between px-6 py-4 border-b border-white/10 glass-panel">
        <div className="flex items-center gap-4">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
            className="p-2 rounded-full border border-cyan-glow/30"
          >
            <Cpu className="w-8 h-8 text-cyan-glow" />
          </motion.div>
          <div>
            <h1 className="font-display text-xl tracking-widest glow-text">PROJECT MENTOR AI</h1>
            <p className="text-xs text-white/40 tracking-wider">JARVIS-INSPIRED INTELLIGENCE SYSTEM</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Zap className={`w-4 h-4 ${isConnected ? 'text-green-400' : 'text-red-400'}`} />
          <span className="text-xs font-display tracking-wider">{isConnected ? 'SYSTEMS ONLINE' : 'OFFLINE MODE'}</span>
        </div>
      </header>

      <AnimatePresence>
        {showGreeting && greeting && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="relative z-20 mx-auto mt-6 px-8 py-4 glass-panel rounded-xl glow-border max-w-2xl text-center"
          >
            <p className="font-display text-lg text-cyan-glow glow-text animate-float">{greeting}</p>
          </motion.div>
        )}
      </AnimatePresence>

      <main className="relative z-10 flex-1 flex gap-4 p-4 min-h-0">
        <aside className="w-72 hidden lg:block glass-panel rounded-xl p-4 overflow-y-auto">
          <Dashboard
            metrics={metrics as { total_conversations?: number; decisions_made?: number; tasks_completed?: number; project_phase?: string }}
            suggestions={suggestions}
            isConnected={isConnected}
          />
        </aside>
        <section className="flex-1 glass-panel rounded-xl flex flex-col min-h-0">
          <ChatInterface messages={messages} onSend={handleSendMessage} isThinking={isThinking} followUpQuestions={followUpQuestions} />
        </section>
      </main>

      <footer className="relative z-10 px-6 py-4 border-t border-white/10 glass-panel">
        <VoiceControl
          isListening={isListening}
          isSpeaking={isSpeaking}
          isSupported={isSupported}
          onToggleListen={() => (isListening ? stopListening() : startListening())}
          onStopSpeaking={stopSpeaking}
        />
      </footer>
    </div>
  );
}
