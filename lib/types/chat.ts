export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

export interface ChatRequest {
  messages: Array<{ role: "user" | "assistant"; content: string }>;
}
