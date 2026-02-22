import { NextRequest, NextResponse } from "next/server";
import { readFileSync } from "fs";
import { join } from "path";
import { GoogleGenerativeAI } from "@google/generative-ai";
import OpenAI from "openai";
import { COMPANY, SERVICE_AREAS, OPENING_HOURS } from "@/lib/constants";
import { SERVICE_MAP } from "@/lib/chat-config";
import type { ChatRequest } from "@/lib/types/chat";

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

function buildSystemPrompt(): string {
  const servicesList = Object.values(SERVICE_MAP).flatMap((cat) =>
    cat.services.map((s) => `- ${s.label}: ${s.href}`)
  );

  return `You are the DPS Heating Services virtual assistant.

COMPANY: ${COMPANY.name}, ${COMPANY.phone}, ${COMPANY.email}, Gas Safe: ${COMPANY.gasSafeNumber}
AREAS: ${SERVICE_AREAS.join(", ")}
SERVICES:
${servicesList.join("\n")}
HOURS: Mon-Fri ${OPENING_HOURS.weekday}, Sat ${OPENING_HOURS.saturday}, Sun ${OPENING_HOURS.sunday}

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
  const model = genAI.getGenerativeModel({
    model: "gemini-2.5-flash",
    systemInstruction: systemPrompt,
  });

  const allButLast = messages.slice(0, -1);
  const lastMessage = messages[messages.length - 1];
  if (!lastMessage || lastMessage.role !== "user") throw new Error("No user message");

  const history = messagesToGeminiHistory(allButLast);
  const chat = model.startChat({ history: history as never[] });

  const result = await chat.sendMessageStream(lastMessage.content);

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

  const stream = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: openAIMessages,
    stream: true,
  });

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

    const systemPrompt = buildSystemPrompt();
    const geminiKey = getGeminiApiKey();
    const prefix = geminiKey ? geminiKey.slice(0, 8) + "..." : "none";
    console.log("[chat] GEMINI_API_KEY:", geminiKey ? `set (${geminiKey.length} chars)` : "MISSING", "prefix:", prefix);

    try {
      const stream = await streamGemini(systemPrompt, messages);
      return new NextResponse(stream, {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        },
      });
    } catch (geminiErr) {
      console.error("[chat] Gemini failed:", (geminiErr as Error).message);
      try {
        const stream = await streamOpenAI(systemPrompt, messages);
        return new NextResponse(stream, {
          headers: {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            Connection: "keep-alive",
          },
        });
      } catch (openaiErr) {
        console.error("[chat] OpenAI failed:", (openaiErr as Error).message);
        return NextResponse.json(
          {
            error: "Chat is temporarily unavailable. Please try again or call us.",
          },
          { status: 503 }
        );
      }
    }
  } catch (e) {
    return NextResponse.json(
      { error: "Invalid request" },
      { status: 400 }
    );
  }
}
