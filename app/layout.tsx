import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Space_Grotesk } from "next/font/google";
import "./globals.css";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import { ThemeProvider } from "@/lib/theme-provider";
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
    default: `${COMPANY.name} | Heating, Plumbing & Air Conditioning`,
  },
  description:
    `Professional heating, plumbing and air conditioning services in ${COMPANY.areas}. Gas Safe registered engineers, fast response, free quotes.`,
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
            __html: `(function(){try{var t=localStorage.getItem('dps-theme');if(!t)t=window.matchMedia('(prefers-color-scheme:light)').matches?'light':'dark';document.documentElement.setAttribute('data-theme',t)}catch(e){}})()`,
          }}
        />
      </head>
      <body suppressHydrationWarning className="antialiased bg-brand-surface text-brand-text selection:bg-brand-red selection:text-white" style={{ fontFamily: "var(--font-jakarta)" }}>
        <ThemeProvider>
          <a href="#main-content" className="skip-link">
            Skip to main content
          </a>
          <Header />
          <main id="main-content" className="relative z-10">{children}</main>
          <Footer />
        </ThemeProvider>
      </body>
    </html>
  );
}
