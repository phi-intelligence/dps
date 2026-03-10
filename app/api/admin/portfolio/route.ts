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
    const projects = await prisma.portfolioProject.findMany({
      orderBy: { sortOrder: "asc" },
    });
    return NextResponse.json(
      projects.map((p) => ({
        id: p.id,
        title: p.title,
        category: p.category,
        location: p.location,
        description: p.description,
        image: p.image,
        stats: JSON.parse(p.stats) as { label: string; value: string }[],
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
    const { title, category, location, description, image, stats, published } = body;
    if (!title || !category || !location || !description || !image) {
      return NextResponse.json(
        { error: "Missing required fields: title, category, location, description, image" },
        { status: 400 }
      );
    }
    const statsArr = Array.isArray(stats)
      ? stats.filter((s: unknown) => s && typeof s === "object" && "label" in s && "value" in s)
      : [];
    const maxOrder = await prisma.portfolioProject
      .aggregate({ _max: { sortOrder: true } })
      .then((r) => r._max.sortOrder ?? -1);
    const project = await prisma.portfolioProject.create({
      data: {
        title: String(title),
        category: String(category),
        location: String(location),
        description: String(description),
        image: String(image),
        stats: JSON.stringify(statsArr.length > 0 ? statsArr : [{ label: "—", value: "—" }]),
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
      image: project.image,
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
