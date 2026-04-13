import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import {
  createStatelessAdminToken,
  getAdminCookieName,
  getAdminSessionTtlSeconds,
} from "@/lib/admin-auth";
import { verifyPassword } from "@/lib/password";
import { randomBytes, createHash } from "crypto";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body" }, { status: 400 });
  }

  try {
    const username =
      typeof (body as { username?: unknown }).username === "string"
        ? (body as { username: string }).username.trim()
        : "";
    const password =
      typeof (body as { password?: unknown }).password === "string"
        ? (body as { password: string }).password
        : "";

    if (!username || !password) {
      return NextResponse.json({ error: "Invalid credentials" }, { status: 401 });
    }

    const admin = await prisma.adminUser.findUnique({
      where: { username },
    });

    if (!admin) {
      return NextResponse.json({ error: "Invalid credentials" }, { status: 401 });
    }

    const valid = await verifyPassword(password, admin.passwordHash);
    if (!valid) {
      return NextResponse.json({ error: "Invalid credentials" }, { status: 401 });
    }

    const expiresAt = new Date(Date.now() + getAdminSessionTtlSeconds() * 1000);
    let cookieValue = "";
    try {
      const token = randomBytes(32).toString("base64url");
      const tokenHash = createHash("sha256").update(token).digest("hex");
      await prisma.adminSession.create({
        data: {
          tokenHash,
          expiresAt,
          adminUserId: admin.id,
        },
      });
      cookieValue = token;
    } catch {
      // Fallback for deployments where DB session writes fail.
      cookieValue = createStatelessAdminToken(admin.id);
    }

    const res = NextResponse.json({ ok: true });
    res.cookies.set(getAdminCookieName(), cookieValue, {
      httpOnly: true,
      secure: true,
      sameSite: "lax",
      maxAge: getAdminSessionTtlSeconds(),
      path: "/",
    });
    return res;
  } catch (error) {
    console.error("Admin login failed", error);
    return NextResponse.json({ error: "Login failed" }, { status: 500 });
  }
}
