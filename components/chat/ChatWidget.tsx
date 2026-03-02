"use client";

import { useState, lazy, Suspense } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageCircle, X, AlertCircle } from "lucide-react";

function ChatLoadErrorFallback() {
  return (
    <div className="chat-panel-inner w-full h-full rounded-2xl flex flex-col items-center justify-center gap-4 p-6 text-center">
      <AlertCircle size={32} className="text-brand-red" />
      <p className="text-brand-muted text-sm font-technical uppercase tracking-wider">
        Could not load chat. Please refresh the page.
      </p>
    </div>
  );
}

const ChatPanel = lazy(() =>
  import("./ChatPanel").catch(() => ({ default: ChatLoadErrorFallback }))
);

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [hasOpened, setHasOpened] = useState(false);

  const handleToggle = () => {
    if (!hasOpened) setHasOpened(true);
    setOpen((prev) => !prev);
  };

  return (
    <>
      <div
        className="fixed bottom-6 right-6 z-[100] flex flex-col items-end gap-4"
        aria-label="Chat"
      >
        <AnimatePresence mode="wait">
          {open && hasOpened && (
            <motion.div
              key="panel"
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="chat-panel-opaque fixed bottom-24 right-6 w-[calc(100vw-3rem)] sm:w-[420px] h-[600px] max-h-[80vh] rounded-3xl z-[101] border border-brand-card-border shadow-2xl overflow-hidden"
            >
              <Suspense
                fallback={
                  <div className="chat-panel-inner w-full h-full rounded-2xl flex items-center justify-center">
                    <div className="w-8 h-8 border-2 border-brand-red border-t-transparent rounded-full animate-spin" />
                  </div>
                }
              >
                <ChatPanel />
              </Suspense>
            </motion.div>
          )}
        </AnimatePresence>

        <motion.button
          type="button"
          onClick={handleToggle}
          className="w-14 h-14 rounded-full bg-brand-red text-white flex items-center justify-center shadow-lg shadow-brand-red/30 hover:bg-brand-red/90 transition-colors z-[102]"
          aria-label={open ? "Close chat" : "Open chat"}
        >
          <AnimatePresence mode="wait">
            {open ? (
              <motion.span
                key="close"
                initial={{ opacity: 0, rotate: -90 }}
                animate={{ opacity: 1, rotate: 0 }}
                exit={{ opacity: 0, rotate: 90 }}
                transition={{ duration: 0.2 }}
              >
                <X size={24} />
              </motion.span>
            ) : (
              <motion.span
                key="open"
                initial={{ opacity: 0, rotate: 90 }}
                animate={{ opacity: 1, rotate: 0 }}
                exit={{ opacity: 0, rotate: -90 }}
                transition={{ duration: 0.2 }}
              >
                <MessageCircle size={24} />
              </motion.span>
            )}
          </AnimatePresence>
        </motion.button>
      </div>
    </>
  );
}
