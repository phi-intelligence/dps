import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const reviews = await prisma.review.findMany({
      where: { published: true },
      orderBy: { sortOrder: "asc" },
    });
    return NextResponse.json(
      reviews.map((r) => ({
        name: r.name,
        service: r.service,
        rating: r.rating,
        quote: r.quote,
        image: r.image ?? undefined,
      }))
    );
  } catch (e) {
    console.error(e);
    return NextResponse.json(
      { error: "Failed to fetch reviews" },
      { status: 500 }
    );
  }
}
