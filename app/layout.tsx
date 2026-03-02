import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Space_Grotesk } from "next/font/google";
import "./globals.css";
import LayoutShell from "@/components/layout/LayoutShell";
import { ThemeProvider } from "@/lib/theme-provider";
import { QuoteModalProvider } from "@/lib/quote-modal-context";
import { ContentProvider } from "@/lib/content-provider";
import { getSiteConfig, getNav } from "@/lib/content";
import { COMPANY } from "@/lib/constants";

function withTimeout<T>(p: Promise<T>, ms: number, fallback: T): Promise<T> {
  return Promise.race([p, new Promise<T>((r) => setTimeout(() => r(fallback), ms))]);
}

/** In development, skip DB to avoid blocking the main thread and long renders. */
const SKIP_LAYOUT_DB = process.env.NODE_ENV === "development";

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

export async function generateMetadata(): Promise<Metadata> {
  let site: Awaited<ReturnType<typeof getSiteConfig>> = null;
  if (!SKIP_LAYOUT_DB) {
    try {
      site = await withTimeout(getSiteConfig(), 2000, null);
    } catch {
      site = null;
    }
  }
  const company = site?.company ?? COMPANY;
  return {
    title: {
      template: `%s | ${company.name}`,
      default: `${company.name} | DESIGN • ENGINEER • MAINTAIN`,
    },
    description:
      `Professional commercial and domestic gas, heating and plumbing across ${company.areas}. Gas Safe registered, fast response, free quotes.`,
    openGraph: {
      type: "website",
      siteName: company.name,
    },
  };
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  let site: Awaited<ReturnType<typeof getSiteConfig>> = null;
  let nav: Awaited<ReturnType<typeof getNav>> = [];
  if (!SKIP_LAYOUT_DB) {
    try {
      [site, nav] = await Promise.all([
        withTimeout(getSiteConfig(), 2000, null),
        withTimeout(getNav(), 2000, []),
      ]);
    } catch {
      site = null;
      nav = [];
    }
  }

  return (
    <html lang="en" suppressHydrationWarning className={`${jakarta.variable} ${spaceGrotesk.variable}`}>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('dps-theme');if(!t)t='dark';document.documentElement.setAttribute('data-theme',t);if(t==='dark')document.documentElement.classList.add('dark');else document.documentElement.classList.remove('dark')}catch(e){}})()`,
          }}
        />
      </head>
      <body suppressHydrationWarning className="antialiased bg-brand-surface text-brand-text selection:bg-brand-red selection:text-white" style={{ fontFamily: "var(--font-jakarta)" }}>
        <ThemeProvider>
          <QuoteModalProvider>
            <ContentProvider
              initialSite={site ? { company: site.company, openingHours: site.openingHours } : null}
              initialNav={nav.length > 0 ? nav : null}
            >
              <LayoutShell>{children}</LayoutShell>
            </ContentProvider>
          </QuoteModalProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
