export interface SessionMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: string;
}

export interface Session {
  session_id: string;
  provider: string;
  model: string;
  status: string;
  supported_models: string[];
  created_at: string;
  expires_at?: string;
  last_activity?: string;
  message_count?: number;
  messages?: SessionMessage[];
}

export interface SessionListResponse {
  sessions: Session[];
  total: number;
  limit: number;
  offset: number;
}

export interface SessionCreateRequest {
  provider: string;
  model?: string;
  system_prompt?: string;
  context?: {
    memory?: string;
    previous_summary?: string;
    files?: Array<{ name: string; content: string }>;
  };
  ttl?: number;
  metadata?: Record<string, unknown>;
}
