import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { isAdminAuthenticated } from "@/lib/admin-auth";

export const dynamic = "force-dynamic";

export async function GET() {
  const ok = await isAdminAuthenticated();
  if (!ok) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  try {
    const config = await prisma.siteConfig.findUnique({
      where: { id: "default" },
    });
    if (!config) {
      return NextResponse.json({ error: "Site config not found" }, { status: 404 });
    }
    return NextResponse.json({
      name: config.name,
      legalName: config.legalName,
      phone: config.phone,
      email: config.email,
      address: config.address,
      gasSafeNumber: config.gasSafeNumber,
      areas: config.areas,
      liabilityInsurance: config.liabilityInsurance,
      indemnityInsurance: config.indemnityInsurance,
      founded: config.founded,
      founder: config.founder,
      industryExperience: config.industryExperience,
      mission: config.mission,
      vision: config.vision,
      openingHoursWeekday: config.openingHoursWeekday,
      openingHoursSaturday: config.openingHoursSaturday,
      openingHoursSunday: config.openingHoursSunday,
      defaultMetaTitle: config.defaultMetaTitle,
      defaultMetaDescription: config.defaultMetaDescription,
    });
  } catch (e) {
    console.error(e);
    return NextResponse.json(
      { error: "Failed to fetch site config" },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest) {
  const ok = await isAdminAuthenticated();
  if (!ok) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  try {
    const body = await request.json();
    const config = await prisma.siteConfig.upsert({
      where: { id: "default" },
      create: {
        id: "default",
        name: body.name ?? "",
        legalName: body.legalName ?? "",
        phone: body.phone ?? "",
        email: body.email ?? "",
        address: body.address ?? "",
        gasSafeNumber: body.gasSafeNumber ?? "",
        areas: body.areas ?? "",
        liabilityInsurance: Boolean(body.liabilityInsurance),
        indemnityInsurance: Boolean(body.indemnityInsurance),
        founded: body.founded ?? "",
        founder: body.founder ?? "",
        industryExperience: body.industryExperience ?? "",
        mission: body.mission ?? "",
        vision: body.vision ?? "",
        openingHoursWeekday: body.openingHoursWeekday ?? "",
        openingHoursSaturday: body.openingHoursSaturday ?? "",
        openingHoursSunday: body.openingHoursSunday ?? "",
        defaultMetaTitle: body.defaultMetaTitle ?? null,
        defaultMetaDescription: body.defaultMetaDescription ?? null,
      },
      update: {
        name: body.name,
        legalName: body.legalName,
        phone: body.phone,
        email: body.email,
        address: body.address,
        gasSafeNumber: body.gasSafeNumber,
        areas: body.areas,
        liabilityInsurance: body.liabilityInsurance != null ? Boolean(body.liabilityInsurance) : undefined,
        indemnityInsurance: body.indemnityInsurance != null ? Boolean(body.indemnityInsurance) : undefined,
        founded: body.founded,
        founder: body.founder,
        industryExperience: body.industryExperience,
        mission: body.mission,
        vision: body.vision,
        openingHoursWeekday: body.openingHoursWeekday,
        openingHoursSaturday: body.openingHoursSaturday,
        openingHoursSunday: body.openingHoursSunday,
        defaultMetaTitle: body.defaultMetaTitle ?? undefined,
        defaultMetaDescription: body.defaultMetaDescription ?? undefined,
      },
    });
    return NextResponse.json({ ok: true, updatedAt: config.updatedAt });
  } catch (e) {
    console.error(e);
    return NextResponse.json(
      { error: "Failed to update site config" },
      { status: 500 }
    );
  }
}
