// Guide-Stadtteilseite /guides/restaurants-cafes/stadtteil/{slug} – Inhalt in components/guide-stadtteil.tsx
import type { Metadata } from "next";
import { GuideStadtteil, guideStadtteilMetadaten } from "@/components/guide-stadtteil";

type Props = { params: Promise<{ slug: string }> };

export const instant = false;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  return guideStadtteilMetadaten("restaurants-cafes", (await params).slug);
}

export default async function Seite({ params }: Props) {
  return <GuideStadtteil hub="restaurants-cafes" slug={(await params).slug} />;
}
