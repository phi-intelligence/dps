"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import type { ChatMessage as ChatMessageType } from "@/lib/types/chat";

interface ChatMessageProps {
  message: ChatMessageType;
}

function parseContent(content: string): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = linkRegex.exec(content)) !== null) {
    const [full, text, href] = match;
    const isInternal = href.startsWith("/");

    if (match.index > lastIndex) {
      nodes.push(content.slice(lastIndex, match.index));
    }
    if (isInternal) {
      nodes.push(
        <Link
          key={`${match.index}-${href}`}
          href={href}
          className="underline text-brand-red hover:text-brand-red/80 transition-colors"
        >
          {text}
        </Link>
      );
    } else {
      nodes.push(
        <a
          key={`${match.index}-${href}`}
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="underline text-brand-red hover:text-brand-red/80 transition-colors"
        >
          {text}
        </a>
      );
    }
    lastIndex = match.index + full.length;
  }

  if (lastIndex < content.length) {
    nodes.push(content.slice(lastIndex));
  }

  return nodes.length > 0 ? nodes : [content];
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const isEmpty = !message.content.trim();

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-brand-red text-white rounded-br-md"
            : "bg-brand-card border border-brand-card-border text-brand-text rounded-bl-md"
        }`}
      >
        {isEmpty && message.role === "assistant" ? (
          <div className="flex gap-1 py-1" aria-label="Typing">
            <span className="w-2 h-2 rounded-full bg-brand-muted animate-bounce [animation-delay:0ms]" />
            <span className="w-2 h-2 rounded-full bg-brand-muted animate-bounce [animation-delay:150ms]" />
            <span className="w-2 h-2 rounded-full bg-brand-muted animate-bounce [animation-delay:300ms]" />
          </div>
        ) : (
          <p className="text-sm font-light leading-relaxed whitespace-pre-wrap">
            {parseContent(message.content)}
          </p>
        )}
      </div>
    </motion.div>
  );
}
