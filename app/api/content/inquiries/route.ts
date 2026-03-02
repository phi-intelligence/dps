import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";

/** Public: create inquiry (quote form submission) */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { name, phone, email, service, message } = body;
    if (!name || !email || !message) {
      return NextResponse.json(
        { error: "Missing required fields: name, email, message" },
        { status: 400 }
      );
    }
    const inquiry = await prisma.inquiry.create({
      data: {
        name: String(name),
        phone: String(phone ?? ""),
        email: String(email),
        service: String(service ?? ""),
        message: String(message),
        status: "pending",
      },
    });
    return NextResponse.json({
      id: inquiry.id,
      status: inquiry.status,
      timestamp: inquiry.timestamp.toISOString(),
    });
  } catch (e) {
    console.error(e);
    return NextResponse.json(
      { error: "Failed to create inquiry" },
      { status: 500 }
    );
  }
}
