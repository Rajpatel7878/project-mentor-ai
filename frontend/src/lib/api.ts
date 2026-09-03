const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agent?: string;
  timestamp: Date;
  commandResults?: Array<{ success: boolean; message: string }>;
}

export interface ChatResponse {
  response: string;
  agent: string;
  session_id: string;
  follow_up_questions: string[];
  suggestions: string[];
  command_results: Array<{ success: boolean; message: string; output?: string }>;
  rag_context: string[];
}

export interface GreetingResponse {
  greeting: string;
  time_of_day: string;
  user_name: string;
  proactive_suggestions: string[];
}

export async function fetchGreeting(): Promise<GreetingResponse> {
  const res = await fetch(`${API_URL}/api/greeting`);
  if (!res.ok) throw new Error('Failed to fetch greeting');
  return res.json();
}

export async function sendChatMessage(message: string, sessionId: string): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId, execute_commands: true }),
  });
  if (!res.ok) throw new Error('Failed to send message');
  return res.json();
}

export async function fetchMetrics() {
  const res = await fetch(`${API_URL}/api/memory/metrics`);
  if (!res.ok) throw new Error('Failed to fetch metrics');
  return res.json();
}

export function getWebSocketUrl(): string {
  return `${WS_URL}/api/ws`;
}

export { API_URL, WS_URL };
