/**
 * One-off script to verify chat API keys.
 * Run: node scripts/test-chat-keys.js
 * Loads .env.local and tests Gemini (then OpenAI fallback) without logging keys.
 */

const fs = require("fs");
const path = require("path");

// Load .env.local
const envPath = path.join(__dirname, "..", ".env.local");
if (!fs.existsSync(envPath)) {
  console.error(".env.local not found at", envPath);
  process.exit(1);
}
fs.readFileSync(envPath, "utf8")
  .split("\n")
  .forEach((line) => {
    const m = line.match(/^([^#=]+)=(.*)$/);
    if (m) {
      let val = m[2].trim();
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'")))
        val = val.slice(1, -1);
      process.env[m[1].trim()] = val;
    }
  });

const geminiKey = process.env.GEMINI_API_KEY;
const openaiKey = process.env.OPENAI_API_KEY;

console.log("GEMINI_API_KEY:", geminiKey ? `set (${geminiKey.length} chars)` : "MISSING");
console.log("OPENAI_API_KEY:", openaiKey ? `set (${openaiKey.length} chars)` : "MISSING");

async function testGemini() {
  if (!geminiKey) return { ok: false, error: "GEMINI_API_KEY not set" };
  try {
    const { GoogleGenerativeAI } = require("@google/generative-ai");
    const genAI = new GoogleGenerativeAI(geminiKey);
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });
    const result = await model.generateContent("Reply with exactly: OK");
    const text = result.response?.text?.() ?? "";
    if (text.trim()) return { ok: true };
    return { ok: false, error: "Empty response" };
  } catch (e) {
    return { ok: false, error: e.message || String(e) };
  }
}

async function testOpenAI() {
  if (!openaiKey) return { ok: false, error: "OPENAI_API_KEY not set" };
  try {
    const OpenAI = require("openai").default;
    const openai = new OpenAI({ apiKey: openaiKey });
    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: "Reply with exactly: OK" }],
      max_tokens: 10,
    });
    const text = completion.choices?.[0]?.message?.content ?? "";
    if (text.trim()) return { ok: true };
    return { ok: false, error: "Empty response" };
  } catch (e) {
    return { ok: false, error: e.message || String(e) };
  }
}

(async () => {
  console.log("\nTesting Gemini...");
  const g = await testGemini();
  console.log(g.ok ? "  Gemini: OK" : "  Gemini: FAIL -", g.error);

  console.log("\nTesting OpenAI (fallback)...");
  const o = await testOpenAI();
  console.log(o.ok ? "  OpenAI: OK" : "  OpenAI: FAIL -", o.error);

  if (g.ok || o.ok) {
    console.log("\nAt least one provider works. Chat should work.");
  } else {
    console.log("\nBoth providers failed. Check keys and quotas.");
  }
})();
