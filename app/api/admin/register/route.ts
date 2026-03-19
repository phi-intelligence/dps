import { NextRequest, NextResponse } from "next/server";
import { Prisma } from "@prisma/client";
import { prisma } from "@/lib/db";
import { hashPassword } from "@/lib/password";

export const dynamic = "force-dynamic";

/**
 * One-time admin registration (no UI). After the first row exists, further calls return 409.
 *
 * POST /api/admin/register
 * Body JSON: { "username": "...", "password": "...", "full_name": "..." }
 *
 * Optional: set ADMIN_REGISTER_SECRET in production and send the same value as:
 *   Header: x-admin-register-secret: <secret>
 *   or Authorization: Bearer <secret>
 */
export async function POST(request: NextRequest) {
  const registerSecret = process.env.ADMIN_REGISTER_SECRET;
  if (registerSecret) {
    const headerSecret =
      request.headers.get("x-admin-register-secret") ??
      request.headers.get("authorization")?.replace(/^Bearer\s+/i, "")?.trim();
    if (headerSecret !== registerSecret) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }
  }

  let raw: unknown;
  try {
    raw = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }
  const body = raw as Record<string, unknown>;

  try {
    const username =
      typeof body.username === "string" ? body.username.trim() : "";
    const password = typeof body.password === "string" ? body.password : "";
    const fullName =
      typeof body.full_name === "string"
        ? body.full_name.trim()
        : typeof body.fullName === "string"
          ? body.fullName.trim()
          : "";

    if (!username || username.length > 100) {
      return NextResponse.json(
        { error: "username is required (max 100 characters)" },
        { status: 400 }
      );
    }
    if (password.length < 8) {
      return NextResponse.json(
        { error: "password must be at least 8 characters" },
        { status: 400 }
      );
    }
    if (!fullName || fullName.length > 200) {
      return NextResponse.json(
        { error: "full_name is required (max 200 characters)" },
        { status: 400 }
      );
    }

    const existing = await prisma.adminUser.findUnique({
      where: { id: "singleton" },
    });
    if (existing) {
      return NextResponse.json(
        { error: "An administrator is already registered" },
        { status: 409 }
      );
    }

    const passwordHash = await hashPassword(password);

    try {
      await prisma.adminUser.create({
        data: {
          username,
          passwordHash,
          fullName,
        },
      });
    } catch (e) {
      if (e instanceof Prisma.PrismaClientKnownRequestError && e.code === "P2002") {
        return NextResponse.json(
          { error: "An administrator is already registered" },
          { status: 409 }
        );
      }
      throw e;
    }

    return NextResponse.json({
      ok: true,
      message: "Admin registered successfully",
      username,
    });
  } catch (e) {
    console.error(e);
    return NextResponse.json(
      { error: "Failed to register administrator" },
      { status: 500 }
    );
  }
}
