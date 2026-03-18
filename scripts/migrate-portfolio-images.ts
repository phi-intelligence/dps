import { prisma } from "@/lib/db";

type ProjectUpdate = { title: string; image: string };

const UPDATES: ProjectUpdate[] = [
  { title: "Commercial Boiler Plant Room", image: "/imagesv2/portfolio/boiler_plant_room.jpeg" },
  { title: "Immersion Heater & Leak Repair", image: "/imagesv2/portfolio/immersion_leak.jpg" },
  { title: "Dual Immersion Heater Element Replacement", image: "/imagesv2/portfolio/immersion_heater.webp" },
  { title: "Victorian Terrace Central Heating", image: "/imagesv2/portfolio/central_heating.jpg" },
  { title: "Bathroom Leaks & Ensuite Renovation Prep", image: "/imagesv2/portfolio/bathroom_leak.jpg" },
  { title: "Leak Investigation — Bathroom & Immersion", image: "/imagesv2/portfolio/leak_investigation.jpg" },
  { title: "Radiator Repair & Smoke Alarms", image: "/imagesv2/portfolio/radiator%20repair.jpg" },
  { title: "Emergency Boiler Replacement", image: "/imagesv2/domestic_gas/boiler-install.jpg" },
  { title: "Banging Pipes & Emergency Shut-Off", image: "/imagesv2/portfolio/banging_pipe.jpg" },
  { title: "Three Radiators Fitted", image: "/imagesv2/portfolio/radiator_fitted.jpg" },
  { title: "Radiator Reattachment & Boiler Advice", image: "/imagesv2/portfolio/radiator_attach.jpg" },
  { title: "Leaking Boiler Diagnosis", image: "/imagesv2/portfolio/boiler_repair.jpg" },
  { title: "Boiler Repair", image: "/imagesv2/portfolio/boiler_repair.jpg" },
  { title: "Suspected Leaking Pipe in Bathroom", image: "/imagesv2/domestic_mechanical/domestic_leak.jpg" },
  { title: "Concealed Shower Valve Replacement", image: "/imagesv2/portfolio/concealed_shower_valve.jpg" },
  { title: "Leaking Pipe Beneath Boiler", image: "/imagesv2/portfolio/boiler_repair.jpg" },
  { title: "Leaking Radiator — Sunday Callout", image: "/imagesv2/domestic_mechanical/radiator.jpg" },
  { title: "Faulty Heating System", image: "/imagesv2/portfolio/central_heating.jpg" },
  { title: "Emergency Rising Main — Basement Flood", image: "/imagesv2/portfolio/immersion_leak.jpg" },
];

async function main() {
  const existing = await prisma.portfolioProject.findMany({
    select: { id: true, title: true, image: true },
  });

  const byTitle = new Map(existing.map((p) => [p.title, p] as const));

  const toApply = UPDATES.filter((u) => byTitle.has(u.title));
  const missing = UPDATES.filter((u) => !byTitle.has(u.title)).map((u) => u.title);

  if (missing.length > 0) {
    console.log("[migrate-portfolio-images] Titles not found in DB (skipped):");
    for (const t of missing) console.log(`- ${t}`);
  }

  let updated = 0;
  for (const u of toApply) {
    const row = byTitle.get(u.title)!;
    if (row.image === u.image) continue;
    await prisma.portfolioProject.update({
      where: { id: row.id },
      data: { image: u.image },
    });
    updated++;
  }

  console.log(`[migrate-portfolio-images] Updated ${updated} portfolio image(s).`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });

