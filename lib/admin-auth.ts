import { cookies } from "next/headers";
import { createHash } from "crypto";
import { prisma } from "@/lib/db";

const ADMIN_COOKIE = "dps_admin_session";

export async function isAdminAuthenticated(): Promise<boolean> {
  const cookieStore = await cookies();
  const token = cookieStore.get(ADMIN_COOKIE)?.value;
  if (!token) return false;

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
