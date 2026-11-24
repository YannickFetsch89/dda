// Admin-Bereich – SEO-Aufräumen (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.10, Stufe 5b).
import type { Metadata } from "next";
import { SeoListe } from "./liste";

export const metadata: Metadata = { title: "SEO-Aufräumen" };

export default function AdminSeoAufraeumen() {
  return <SeoListe />;
}
