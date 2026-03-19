import { cookies } from "next/headers";

const ADMIN_COOKIE = "dps_admin_session";

export async function isAdminAuthenticated(): Promise<boolean> {
  const cookieStore = await cookies();
  const token = cookieStore.get(ADMIN_COOKIE)?.value;
  return token === "1";
}

export function getAdminCookieName() {
  return ADMIN_COOKIE;
}
