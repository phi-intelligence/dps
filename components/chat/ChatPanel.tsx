"use client";

import { useRef, useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ICON_MAP } from "@/lib/icons";
import { useChat } from "@/lib/hooks/use-chat";
import { QUICK_ACTIONS } from "@/lib/chat-config";
import ChatMessage from "./ChatMessage";

export default function ChatPanel() {
  const { messages, isStreaming, sendMessage, clearChat } = useChat();
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const input = inputRef.current;
    if (input?.value.trim()) {
      sendMessage(input.value.trim());
      input.value = "";
    }
  };

  const SendIcon = ICON_MAP.send;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, y: 20 }}
      transition={{ type: "spring", damping: 25, stiffness: 300 }}
      className="chat-panel-inner flex flex-col w-full h-full rounded-2xl overflow-hidden"
    >
      {/* Header */}
      <div className="chat-panel-header flex items-center justify-between px-5 py-4 border-b border-brand-card-border shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-brand-red animate-pulse" />
          <span className="font-technical font-bold text-brand-text text-sm tracking-widest uppercase">
            DPS Assistant
          </span>
          <span className="text-brand-muted text-[10px] font-technical uppercase tracking-wider">
            {isStreaming ? "Typing..." : "Online"}
          </span>
        </div>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="chat-panel-messages flex-1 overflow-y-auto p-4 space-y-4 min-h-0"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full min-h-[200px] text-center px-4">
            <p className="text-brand-muted text-sm font-technical uppercase tracking-wider mb-8">
              How can we help?
            </p>
            <div className="grid grid-cols-2 gap-3 w-full max-w-[280px]">
              {QUICK_ACTIONS.map((action) =>
                action.href.startsWith("tel:") ? (
                  <a
                    key={action.label}
                    href={action.href}
                    className="chat-panel-btn px-4 py-3 rounded-xl border border-brand-card-border-hover hover:border-brand-red/20 text-brand-text text-[10px] font-technical font-bold uppercase tracking-widest transition-all text-center"
                  >
                    {action.label}
                  </a>
                ) : (
                  <Link
                    key={action.label}
                    href={action.href}
                    className="chat-panel-btn px-4 py-3 rounded-xl border border-brand-card-border-hover hover:border-brand-red/20 text-brand-text text-[10px] font-technical font-bold uppercase tracking-widest transition-all text-center"
                  >
                    {action.label}
                  </Link>
                )
              )}
            </div>
          </div>
        ) : (
          messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="chat-panel-form p-4 border-t border-brand-card-border shrink-0">
        <div className="flex gap-3 items-center">
          <input
            ref={inputRef}
            type="text"
            placeholder="Type your message..."
            disabled={isStreaming}
            className="chat-panel-btn flex-1 border border-brand-card-border-hover rounded-full px-5 py-3 text-brand-text text-sm placeholder-brand-muted/50 focus:outline-none focus:border-brand-red/50 transition-all disabled:opacity-60"
            aria-label="Message"
          />
          <button
            type="submit"
            disabled={isStreaming}
            className="w-12 h-12 rounded-full bg-brand-red text-white flex items-center justify-center shrink-0 hover:bg-brand-red/90 transition-all disabled:opacity-60 disabled:pointer-events-none"
            aria-label="Send"
          >
            <SendIcon size={20} />
          </button>
        </div>
      </form>
    </motion.div>
  );
}
