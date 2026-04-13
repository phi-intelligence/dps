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

export async function GET() {
  const authError = await checkAuth();
  if (authError) return authError;
  try {
    const projects = await prisma.portfolioProject.findMany({
      orderBy: { sortOrder: "asc" },
    });
    return NextResponse.json(
      projects.map((p) => ({
        id: p.id,
        title: p.title,
        category: String(p.category).toLowerCase(),
        location: p.location,
        description: p.description,
        images:
          (() => {
            try {
              const parsed = JSON.parse(p.images);
              if (Array.isArray(parsed)) return parsed.filter((x) => typeof x === "string");
            } catch {
              // ignore parse errors
            }
            return p.image ? [p.image] : [];
          })(),
        stats:
          (() => {
            try {
              const parsed = JSON.parse(p.stats);
              if (Array.isArray(parsed)) {
                return parsed.filter(
                  (s) =>
                    s &&
                    typeof s === "object" &&
                    typeof (s as { label?: unknown }).label === "string" &&
                    typeof (s as { value?: unknown }).value === "string"
                );
              }
            } catch {
              // ignore parse errors
            }
            return [];
          })(),
        sortOrder: p.sortOrder,
        published: p.published,
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

export async function POST(request: NextRequest) {
  const authError = await checkAuth();
  if (authError) return authError;
  try {
    const body = await request.json();
    const {
      title,
      category,
      location,
      description,
      images,
      stats,
      published,
    } = body;

    if (!title || !category || !location || !description) {
      return NextResponse.json(
        {
          error: "Missing required fields: title, category, location, description",
        },
        { status: 400 }
      );
    }

    const normalizedCategory = String(category).toLowerCase();
    if (!VALID_CATEGORIES.has(normalizedCategory)) {
      return NextResponse.json(
        { error: "Category must be gas, mechanical, electrical or plumbing" },
        { status: 400 }
      );
    }

    const imageArr = Array.isArray(images)
      ? images.filter((img: unknown) => typeof img === "string" && img.trim().length > 0)
      : [];
    if (imageArr.length === 0) {
      return NextResponse.json({ error: "At least one image is required" }, { status: 400 });
    }

    const statsArr = Array.isArray(stats)
      ? stats
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
          .filter((s) => s.label || s.value)
      : [];
    if (statsArr.length > 4) {
      return NextResponse.json({ error: "Maximum of 4 stats allowed" }, { status: 400 });
    }

    const maxOrder = await prisma.portfolioProject
      .aggregate({ _max: { sortOrder: true } })
      .then((r) => r._max.sortOrder ?? -1);
    const project = await prisma.portfolioProject.create({
      data: {
        title: String(title),
        category: normalizedCategory,
        location: String(location),
        description: String(description),
        image: imageArr[0],
        images: JSON.stringify(imageArr),
        stats: JSON.stringify(statsArr),
        workStatus: "completed",
        sortOrder: maxOrder + 1,
        published: published != null ? Boolean(published) : true,
      },
    });
    return NextResponse.json({
      id: project.id,
      title: project.title,
      category: project.category,
      location: project.location,
      description: project.description,
      images: JSON.parse(project.images) as string[],
      stats: JSON.parse(project.stats) as { label: string; value: string }[],
      sortOrder: project.sortOrder,
      published: project.published,
    });
  } catch (e) {
    console.error(e);
    return NextResponse.json(
      { error: "Failed to create project" },
      { status: 500 }
    );
  }
}
