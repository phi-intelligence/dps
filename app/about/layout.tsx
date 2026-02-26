import type { Metadata } from "next";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "About Us",
  description: `${COMPANY.name} — mechanical, electrical and gas services across ${COMPANY.areas}. Our story, founder, and commitment to quality. Gas Safe registered.`,
};

export default function AboutLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
