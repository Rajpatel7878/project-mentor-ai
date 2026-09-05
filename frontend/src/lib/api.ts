const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agent?: string;
  timestamp: Date;
  commandResults?: Array<{ success: boolean; message: string; requires_confirmation?: boolean }>;
}

export interface ChatResponse {
  response: string;
  agent: string;
  session_id: string;
  follow_up_questions: string[];
  suggestions: string[];
  command_results: Array<{ success: boolean; message: string; output?: string; requires_confirmation?: boolean }>;
  rag_context: string[];
}

export interface GreetingResponse {
  greeting: string;
  time_of_day: string;
  user_name: string;
  proactive_suggestions: string[];
}

export interface Device {
  id: string;
  name: string;
  type: 'system' | 'light' | 'thermostat' | 'switch' | 'sensor' | 'lock';
  status: 'online' | 'offline' | 'warning';
  protocol: string;
  state: Record<string, any>;
  last_updated: string;
}

export interface DeviceActionResponse {
  success: boolean;
  message: string;
  device_id: string;
  new_state: Record<string, any>;
  requires_confirmation: boolean;
}

export interface TelemetrySnapshot {
  timestamp: string;
  system: {
    os?: string;
    cpu_percent?: number;
    ram_percent?: number;
    disk_percent?: number;
    power_plugged?: boolean;
  };
  devices: Device[];
}

export interface DocumentInfo {
  name: string;
  size_bytes: number;
  chunk_count: number;
  format: string;
  uploaded_at: string;
}

export interface RAGSearchResponse {
  query: string;
  results: Array<{
    text: string;
    source: string;
    relevance: number;
    format: string;
  }>;
  retrieval_mode: string;
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

// Device & IoT APIs
export async function fetchDevices(): Promise<Device[]> {
  const res = await fetch(`${API_URL}/api/devices`);
  if (!res.ok) throw new Error('Failed to fetch devices');
  return res.json();
}

export async function fetchTelemetry(): Promise<TelemetrySnapshot> {
  const res = await fetch(`${API_URL}/api/devices/telemetry`);
  if (!res.ok) throw new Error('Failed to fetch telemetry');
  return res.json();
}

export async function executeDeviceAction(
  deviceId: string,
  action: string,
  params: Record<string, any> = {},
  confirm: boolean = false
): Promise<DeviceActionResponse> {
  const res = await fetch(`${API_URL}/api/devices/${deviceId}/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, params, confirm }),
  });
  if (!res.ok) throw new Error(`Device action failed: ${res.statusText}`);
  return res.json();
}

// RAG & Knowledge Base APIs
export async function fetchDocuments(): Promise<DocumentInfo[]> {
  const res = await fetch(`${API_URL}/api/rag/documents`);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

export async function uploadDocument(file: File): Promise<DocumentInfo> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_URL}/api/rag/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(errorData.detail || 'Failed to upload document');
  }
  return res.json();
}

export async function deleteDocument(filename: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/rag/documents/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete document');
}

export async function refreshRAG(): Promise<{ status: string; document_count: number }> {
  const res = await fetch(`${API_URL}/api/rag/refresh`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to refresh knowledge base');
  return res.json();
}

export async function searchRAG(query: string, mode: string = 'hybrid'): Promise<RAGSearchResponse> {
  const res = await fetch(`${API_URL}/api/rag/search?q=${encodeURIComponent(query)}&mode=${mode}`);
  if (!res.ok) throw new Error('Failed to search knowledge base');
  return res.json();
}

// Swappable Agent Registry APIs
export interface AgentInfo {
  name: string;
  display_name: string;
  role_description: string;
  category: string;
  color_scheme: string;
  keywords: string[];
  follow_up_questions: string[];
  suggestions: string[];
}

export async function fetchAgents(): Promise<AgentInfo[]> {
  const res = await fetch(`${API_URL}/api/agents`);
  if (!res.ok) throw new Error('Failed to fetch registered agents');
  return res.json();
}

// Client Intake & Template Recommendation APIs
export interface ClientTemplate {
  id: string;
  name: string;
  tagline: string;
  description: string;
  primary_agents: string[];
  recommended_tools: string[];
  setup_time: string;
  monthly_token_estimate: number;
  gemini_monthly_cost_usd: number;
  gpt4_monthly_cost_usd: number;
  key_benefits: string[];
}

export interface IntakeAnalysisResult {
  company_name: string;
  recommended_template: ClientTemplate;
  fit_score: number;
  rationale: string;
  roi_projections: {
    monthly_tokens: number;
    gemini_monthly_cost_usd: number;
    gpt4_equivalent_monthly_usd: number;
    monthly_savings_usd: number;
    annual_savings_usd: number;
    savings_percentage: number;
  };
  implementation_roadmap: string[];
  all_scores: Record<string, number>;
}

export async function fetchIntakeTemplates(): Promise<ClientTemplate[]> {
  const res = await fetch(`${API_URL}/api/intake/templates`);
  if (!res.ok) throw new Error('Failed to fetch intake templates');
  return res.json();
}

export async function analyzeIntake(profile: {
  company_name: string;
  problem_statement: string;
  primary_goal?: string;
  current_tools?: string;
  team_size?: string;
}): Promise<IntakeAnalysisResult> {
  const res = await fetch(`${API_URL}/api/intake/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile),
  });
  if (!res.ok) throw new Error('Failed to analyze client intake');
  return res.json();
}

// Usage & Cost Analytics Dashboard APIs
export interface AnalyticsSummary {
  total_calls: number;
  total_tokens: number;
  total_input_tokens: number;
  total_output_tokens: number;
  avg_latency_ms: number;
  total_cost_usd: number;
  gpt4_equivalent_cost_usd: number;
  estimated_savings_usd: number;
  savings_percentage: number;
  agent_breakdown: Record<
    string,
    {
      calls: number;
      input_tokens: number;
      output_tokens: number;
      total_tokens: number;
      avg_latency_ms: number;
      cost_usd: number;
    }
  >;
  model: string;
  recent_activity: Array<{
    timestamp: string;
    agent: string;
    input_tokens: number;
    output_tokens: number;
    latency_ms: number;
    cost_usd: number;
    gpt4_cost_usd: number;
    success: boolean;
  }>;
}

export async function fetchUsageAnalytics(): Promise<AnalyticsSummary> {
  const res = await fetch(`${API_URL}/api/analytics/usage`);
  if (!res.ok) throw new Error('Failed to fetch usage analytics');
  return res.json();
}

export async function resetUsageAnalytics(): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_URL}/api/analytics/reset`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to reset usage analytics');
  return res.json();
}

export function getWebSocketUrl(): string {
  return `${WS_URL}/api/ws`;
}

export { API_URL, WS_URL };

