import { NextRequest, NextResponse } from "next/server";
import { listServices, getServiceBySlug } from "@/lib/content";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  try {
    const slug = request.nextUrl.searchParams.get("slug");
    if (slug) {
      const service = await getServiceBySlug(slug);
      if (!service) {
        return NextResponse.json({ error: "Service not found" }, { status: 404 });
      }
      return NextResponse.json(service);
    }
    const services = await listServices();
    return NextResponse.json(services);
  } catch (e) {
    console.error(e);
    return NextResponse.json(
      { error: "Failed to fetch services" },
      { status: 500 }
    );
  }
}
