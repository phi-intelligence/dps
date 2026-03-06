export type PageFieldType = "text" | "textarea";

export interface PageFieldConfig {
  id: string;
  label: string;
  type: PageFieldType;
  description?: string;
  multiline?: boolean;
  placeholder?: string;
  defaultValue?: string;
}

export interface PageConfig {
  id: string;
  label: string;
  description?: string;
  fields: PageFieldConfig[];
}

export const PAGE_CONFIGS: PageConfig[] = [
  {
    id: "home",
    label: "Home",
    description: "Hero and primary marketing copy for the homepage.",
    fields: [
      {
        id: "heroTitle",
        label: "Hero title",
        type: "text",
        placeholder: "Precision Heating & Plumbing",
        defaultValue: "",
      },
      {
        id: "heroSubtitle",
        label: "Hero description",
        type: "textarea",
        multiline: true,
        description: "Short sentence that sits under the hero title.",
        placeholder:
          "Engineered heating and plumbing for commercial plant rooms and homes across London and the South East.",
        defaultValue: "",
      },
      {
        id: "heroPrimaryCta",
        label: "Primary CTA label",
        type: "text",
        placeholder: "Book a consultation",
        defaultValue: "",
      },
      {
        id: "heroSecondaryCta",
        label: "Secondary CTA label",
        type: "text",
        placeholder: "View services",
        defaultValue: "",
      },
      {
        id: "operationalSnapshotHeading",
        label: "Operational snapshot heading",
        type: "text",
        placeholder: "Engineered Reliability. Luxury Finish.",
      },
      {
        id: "servicesHeading",
        label: "Services band heading",
        type: "text",
        placeholder: "Mechanical, Electrical & Gas",
      },
      {
        id: "servicesIntro",
        label: "Services band intro",
        type: "textarea",
        multiline: true,
        description: "Short line explaining how you work with clients.",
        placeholder:
          "Three clear paths into how we work with commercial estates and domestic homeowners.",
      },
      {
        id: "howWeWorkHeading",
        label: "How we work heading",
        type: "text",
        placeholder: "Engineered From First Sketch",
      },
      {
        id: "sectorsHeading",
        label: "Sectors heading",
        type: "text",
        placeholder: "Sectors We Partner With",
      },
      {
        id: "aboutBandHeading",
        label: "About band heading",
        type: "text",
        placeholder: "Disciplined Engineers. Clean Installs.",
      },
      {
        id: "aboutBandIntro",
        label: "About band intro",
        type: "textarea",
        multiline: true,
        placeholder:
          "Founded in 20XX, DPS Heating Services brings decades of experience across domestic and commercial plant.",
      },
    ],
  },
  {
    id: "about",
    label: "About Us",
    description: "Top-of-page heading and intro for the About page.",
    fields: [
      {
        id: "aboutHeading",
        label: "Main heading",
        type: "text",
        placeholder: "Disciplined Engineers. Clean Installs.",
      },
      {
        id: "aboutIntro",
        label: "Intro paragraph",
        type: "textarea",
        multiline: true,
        description: "Short paragraph explaining who DPS are and what they do.",
        placeholder:
          "Founded in 20XX, DPS Heating Services brings decades of experience across domestic and commercial plant.",
      },
      {
        id: "aboutMissionHeading",
        label: "Mission heading",
        type: "text",
        placeholder: "Our Mission",
      },
      {
        id: "aboutMissionBody",
        label: "Mission body",
        type: "textarea",
        multiline: true,
        placeholder:
          "Explain what drives the company and how projects are treated as engineered infrastructure.",
      },
      {
        id: "aboutVisionHeading",
        label: "Vision heading",
        type: "text",
        placeholder: "Our Vision",
      },
      {
        id: "aboutVisionBody",
        label: "Vision body",
        type: "textarea",
        multiline: true,
        placeholder:
          "Describe where the company is heading and how you want clients to experience working with DPS.",
      },
      {
        id: "aboutStatsHeading",
        label: "Stats / credentials heading",
        type: "text",
        placeholder: "Numbers that back the work",
      },
    ],
  },
  {
    id: "portfolio",
    label: "Portfolio",
    description: "High level heading and intro for project work.",
    fields: [
      {
        id: "portfolioHeading",
        label: "Main heading",
        type: "text",
        placeholder: "Selected Projects",
      },
      {
        id: "portfolioIntro",
        label: "Intro paragraph",
        type: "textarea",
        multiline: true,
        description: "One or two sentences describing the type of projects featured.",
        placeholder:
          "A snapshot of recent commercial and domestic projects, from boiler plant upgrades to full mechanical refurbishments.",
      },
      {
        id: "portfolioFeaturedTitle",
        label: "Featured project title",
        type: "text",
        placeholder: "Featured project heading",
      },
      {
        id: "portfolioFeaturedSummary",
        label: "Featured project summary",
        type: "textarea",
        multiline: true,
        placeholder:
          "Short summary of a flagship installation or contract to highlight at the top of the portfolio.",
      },
      {
        id: "portfolioGridHeading",
        label: "Projects grid heading",
        type: "text",
        placeholder: "Recent work",
      },
    ],
  },
];

export function getPageConfig(id: string): PageConfig | undefined {
  return PAGE_CONFIGS.find((page) => page.id === id);
}

