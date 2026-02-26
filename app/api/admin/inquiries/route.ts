import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { isAdminAuthenticated } from "@/lib/admin-auth";

export const dynamic = "force-dynamic";

export async function GET() {
  const ok = await isAdminAuthenticated();
  if (!ok) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  try {
    const inquiries = await prisma.inquiry.findMany({
      orderBy: { timestamp: "desc" },
    });
    return NextResponse.json(
      inquiries.map((i) => ({
        id: i.id,
        name: i.name,
        phone: i.phone,
        email: i.email,
        service: i.service,
        message: i.message,
        status: i.status,
        timestamp: i.timestamp.getTime(),
      }))
    );
  } catch (e) {
    console.error(e);
    return NextResponse.json(
      { error: "Failed to fetch inquiries" },
      { status: 500 }
    );
  }
}
