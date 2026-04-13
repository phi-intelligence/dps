import { NextRequest, NextResponse } from "next/server";
import { readFileSync } from "fs";
import { join } from "path";
import { GoogleGenerativeAI } from "@google/generative-ai";
import OpenAI from "openai";
import { getSiteConfig, getServiceAreas } from "@/lib/content";
import { COMPANY, SERVICE_AREAS, OPENING_HOURS } from "@/lib/constants";
import { SERVICE_MAP } from "@/lib/chat-config";
import type { ChatRequest } from "@/lib/types/chat";

function withTimeout<T>(p: Promise<T>, ms: number, timeoutMessage: string): Promise<T> {
  return Promise.race([
    p,
    new Promise<T>((_resolve, reject) =>
      setTimeout(() => reject(new Error(timeoutMessage)), ms)
    ),
  ]);
}

async function retryOnce<T>(fn: () => Promise<T>, label: string): Promise<T> {
  try {
    return await fn();
  } catch (firstError) {
    try {
      return await fn();
    } catch (secondError) {
      console.error(`[chat] ${label} failed twice`, {
        first: String(firstError),
        second: String(secondError),
      });
      throw secondError;
    }
  }
}

function isTransientGeminiError(error: unknown): boolean {
  const text = String(error).toLowerCase();
  return (
    text.includes("503") ||
    text.includes("429") ||
    text.includes("unavailable") ||
    text.includes("resource_exhausted") ||
    text.includes("high demand") ||
    text.includes("timeout")
  );
}

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Prefer key from .env.local on disk so restarts aren't needed when key is updated. */
function getGeminiApiKey(): string | undefined {
  try {
    const path = join(process.cwd(), ".env.local");
    const content = readFileSync(path, "utf8");
    const match = content.match(/^\s*GEMINI_API_KEY\s*=\s*(.+?)\s*$/m);
    if (match) {
      const value = match[1].trim().replace(/^["']|["']$/g, "");
      if (value.length > 0) return value;
    }
  } catch {
    // ignore
  }
  return process.env.GEMINI_API_KEY;
}

async function buildSystemPrompt(): Promise<string> {
  const [site, areas] = await Promise.all([getSiteConfig(), getServiceAreas()]);
  const company = site?.company ?? COMPANY;
  const hours = site?.openingHours ?? OPENING_HOURS;
  const areaList = areas.length > 0 ? areas : SERVICE_AREAS;

  const servicesList = Object.values(SERVICE_MAP).flatMap((cat) =>
    cat.services.map((s) => `- ${s.label}: ${s.href}`)
  );

  return `You are the DPS Heating Services virtual assistant.

COMPANY: ${company.name}, ${company.phone}, ${company.email}, Gas Safe: ${company.gasSafeNumber}
AREAS: ${areaList.join(", ")}
SERVICES:
${servicesList.join("\n")}
HOURS: Mon-Fri ${hours.weekday}, Sat ${hours.saturday}, Sun ${hours.sunday}

RULES:
1. Use British English. Be professional and concise (2-4 sentences).
2. Provide page links as [text](/path) markdown.
3. For gas emergencies, always say "Call 0800 111 999 immediately".
4. For booking, direct to /contact or suggest calling.
5. For pricing, give general guidance only and recommend /contact for a formal quote.
6. Never invent information or discuss competitors.
7. Suggest /tools for the Service Finder when users are unsure which service they need.`;
}

function messagesToGeminiHistory(
  messages: Array<{ role: "user" | "assistant"; content: string }>
): Array<{ role: string; parts: { text: string }[] }> {
  const history: Array<{ role: string; parts: { text: string }[] }> = [];
  for (const m of messages) {
    const role = m.role === "user" ? "user" : "model";
    history.push({ role, parts: [{ text: m.content }] });
  }
  return history;
}

async function streamGemini(
  systemPrompt: string,
  messages: Array<{ role: "user" | "assistant"; content: string }>
): Promise<ReadableStream<Uint8Array>> {
  const apiKey = getGeminiApiKey();
  if (!apiKey) throw new Error("GEMINI_API_KEY not set");

  const genAI = new GoogleGenerativeAI(apiKey);
  const allButLast = messages.slice(0, -1);
  const lastMessage = messages[messages.length - 1];
  if (!lastMessage || lastMessage.role !== "user") throw new Error("No user message");

  const history = messagesToGeminiHistory(allButLast);
  const modelsToTry = ["gemini-2.5-flash", "gemini-2.0-flash"];
  let result:
    | Awaited<ReturnType<ReturnType<GoogleGenerativeAI["getGenerativeModel"]>["startChat"]>["sendMessageStream"]>
    | undefined;
  let lastError: unknown;

  for (const modelName of modelsToTry) {
    for (let attempt = 1; attempt <= 3; attempt += 1) {
      try {
        const model = genAI.getGenerativeModel({
          model: modelName,
          systemInstruction: systemPrompt,
        });
        const chat = model.startChat({ history: history as never[] });
        result = await withTimeout(
          chat.sendMessageStream(lastMessage.content),
          25000,
          `Gemini request timed out (${modelName})`
        );
        break;
      } catch (error) {
        lastError = error;
        if (!isTransientGeminiError(error) || attempt === 3) break;
        await wait(350 * 2 ** (attempt - 1));
      }
    }
    if (result) break;
  }

  if (!result) {
    throw new Error(`Gemini unavailable across models: ${String(lastError)}`);
  }

  const encoder = new TextEncoder();
  return new ReadableStream({
    async start(controller) {
      try {
        for await (const chunk of result.stream) {
          const text = chunk.text?.() ?? "";
          if (text) {
            controller.enqueue(
              encoder.encode(`data: ${JSON.stringify({ content: text, done: false })}\n\n`)
            );
          }
        }
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify({ content: "", done: true })}\n\n`)
        );
      } catch (e) {
        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({ content: "", done: true, error: String(e) })}\n\n`
          )
        );
      } finally {
        controller.close();
      }
    },
  });
}

async function streamOpenAI(
  systemPrompt: string,
  messages: Array<{ role: "user" | "assistant"; content: string }>
): Promise<ReadableStream<Uint8Array>> {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) throw new Error("OPENAI_API_KEY not set");

  const openai = new OpenAI({ apiKey });
  const openAIMessages: OpenAI.Chat.ChatCompletionMessageParam[] = [
    { role: "system", content: systemPrompt },
    ...messages.map((m) => ({
      role: m.role as "user" | "assistant",
      content: m.content,
    })),
  ];

  const stream = await withTimeout(
    openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: openAIMessages,
      stream: true,
    }),
    25000,
    "OpenAI request timed out"
  );

  const encoder = new TextEncoder();
  return new ReadableStream({
    async start(controller) {
      try {
        for await (const chunk of stream) {
          const content = chunk.choices[0]?.delta?.content;
          if (content) {
            controller.enqueue(
              encoder.encode(`data: ${JSON.stringify({ content, done: false })}\n\n`)
            );
          }
        }
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify({ content: "", done: true })}\n\n`)
        );
      } catch (e) {
        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({ content: "", done: true, error: String(e) })}\n\n`
          )
        );
      } finally {
        controller.close();
      }
    },
  });
}

function buildFallbackMessage(
  messages: Array<{ role: "user" | "assistant"; content: string }>
): string {
  const userMessage = [...messages].reverse().find((m) => m.role === "user")?.content ?? "";
  const lower = userMessage.toLowerCase();

  if (lower.includes("service")) {
    return "We offer commercial and domestic Mechanical, Plumbing, Electrical, and Gas services. You can explore all options at [/services](/services), or tell me your issue and I will point you to the right page.";
  }
  if (lower.includes("area") || lower.includes("location") || lower.includes("where")) {
    return "We cover London, Kent, Essex and Surrey. For service-area details, see [/service-areas](/service-areas).";
  }
  if (lower.includes("price") || lower.includes("cost") || lower.includes("quote")) {
    return "Costs depend on the job scope and access. For an accurate quote, please use [/contact](/contact) or call us on +44 07932 403830.";
  }
  if (lower.includes("emergency") || lower.includes("gas leak") || lower.includes("smell gas")) {
    return "If you suspect a gas leak, call 0800 111 999 immediately. For urgent non-gas issues, call +44 07932 403830 and we will assist as quickly as possible.";
  }

  return "I can help with our services, coverage areas, and booking guidance. Visit [/services](/services) or [/contact](/contact), or call us on +44 07932 403830.";
}

function fallbackSseStream(
  messages: Array<{ role: "user" | "assistant"; content: string }>
): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  const fallback = buildFallbackMessage(messages);

  return new ReadableStream({
    start(controller) {
      controller.enqueue(
        encoder.encode(`data: ${JSON.stringify({ content: fallback, done: false })}\n\n`)
      );
      controller.enqueue(
        encoder.encode(`data: ${JSON.stringify({ content: "", done: true })}\n\n`)
      );
      controller.close();
    },
  });
}

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as ChatRequest;
    const { messages } = body;
    if (!Array.isArray(messages) || messages.length === 0) {
      return NextResponse.json(
        { error: "messages array required" },
        { status: 400 }
      );
    }

    const systemPrompt = await withTimeout(
      buildSystemPrompt(),
      4000,
      "System prompt build timed out"
    );
    // Do not log API key presence, length, or prefixes — ends up in server logs / APM.
    // const geminiKey = getGeminiApiKey();
    // const prefix = geminiKey ? geminiKey.slice(0, 8) + "..." : "none";
    // console.log("[chat] GEMINI_API_KEY:", geminiKey ? `set (${geminiKey.length} chars)` : "MISSING", "prefix:", prefix);

    try {
      const stream = await retryOnce(
        () => streamGemini(systemPrompt, messages),
        "Gemini stream"
      );
      return new NextResponse(stream, {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        },
      });
    } catch {
      // console.error("[chat] Gemini failed:", …);
      if (!process.env.OPENAI_API_KEY) {
        console.warn("[chat] OpenAI key missing, using local fallback after Gemini failure");
        const stream = fallbackSseStream(messages);
        return new NextResponse(stream, {
          headers: {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            Connection: "keep-alive",
          },
        });
      }
      try {
        const stream = await retryOnce(
          () => streamOpenAI(systemPrompt, messages),
          "OpenAI stream"
        );
        return new NextResponse(stream, {
          headers: {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            Connection: "keep-alive",
          },
        });
      } catch (openaiError) {
        console.error("[chat] Both providers unavailable, serving local fallback", {
          error: String(openaiError),
        });
        const stream = fallbackSseStream(messages);
        return new NextResponse(stream, {
          headers: {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            Connection: "keep-alive",
          },
        });
      }
    }
  } catch {
    return NextResponse.json(
      { error: "Invalid request" },
      { status: 400 }
    );
  }
}
