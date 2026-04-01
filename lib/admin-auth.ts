import { cookies } from "next/headers";
import { createHash, createHmac, timingSafeEqual } from "crypto";
import { prisma } from "@/lib/db";

const ADMIN_COOKIE = "dps_admin_session";
const STATELESS_PREFIX = "st.";
const SESSION_TTL_SECONDS = 60 * 60 * 24 * 7;

function getSessionSecret(): string {
  return (
    process.env.ADMIN_SESSION_SECRET ??
    process.env.ADMIN_REGISTER_SECRET ??
    process.env.JWT_SECRET ??
    "dev-only-insecure-admin-session-secret"
  );
}

function toBase64Url(input: string): string {
  return Buffer.from(input, "utf8").toString("base64url");
}

function fromBase64Url(input: string): string {
  return Buffer.from(input, "base64url").toString("utf8");
}

function signPayload(payloadB64: string): string {
  return createHmac("sha256", getSessionSecret()).update(payloadB64).digest("base64url");
}

export function createStatelessAdminToken(adminUserId: string): string {
  const payload = JSON.stringify({
    sub: adminUserId,
    exp: Date.now() + SESSION_TTL_SECONDS * 1000,
  });
  const payloadB64 = toBase64Url(payload);
  const signature = signPayload(payloadB64);
  return `${STATELESS_PREFIX}${payloadB64}.${signature}`;
}

function verifyStatelessAdminToken(token: string): { sub: string; exp: number } | null {
  if (!token.startsWith(STATELESS_PREFIX)) return null;
  const unsigned = token.slice(STATELESS_PREFIX.length);
  const [payloadB64, signature] = unsigned.split(".");
  if (!payloadB64 || !signature) return null;

  const expected = signPayload(payloadB64);
  const expectedBuffer = Buffer.from(expected);
  const signatureBuffer = Buffer.from(signature);
  if (expectedBuffer.length !== signatureBuffer.length) return null;
  if (!timingSafeEqual(expectedBuffer, signatureBuffer)) return null;

  try {
    const payloadRaw = fromBase64Url(payloadB64);
    const payload = JSON.parse(payloadRaw) as { sub?: string; exp?: number };
    if (typeof payload.sub !== "string" || typeof payload.exp !== "number") return null;
    return { sub: payload.sub, exp: payload.exp };
  } catch {
    return null;
  }
}

export async function isAdminAuthenticated(): Promise<boolean> {
  const cookieStore = await cookies();
  const token = cookieStore.get(ADMIN_COOKIE)?.value;
  if (!token) return false;

  const stateless = verifyStatelessAdminToken(token);
  if (stateless) {
    if (stateless.exp <= Date.now()) return false;
    const admin = await prisma.adminUser.findUnique({
      where: { id: stateless.sub },
      select: { id: true },
    });
    return Boolean(admin);
  }

  const tokenHash = createHash("sha256").update(token).digest("hex");
  const session = await prisma.adminSession.findUnique({
    where: { tokenHash },
    select: { expiresAt: true },
  });
  if (!session) return false;
  return session.expiresAt.getTime() > Date.now();
}

export function getAdminCookieName() {
  return ADMIN_COOKIE;
}

export function getAdminSessionTtlSeconds() {
  return SESSION_TTL_SECONDS;
}
