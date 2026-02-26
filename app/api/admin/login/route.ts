import { NextRequest, NextResponse } from "next/server";
import { getAdminCredentials, getAdminCookieName } from "@/lib/admin-auth";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { username, password } = body;
    const { username: adminUser, password: adminPass } = getAdminCredentials();
    if (username === adminUser && password === adminPass) {
      const res = NextResponse.json({ ok: true });
      res.cookies.set(getAdminCookieName(), "1", {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        maxAge: 60 * 60 * 24 * 7, // 7 days
        path: "/",
      });
      return res;
    }
    return NextResponse.json({ error: "Invalid credentials" }, { status: 401 });
  } catch {
    return NextResponse.json({ error: "Bad request" }, { status: 400 });
  }
}
