import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const links = await prisma.navLink.findMany({
      where: { parentId: null },
      orderBy: { sortOrder: "asc" },
      include: {
        children: {
          orderBy: { sortOrder: "asc" },
        },
      },
    });
    const nav = links.map((link) => {
      if (link.children.length > 0) {
        return {
          label: link.label,
          href: link.href,
          children: link.children.map((c) => ({
            label: c.label,
            href: c.href,
          })),
        };
      }
      return { label: link.label, href: link.href };
    });
    return NextResponse.json(nav);
  } catch (e) {
    console.error(e);
    return NextResponse.json(
      { error: "Failed to fetch navigation" },
      { status: 500 }
    );
  }
}
