import { cookies } from "next/headers";

const ADMIN_COOKIE = "dps_admin_session";
const ADMIN_USERNAME = process.env.ADMIN_USERNAME ?? "admin";
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD ?? "admin";

export function getAdminCredentials() {
  return { username: ADMIN_USERNAME, password: ADMIN_PASSWORD };
}

export async function isAdminAuthenticated(): Promise<boolean> {
  const cookieStore = await cookies();
  const token = cookieStore.get(ADMIN_COOKIE)?.value;
  return token === "1";
}

export function getAdminCookieName() {
  return ADMIN_COOKIE;
}
