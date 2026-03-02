import { prisma } from "@/lib/db";

export interface Company {
  name: string;
  legalName: string;
  phone: string;
  email: string;
  address: string;
  gasSafeNumber: string;
  areas: string;
  liabilityInsurance: boolean;
  indemnityInsurance: boolean;
  founded: string;
  founder: string;
  industryExperience: string;
  mission: string;
  vision: string;
}

export interface OpeningHours {
  weekday: string;
  saturday: string;
  sunday: string;
}

export interface NavLinkItem {
  label: string;
  href: string;
  children?: { label: string; href: string }[];
}

export interface ReviewItem {
  name: string;
  service: string;
  rating: number;
  quote: string;
  image?: string;
}

export interface PortfolioProjectItem {
  title: string;
  category: string;
  location: string;
  description: string;
  image: string;
  stats: { label: string; value: string }[];
}

export interface AccreditationItem {
  title: string;
  items: string[];
}

/** Shape for ServiceDetailLayout props (from CMS) */
export interface ServiceDetailData {
  title: string;
  subtitle: string;
  backgroundImage: string;
  sideImage: string;
  sideImageAlt: string;
  introduction: string;
  included: string[];
  issues: { icon: string; title: string; description: string }[];
  steps: { icon: string; number: string; title: string; description: string }[];
  trustPoints: { icon: string; title: string; description: string }[];
  faqs: { question: string; answer: string }[];
  breadcrumbs: { label: string; href?: string }[];
  serviceValue: string;
  showGasSafeNote?: boolean;
  accentColor?: "red" | "blue";
  metaTitle?: string | null;
  metaDescription?: string | null;
}

export interface ServiceListItem {
  slug: string;
  title: string;
  shortDescription: string | null;
  sector: string | null;
  discipline: string | null;
  parentSlug: string | null;
  sortOrder: number;
}

export async function getSiteConfig(): Promise<{
  company: Company;
  openingHours: OpeningHours;
  defaultMetaTitle: string | null;
  defaultMetaDescription: string | null;
} | null> {
  try {
    const config = await prisma.siteConfig.findUnique({
      where: { id: "default" },
    });
    if (!config) return null;
    return {
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
    };
  } catch {
    return null;
  }
}

export async function getNav(): Promise<NavLinkItem[]> {
  try {
    const links = await prisma.navLink.findMany({
      where: { parentId: null },
      orderBy: { sortOrder: "asc" },
      include: {
        children: { orderBy: { sortOrder: "asc" } },
      },
    });
    return links.map((link) => {
      if (link.children.length > 0) {
        return {
          label: link.label,
          href: link.href,
          children: link.children.map((c) => ({ label: c.label, href: c.href })),
        };
      }
      return { label: link.label, href: link.href };
    });
  } catch {
    return [];
  }
}

export async function getReviews(): Promise<ReviewItem[]> {
  try {
    const reviews = await prisma.review.findMany({
      where: { published: true },
      orderBy: { sortOrder: "asc" },
    });
    return reviews.map((r) => ({
      name: r.name,
      service: r.service,
      rating: r.rating,
      quote: r.quote,
      image: r.image ?? undefined,
    }));
  } catch {
    return [];
  }
}

export async function getPortfolio(): Promise<PortfolioProjectItem[]> {
  try {
    const projects = await prisma.portfolioProject.findMany({
      where: { published: true },
      orderBy: { sortOrder: "asc" },
    });
    return projects.map((p) => ({
      title: p.title,
      category: p.category,
      location: p.location,
      description: p.description,
      image: p.image,
      stats: JSON.parse(p.stats) as { label: string; value: string }[],
    }));
  } catch {
    return [];
  }
}

export async function getAccreditations(): Promise<AccreditationItem[]> {
  try {
    const list = await prisma.accreditation.findMany({
      orderBy: { sortOrder: "asc" },
    });
    return list.map((a) => ({
      title: a.title,
      items: JSON.parse(a.items) as string[],
    }));
  } catch {
    return [];
  }
}

export async function getServiceAreas(): Promise<string[]> {
  try {
    const areas = await prisma.serviceArea.findMany({
      orderBy: { sortOrder: "asc" },
    });
    return areas.map((a) => a.name);
  } catch {
    return [];
  }
}

export async function getServiceBySlug(slug: string): Promise<ServiceDetailData | null> {
  try {
    const service = await prisma.service.findUnique({
      where: { slug },
      include: { detail: true },
    });
    if (!service?.detail) return null;
    const d = service.detail;
    return {
      title: service.title,
      subtitle: d.subtitle ?? "",
      backgroundImage: d.backgroundImage ?? "",
      sideImage: d.sideImage ?? "",
      sideImageAlt: d.sideImageAlt ?? "",
      introduction: d.introduction ?? "",
      included: JSON.parse(d.included) as string[],
      issues: JSON.parse(d.issues) as { icon: string; title: string; description: string }[],
      steps: JSON.parse(d.steps) as { icon: string; number: string; title: string; description: string }[],
      trustPoints: JSON.parse(d.trustPoints) as { icon: string; title: string; description: string }[],
      faqs: JSON.parse(d.faqs) as { question: string; answer: string }[],
      breadcrumbs: JSON.parse(d.breadcrumbs) as { label: string; href?: string }[],
      serviceValue: d.serviceValue ?? service.slug,
      showGasSafeNote: d.showGasSafeNote,
      accentColor: (d.accentColor === "blue" ? "blue" : "red") as "red" | "blue",
      metaTitle: d.metaTitle,
      metaDescription: d.metaDescription,
    };
  } catch {
    return null;
  }
}

export async function listServices(): Promise<ServiceListItem[]> {
  try {
    const services = await prisma.service.findMany({
      orderBy: [{ parentSlug: "asc" }, { sortOrder: "asc" }],
    });
    return services.map((s) => ({
      slug: s.slug,
      title: s.title,
      shortDescription: s.shortDescription,
      sector: s.sector,
      discipline: s.discipline,
      parentSlug: s.parentSlug,
      sortOrder: s.sortOrder,
    }));
  } catch {
    return [];
  }
}

/** Keyed content blocks (About timeline, Home sections, etc.). Returns parsed JSON or null. */
export async function getContentBlock<T = unknown>(key: string): Promise<T | null> {
  try {
    const block = await prisma.contentBlock.findUnique({
      where: { key },
    });
    if (!block) return null;
    return JSON.parse(block.value) as T;
  } catch {
    return null;
  }
}
