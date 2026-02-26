import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const areas = await prisma.serviceArea.findMany({
      orderBy: { sortOrder: "asc" },
    });
    return NextResponse.json(areas.map((a) => a.name));
  } catch (e) {
    console.error(e);
    return NextResponse.json(
      { error: "Failed to fetch service areas" },
      { status: 500 }
    );
  }
}
