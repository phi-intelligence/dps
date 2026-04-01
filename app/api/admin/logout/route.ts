import { NextResponse } from "next/server";
import { getAdminCookieName } from "@/lib/admin-auth";
import { cookies } from "next/headers";
import { createHash } from "crypto";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function POST() {
  const cookieStore = await cookies();
  const token = cookieStore.get(getAdminCookieName())?.value;
  if (token) {
    const tokenHash = createHash("sha256").update(token).digest("hex");
    await prisma.adminSession.deleteMany({ where: { tokenHash } });
  }
  const res = NextResponse.json({ ok: true });
  res.cookies.set(getAdminCookieName(), "", { maxAge: 0, path: "/", secure: false });
  return res;
}
