// Admin-Bereich – Scraper (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.3, Stufe 1c; Quellen an/aus Stufe 5b).
import type { Metadata } from "next";
import { QuellenSchalter } from "./quellen";
import { ScraperSeite } from "./scraper";

export const metadata: Metadata = { title: "Scraper" };

export default function AdminScraper() {
  return (
    <>
      <ScraperSeite />
      <QuellenSchalter />
    </>
  );
}
