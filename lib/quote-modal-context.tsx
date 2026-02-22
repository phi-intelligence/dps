"use client";

import { createContext, useContext, useState, useCallback } from "react";
import QuoteModal from "@/components/ui/QuoteModal";

interface QuoteModalContextValue {
  openQuoteModal: (options?: { preselectedService?: string }) => void;
  closeQuoteModal: () => void;
}

const QuoteModalContext = createContext<QuoteModalContextValue | null>(null);

export function QuoteModalProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [preselectedService, setPreselectedService] = useState("");

  const openQuoteModal = useCallback(
    (options?: { preselectedService?: string }) => {
      setPreselectedService(options?.preselectedService ?? "");
      setIsOpen(true);
    },
    []
  );

  const closeQuoteModal = useCallback(() => {
    setIsOpen(false);
  }, []);

  return (
    <QuoteModalContext.Provider value={{ openQuoteModal, closeQuoteModal }}>
      {children}
      <QuoteModal
        open={isOpen}
        onClose={closeQuoteModal}
        preselectedService={preselectedService}
      />
    </QuoteModalContext.Provider>
  );
}

export function useQuoteModal(): QuoteModalContextValue {
  const ctx = useContext(QuoteModalContext);
  if (!ctx) {
    throw new Error("useQuoteModal must be used within QuoteModalProvider");
  }
  return ctx;
}
