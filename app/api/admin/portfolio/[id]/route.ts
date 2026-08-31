import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { isAdminAuthenticated } from "@/lib/admin-auth";

export const dynamic = "force-dynamic";
const VALID_CATEGORIES = new Set(["gas", "mechanical", "electrical", "plumbing"]);

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
    if (body.category != null) {
      const normalizedCategory = String(body.category).toLowerCase();
      if (!VALID_CATEGORIES.has(normalizedCategory)) {
        return NextResponse.json(
          { error: "Category must be gas, mechanical, electrical or plumbing" },
          { status: 400 }
        );
      }
      data.category = normalizedCategory;
    }
    if (body.location != null) data.location = String(body.location);
    if (body.description != null) data.description = String(body.description);
    if (body.images != null) {
      const imageArr = Array.isArray(body.images)
        ? body.images.filter((img: unknown) => typeof img === "string" && img.trim().length > 0)
        : [];
      if (imageArr.length === 0) {
        return NextResponse.json({ error: "At least one image is required" }, { status: 400 });
      }
      data.images = JSON.stringify(imageArr);
      data.image = imageArr[0];
    }
    if (body.stats != null) {
      const statsArr = Array.isArray(body.stats)
        ? body.stats
            .filter(
              (s: unknown) =>
                s &&
                typeof s === "object" &&
                typeof (s as { label?: unknown }).label === "string" &&
                typeof (s as { value?: unknown }).value === "string"
            )
            .map((s: { label: string; value: string }) => ({
              label: s.label.trim(),
              value: s.value.trim(),
            }))
            .filter((s: { label: string; value: string }) => s.label || s.value)
        : [];
      if (statsArr.length > 4) {
        return NextResponse.json({ error: "Maximum of 4 stats allowed" }, { status: 400 });
      }
      data.stats = JSON.stringify(statsArr);
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
      images:
        (() => {
          try {
            const parsed = JSON.parse(project.images);
            if (Array.isArray(parsed)) return parsed.filter((x) => typeof x === "string");
          } catch {
            // ignore parse errors
          }
          return project.image ? [project.image] : [];
        })(),
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
