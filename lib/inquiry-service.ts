"use client";

export interface Inquiry {
  id: string;
  name: string;
  phone: string;
  email: string;
  service: string;
  message: string;
  status: "pending" | "contacted" | "completed" | "archived";
  timestamp: number;
}

const STORAGE_KEY = "dps_inquiries";

export const inquiryService = {
  getInquiries: (): Inquiry[] => {
    if (typeof window === "undefined") return [];
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  },

  /** Submit inquiry: tries API first, falls back to localStorage if API fails (e.g. offline). */
  addInquiry: async (
    data: Omit<Inquiry, "id" | "status" | "timestamp">
  ): Promise<Inquiry | undefined> => {
    if (typeof window === "undefined") return undefined;
    try {
      const res = await fetch("/api/content/inquiries", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (res.ok) {
        const json = await res.json();
        return {
          ...data,
          id: json.id,
          status: json.status ?? "pending",
          timestamp: json.timestamp ? new Date(json.timestamp).getTime() : Date.now(),
        };
      }
    } catch {
      // fall through to localStorage fallback
    }
    const inquiries = inquiryService.getInquiries();
    const newInquiry: Inquiry = {
      ...data,
      id: Math.random().toString(36).substring(2, 9),
      status: "pending",
      timestamp: Date.now(),
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify([newInquiry, ...inquiries]));
    return newInquiry;
  },

  updateInquiryStatus: (id: string, status: Inquiry["status"]) => {
    if (typeof window === "undefined") return;
    const inquiries = inquiryService.getInquiries();
    const updated = inquiries.map((inq) =>
      inq.id === id ? { ...inq, status } : inq
    );
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  },

  deleteInquiry: (id: string) => {
    if (typeof window === "undefined") return;
    const inquiries = inquiryService.getInquiries();
    const updated = inquiries.filter((inq) => inq.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  },
};
