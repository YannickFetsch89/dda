// Guide-Stadtteilseite /guides/kneipen-bars/stadtteil/{slug} – Inhalt in components/guide-stadtteil.tsx
import type { Metadata } from "next";
import { GuideStadtteil, guideStadtteilMetadaten } from "@/components/guide-stadtteil";

type Props = { params: Promise<{ slug: string }> };

export const instant = false;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  return guideStadtteilMetadaten("kneipen-bars", (await params).slug);
}

export default async function Seite({ params }: Props) {
  return <GuideStadtteil hub="kneipen-bars" slug={(await params).slug} />;
}
