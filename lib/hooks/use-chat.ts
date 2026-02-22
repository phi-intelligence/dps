"use client";

import { useState, useRef, useCallback } from "react";
import type { ChatMessage } from "@/lib/types/chat";

function generateId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    const trimmed = content.trim();
    if (!trimmed || isStreaming) return;

    const userMessage: ChatMessage = {
      id: generateId(),
      role: "user",
      content: trimmed,
      timestamp: Date.now(),
    };
    const assistantMessage: ChatMessage = {
      id: generateId(),
      role: "assistant",
      content: "",
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setIsStreaming(true);

    abortRef.current = new AbortController();
    const signal = abortRef.current.signal;

    try {
      const history = [...messages, userMessage].map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history }),
        signal,
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const errorText = data?.error ?? `Error ${res.status}`;
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessage.id
              ? { ...msg, content: `Sorry, something went wrong. ${errorText}` }
              : msg
          )
        );
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessage.id
              ? { ...msg, content: "No response stream." }
              : msg
          )
        );
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const json = JSON.parse(line.slice(6)) as {
                content?: string;
                done?: boolean;
                error?: string;
              };
              if (json.error) {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessage.id
                      ? { ...msg, content: `Error: ${json.error}` }
                      : msg
                  )
                );
                break;
              }
              if (json.content !== undefined) {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessage.id
                      ? { ...msg, content: msg.content + (json.content ?? "") }
                      : msg
                  )
                );
              }
            } catch {
              // skip malformed line
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessage.id
            ? { ...msg, content: "Connection failed. Please try again." }
            : msg
        )
      );
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }, [messages, isStreaming]);

  const clearChat = useCallback(() => {
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = null;
    setMessages([]);
    setIsStreaming(false);
  }, []);

  return { messages, isStreaming, sendMessage, clearChat };
}
