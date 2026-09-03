'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { getWebSocketUrl } from '@/lib/api';

interface WebSocketMessage {
  type: string;
  payload: Record<string, unknown>;
}

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout>();
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(getWebSocketUrl());

    ws.onopen = () => {
      setIsConnected(true);
      optionsRef.current.onConnect?.();
    };

    ws.onclose = () => {
      setIsConnected(false);
      optionsRef.current.onDisconnect?.();
      reconnectTimeout.current = setTimeout(connect, 3000);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as WebSocketMessage;
      if (data.type === 'thinking') setIsThinking(true);
      if (data.type === 'response' || data.type === 'greeting') setIsThinking(false);
      optionsRef.current.onMessage?.(data);
    };

    ws.onerror = () => ws.close();
    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimeout.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((type: string, payload: Record<string, unknown> = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, ...payload }));
    }
  }, []);

  const sendChat = useCallback((message: string, sessionId: string) => {
    send('chat', { message, session_id: sessionId, execute_commands: true });
  }, [send]);

  const requestGreeting = useCallback(() => {
    send('greeting');
  }, [send]);

  return { isConnected, isThinking, sendChat, requestGreeting, send };
}
