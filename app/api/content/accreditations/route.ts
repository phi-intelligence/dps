import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const accreditations = await prisma.accreditation.findMany({
      orderBy: { sortOrder: "asc" },
    });
    return NextResponse.json(
      accreditations.map((a) => ({
        title: a.title,
        items: JSON.parse(a.items) as string[],
      }))
    );
  } catch (e) {
    console.error(e);
    return NextResponse.json(
      { error: "Failed to fetch accreditations" },
      { status: 500 }
    );
  }
}
