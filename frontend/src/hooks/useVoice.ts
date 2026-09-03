'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

// Speech recognition type definitions for cross-browser compatibility
type SpeechRecognitionInstance = any;
type SpeechRecognitionEventInstance = any;

interface UseVoiceOptions {
  onTranscript?: (text: string) => void;
  onWakeWord?: () => void;
  wakeWords?: string[];
  continuous?: boolean;
}

export function useVoice(options: UseVoiceOptions = {}) {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const wakeWords = options.wakeWords || ['hey mentor', 'jarvis'];

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    setIsSupported(true);
    const recognition = new SpeechRecognition();
    recognition.continuous = options.continuous ?? true;
    recognition.interimResults = true;
    recognition.lang = 'en-GB';

    recognition.onresult = (event: SpeechRecognitionEventInstance) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        }
      }

      if (finalTranscript) {
        const lower = finalTranscript.toLowerCase().trim();
        setTranscript(finalTranscript);

        if (wakeWords.some((w) => lower.includes(w))) {
          options.onWakeWord?.();
          const command = lower.replace(new RegExp(wakeWords.join('|'), 'gi'), '').trim();
          if (command) options.onTranscript?.(command);
        } else if (isListening) {
          options.onTranscript?.(finalTranscript.trim());
        }
      }
    };

    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => {
      if (isListening) recognition.start();
    };

    recognitionRef.current = recognition;
  }, [options.continuous, wakeWords, isListening]);

  const startListening = useCallback(() => {
    if (recognitionRef.current && !isListening) {
      setIsListening(true);
      recognitionRef.current.start();
    }
  }, [isListening]);

  const stopListening = useCallback(() => {
    setIsListening(false);
    recognitionRef.current?.stop();
  }, []);

  const speak = useCallback((text: string) => {
    if (!window.speechSynthesis) return;

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-GB';
    utterance.rate = 0.95;
    utterance.pitch = 0.9;

    const voices = window.speechSynthesis.getVoices();
    const britishVoice = voices.find(
      (v) => v.lang.startsWith('en-GB') || v.name.toLowerCase().includes('british')
    );
    if (britishVoice) utterance.voice = britishVoice;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
  }, []);

  const stopSpeaking = useCallback(() => {
    window.speechSynthesis?.cancel();
    setIsSpeaking(false);
  }, []);

  return {
    isListening,
    isSpeaking,
    isSupported,
    transcript,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
  };
}

declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}
