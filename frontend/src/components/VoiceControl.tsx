'use client';

import { motion } from 'framer-motion';
import { Mic, MicOff, Volume2, VolumeX } from 'lucide-react';

interface VoiceControlProps {
  isListening: boolean;
  isSpeaking: boolean;
  isSupported: boolean;
  onToggleListen: () => void;
  onStopSpeaking: () => void;
}

export function VoiceControl({ isListening, isSpeaking, isSupported, onToggleListen, onStopSpeaking }: VoiceControlProps) {
  if (!isSupported) {
    return (
      <div className="text-xs text-white/40 text-center">
        Voice not supported in this browser
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center gap-4">
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onToggleListen}
        className={`relative p-4 rounded-full border-2 transition-all ${
          isListening
            ? 'border-cyan-glow bg-cyan-glow/20 animate-pulse-glow'
            : 'border-white/20 bg-white/5 hover:border-cyan-glow/50'
        }`}
        title={isListening ? 'Stop listening' : 'Start listening'}
      >
        {isListening ? (
          <Mic className="w-6 h-6 text-cyan-glow" />
        ) : (
          <MicOff className="w-6 h-6 text-white/60" />
        )}
        {isListening && (
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-cyan-glow"
            animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        )}
      </motion.button>

      {isSpeaking && (
        <motion.button
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          whileHover={{ scale: 1.05 }}
          onClick={onStopSpeaking}
          className="p-3 rounded-full border border-purple-500/50 bg-purple-500/10"
          title="Stop speaking"
        >
          <VolumeX className="w-5 h-5 text-purple-400" />
        </motion.button>
      )}

      {!isSpeaking && isListening && (
        <div className="flex items-center gap-2 text-xs text-cyan-glow/60">
          <Volume2 className="w-4 h-4" />
          <span>Say &quot;Hey Mentor&quot; or &quot;Jarvis&quot;</span>
        </div>
      )}
    </div>
  );
}
