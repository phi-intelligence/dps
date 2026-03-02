import "dotenv/config";
import { prisma } from "../lib/db";
import {
  OPENING_HOURS,
  COMPANY,
  NAV_LINKS,
  SERVICE_AREAS,
  REVIEWS,
  PORTFOLIO_PROJECTS,
  ACCREDITATIONS,
} from "../lib/constants";

async function main() {
  await prisma.siteConfig.upsert({
    where: { id: "default" },
    create: {
      id: "default",
      name: COMPANY.name,
      legalName: COMPANY.legalName,
      phone: COMPANY.phone,
      email: COMPANY.email,
      address: COMPANY.address,
      gasSafeNumber: COMPANY.gasSafeNumber,
      areas: COMPANY.areas,
      liabilityInsurance: COMPANY.liabilityInsurance,
      indemnityInsurance: COMPANY.indemnityInsurance,
      founded: COMPANY.founded,
      founder: COMPANY.founder,
      industryExperience: COMPANY.industryExperience,
      mission: COMPANY.mission,
      vision: COMPANY.vision,
      openingHoursWeekday: OPENING_HOURS.weekday,
      openingHoursSaturday: OPENING_HOURS.saturday,
      openingHoursSunday: OPENING_HOURS.sunday,
      defaultMetaTitle: null,
      defaultMetaDescription: null,
    },
    update: {
      name: COMPANY.name,
      legalName: COMPANY.legalName,
      phone: COMPANY.phone,
      email: COMPANY.email,
      address: COMPANY.address,
      gasSafeNumber: COMPANY.gasSafeNumber,
      areas: COMPANY.areas,
      liabilityInsurance: COMPANY.liabilityInsurance,
      indemnityInsurance: COMPANY.indemnityInsurance,
      founded: COMPANY.founded,
      founder: COMPANY.founder,
      industryExperience: COMPANY.industryExperience,
      mission: COMPANY.mission,
      vision: COMPANY.vision,
      openingHoursWeekday: OPENING_HOURS.weekday,
      openingHoursSaturday: OPENING_HOURS.saturday,
      openingHoursSunday: OPENING_HOURS.sunday,
    },
  });

  await prisma.navLink.deleteMany({});
  let sortOrder = 0;
  for (const link of NAV_LINKS) {
    if ("children" in link && link.children) {
      const parent = await prisma.navLink.create({
        data: {
          label: link.label,
          href: link.href,
          sortOrder: sortOrder++,
        },
      });
      for (const child of link.children) {
        await prisma.navLink.create({
          data: {
            label: child.label,
            href: child.href,
            sortOrder: 0,
            parentId: parent.id,
          },
        });
      }
    } else {
      await prisma.navLink.create({
        data: {
          label: link.label,
          href: link.href,
          sortOrder: sortOrder++,
        },
      });
    }
  }

  await prisma.serviceArea.deleteMany({});
  for (let i = 0; i < SERVICE_AREAS.length; i++) {
    await prisma.serviceArea.create({
      data: { name: SERVICE_AREAS[i], sortOrder: i },
    });
  }

  await prisma.review.deleteMany({});
  await Promise.all(
    REVIEWS.map((r, i) =>
      prisma.review.create({
        data: {
          name: r.name,
          service: r.service,
          rating: r.rating,
          quote: r.quote,
          sortOrder: i,
        },
      })
    )
  );

  await prisma.portfolioProject.deleteMany({});
  await Promise.all(
    PORTFOLIO_PROJECTS.map((p, i) =>
      prisma.portfolioProject.create({
        data: {
          title: p.title,
          category: p.category,
          location: p.location,
          description: p.description,
          image: p.image,
          stats: JSON.stringify(p.stats),
          sortOrder: i,
        },
      })
    )
  );

  await prisma.accreditation.deleteMany({});
  await Promise.all(
    ACCREDITATIONS.map((a, i) =>
      prisma.accreditation.create({
        data: {
          title: a.title,
          items: JSON.stringify(a.items),
          sortOrder: i,
        },
      })
    )
  );

  // Seed one service detail (boiler-installation) so CMS-driven service pages work
  await prisma.serviceDetail.deleteMany({});
  await prisma.service.deleteMany({});
  const boilerService = await prisma.service.create({
    data: {
      slug: "heating/boiler-installation",
      title: "Boiler Installation",
      shortDescription: "Professional new boiler installation by Gas Safe registered engineers.",
      sector: "both",
      discipline: "heating",
      parentSlug: "heating",
      sortOrder: 0,
    },
  });
  await prisma.serviceDetail.create({
    data: {
      serviceId: boilerService.id,
      subtitle: "Professional new boiler installation by Gas Safe registered engineers. Supply, fit, and commission.",
      introduction: `A new boiler is a significant investment, and it pays to have it installed correctly. DPS Heating Services LTD provides full boiler installation across ${COMPANY.areas}, including a free survey, system design, supply and installation of the new boiler, commissioning, and warranty registration. We are Gas Safe registered and work with all leading brands.`,
      included: JSON.stringify([
        "Free survey and quote",
        "Boiler and system design advice",
        "Full installation to current regulations",
        "Commissioning and testing",
        "Manufacturer warranty registration",
        "Removal and disposal of old boiler",
        "Building regulations certificate",
      ]),
      issues: JSON.stringify([
        { icon: "flame", title: "Boiler Over 10 Years Old", description: "Older boilers are less efficient and more likely to develop faults. A new A-rated boiler can significantly reduce heating bills." },
        { icon: "checkCircle", title: "Frequent Breakdowns", description: "If your boiler is breaking down regularly, replacement is often more cost-effective than continued repairs." },
        { icon: "gauge", title: "Rising Energy Bills", description: "An inefficient boiler uses more gas to produce the same amount of heat, costing you more each month." },
        { icon: "wrench", title: "Moving to a New Property", description: "A new property may benefit from a new boiler installation to match the size and requirements of the home." },
      ]),
      steps: JSON.stringify([
        { icon: "phone", number: "01", title: "Free Survey", description: "We visit your property to assess your heating needs and recommend the right boiler." },
        { icon: "clipboardList", number: "02", title: "Written Quote", description: "You receive a clear, fixed quote with no hidden charges before any work begins." },
        { icon: "wrench", number: "03", title: "Installation Day", description: "Our engineers install the new boiler neatly and efficiently, protecting your home throughout." },
        { icon: "shield", number: "04", title: "Commission & Register", description: "The boiler is commissioned, tested, and registered for warranty. You receive all documentation." },
      ]),
      trustPoints: JSON.stringify([
        { icon: "shield", title: "Fully Compliant", description: "All installations meet current Gas Safe and building regulation requirements." },
        { icon: "star", title: "Leading Brands", description: "We install Worcester Bosch, Vaillant, Baxi, Ideal, and Viessmann boilers." },
        { icon: "clock", title: "Typically One Day", description: "Most boiler replacements are completed within a single working day." },
      ]),
      faqs: JSON.stringify([
        { question: "How long does a boiler installation take?", answer: "Most boiler replacements are completed in one day. More complex installations, such as system changes, may take longer." },
        { question: "Which boilers do you install?", answer: "We install all major brands including Worcester Bosch, Vaillant, Baxi, Ideal, and Viessmann. We can advise on the best option for your home." },
        { question: "Will my home be left clean and tidy?", answer: "Absolutely. We use protective coverings throughout and leave your home as we found it." },
        { question: "What warranty comes with a new boiler?", answer: "Most new boilers come with a 5–12 year manufacturer warranty when installed by a registered engineer. We handle all registration on your behalf." },
      ]),
      breadcrumbs: JSON.stringify([
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Heating", href: "/services/heating" },
        { label: "Boiler Installation" },
      ]),
      backgroundImage: "/images/140d49a2-daf4-4c0f-b0c4-881f971b97c0.jpg",
      sideImage: "/images/140d49a2-daf4-4c0f-b0c4-881f971b97c0.jpg",
      sideImageAlt: "New boiler neatly installed in kitchen cupboard with copper pipework",
      showGasSafeNote: true,
      accentColor: "red",
      serviceValue: "boiler-installation",
      metaTitle: "Boiler Installation",
      metaDescription: `New boiler installation in ${COMPANY.areas}. Gas Safe registered engineers, all major brands, full commissioning and warranty registration.`,
    },
  });

  console.log("Seed completed.");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
