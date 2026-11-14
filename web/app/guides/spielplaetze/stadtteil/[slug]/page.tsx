// Guide-Stadtteilseite /guides/spielplaetze/stadtteil/{slug} – Inhalt in components/guide-stadtteil.tsx
import type { Metadata } from "next";
import { GuideStadtteil, guideStadtteilMetadaten } from "@/components/guide-stadtteil";

type Props = { params: Promise<{ slug: string }> };

export const instant = false;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  return guideStadtteilMetadaten("spielplaetze", (await params).slug);
}

export default async function Seite({ params }: Props) {
  return <GuideStadtteil hub="spielplaetze" slug={(await params).slug} />;
}
