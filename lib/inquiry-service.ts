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

    addInquiry: (data: Omit<Inquiry, "id" | "status" | "timestamp">) => {
        if (typeof window === "undefined") return;
        const inquiries = inquiryService.getInquiries();
        const newInquiry: Inquiry = {
            ...data,
            id: Math.random().toString(36).substring(2, 9),
            status: "pending",
            timestamp: Date.now(),
        };
        const updated = [newInquiry, ...inquiries];
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
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
