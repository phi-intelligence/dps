import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Space_Grotesk } from "next/font/google";
import "./globals.css";
import LayoutShell from "@/components/layout/LayoutShell";
import { ThemeProvider } from "@/lib/theme-provider";
import { QuoteModalProvider } from "@/lib/quote-modal-context";
import { COMPANY } from "@/lib/constants";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-jakarta",
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    template: `%s | ${COMPANY.name}`,
    default: `${COMPANY.name} | Heating & Air Conditioning`,
  },
  description:
    `Professional heating and air conditioning services across ${COMPANY.areas}. Gas Safe registered engineers, fast response, free quotes.`,
  openGraph: {
    type: "website",
    siteName: COMPANY.name,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className={`${jakarta.variable} ${spaceGrotesk.variable}`}>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('dps-theme');if(!t)t='light';document.documentElement.setAttribute('data-theme',t);if(t==='dark')document.documentElement.classList.add('dark');else document.documentElement.classList.remove('dark')}catch(e){}})()`,
          }}
        />
      </head>
      <body suppressHydrationWarning className="antialiased bg-brand-surface text-brand-text selection:bg-brand-red selection:text-white" style={{ fontFamily: "var(--font-jakarta)" }}>
        <ThemeProvider>
          <QuoteModalProvider>
            <LayoutShell>{children}</LayoutShell>
          </QuoteModalProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
