import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const config = await prisma.siteConfig.findUnique({
      where: { id: "default" },
    });
    if (!config) {
      return NextResponse.json(
        { error: "Site config not found" },
        { status: 404 }
      );
    }
    return NextResponse.json({
      company: {
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
      },
      openingHours: {
        weekday: config.openingHoursWeekday,
        saturday: config.openingHoursSaturday,
        sunday: config.openingHoursSunday,
      },
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
