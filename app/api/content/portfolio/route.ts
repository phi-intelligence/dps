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
