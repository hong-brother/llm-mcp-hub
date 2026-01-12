export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatCompletionRequest {
  messages: ChatMessage[];
  provider?: string;
  model?: string;
  stream?: boolean;
  timeout?: number;
}

export interface ChatCompletionResponse {
  response: string;
  session_id: string | null;
  provider: string;
  model: string;
}
