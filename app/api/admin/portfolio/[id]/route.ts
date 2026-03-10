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
    if (body.title != null) data.title = String(body.title);
    if (body.category != null) data.category = String(body.category);
    if (body.location != null) data.location = String(body.location);
    if (body.description != null) data.description = String(body.description);
    if (body.image != null) data.image = String(body.image);
    if (body.stats != null) {
      const statsArr = Array.isArray(body.stats)
        ? body.stats.filter((s: unknown) => s && typeof s === "object" && "label" in s && "value" in s)
        : [];
      data.stats = JSON.stringify(statsArr.length > 0 ? statsArr : [{ label: "—", value: "—" }]);
    }
    if (body.published != null) data.published = Boolean(body.published);
    if (body.sortOrder != null) data.sortOrder = Number(body.sortOrder);
    const project = await prisma.portfolioProject.update({
      where: { id },
      data,
    });
    return NextResponse.json({
      id: project.id,
      title: project.title,
      category: project.category,
      location: project.location,
      description: project.description,
      image: project.image,
      stats: JSON.parse(project.stats) as { label: string; value: string }[],
      sortOrder: project.sortOrder,
      published: project.published,
    });
  } catch (e) {
    console.error(e);
    return NextResponse.json(
      { error: "Failed to update project" },
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
    await prisma.portfolioProject.delete({ where: { id } });
    return NextResponse.json({ ok: true });
  } catch (e) {
    console.error(e);
    return NextResponse.json(
      { error: "Failed to delete project" },
      { status: 500 }
    );
  }
}
