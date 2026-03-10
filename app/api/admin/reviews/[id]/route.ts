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

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const authError = await checkAuth();
  if (authError) return authError;
  const { id } = await params;
  try {
    const body = await request.json();
    const data: Record<string, unknown> = {};
    if (body.name != null) data.name = String(body.name);
    if (body.service != null) data.service = String(body.service);
    if (body.rating != null) data.rating = Math.min(5, Math.max(1, Number(body.rating) || 5));
    if (body.quote != null) data.quote = String(body.quote);
    if (body.image !== undefined) data.image = body.image ? String(body.image) : null;
    if (body.published != null) data.published = Boolean(body.published);
    if (body.sortOrder != null) data.sortOrder = Number(body.sortOrder);
    const review = await prisma.review.update({
      where: { id },
      data,
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
      { error: "Failed to update review" },
      { status: 500 }
    );
  }
}

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const authError = await checkAuth();
  if (authError) return authError;
  const { id } = await params;
  try {
    await prisma.review.delete({ where: { id } });
    return NextResponse.json({ ok: true });
  } catch (e) {
    console.error(e);
    return NextResponse.json(
      { error: "Failed to delete review" },
      { status: 500 }
    );
  }
}
