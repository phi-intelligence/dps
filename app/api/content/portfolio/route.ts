import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const projects = await prisma.portfolioProject.findMany({
      where: { published: true },
      orderBy: { sortOrder: "asc" },
    });
    return NextResponse.json(
      projects.map((p) => ({
        title: p.title,
        category: p.category,
        location: p.location,
        description: p.description,
        image: p.image,
        stats: JSON.parse(p.stats) as { label: string; value: string }[],
      }))
    );
  } catch (e) {
    console.error(e);
    return NextResponse.json(
      { error: "Failed to fetch portfolio" },
      { status: 500 }
    );
  }
}
