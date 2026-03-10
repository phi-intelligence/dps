import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { isAdminAuthenticated } from "@/lib/admin-auth";

export const dynamic = "force-dynamic";

async function checkAuth() {
  const ok = await isAdminAuthenticated();
  if (!ok) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  return null;
}

export async function GET() {
  const authError = await checkAuth();
  if (authError) return authError;
  try {
    const reviews = await prisma.review.findMany({
      orderBy: { sortOrder: "asc" },
    });
    return NextResponse.json(
      reviews.map((r) => ({
        id: r.id,
        name: r.name,
        service: r.service,
        rating: r.rating,
        quote: r.quote,
        image: r.image ?? undefined,
        sortOrder: r.sortOrder,
        published: r.published,
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

export async function POST(request: NextRequest) {
  const authError = await checkAuth();
  if (authError) return authError;
  try {
    const body = await request.json();
    const { name, service, rating, quote, image, published } = body;
    if (!name || !service || !quote) {
      return NextResponse.json(
        { error: "Missing required fields: name, service, quote" },
        { status: 400 }
      );
    }
    const ratingNum = Math.min(5, Math.max(1, Number(rating) || 5));
    const maxOrder = await prisma.review
      .aggregate({ _max: { sortOrder: true } })
      .then((r) => r._max.sortOrder ?? -1);
    const review = await prisma.review.create({
      data: {
        name: String(name),
        service: String(service),
        rating: ratingNum,
        quote: String(quote),
        image: image ? String(image) : null,
        sortOrder: maxOrder + 1,
        published: published != null ? Boolean(published) : true,
      },
    });
    return NextResponse.json({
      id: review.id,
      name: review.name,
      service: review.service,
      rating: review.rating,
      quote: review.quote,
      image: review.image ?? undefined,
      sortOrder: review.sortOrder,
      published: review.published,
    });
  } catch (e) {
    console.error(e);
    return NextResponse.json(
      { error: "Failed to create review" },
      { status: 500 }
    );
  }
}
