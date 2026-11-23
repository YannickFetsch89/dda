// Admin-Bereich – Newsletter (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.9, Stufe 4).
import type { Metadata } from "next";
import { NewsletterListe } from "./liste";

export const metadata: Metadata = { title: "Newsletter" };

export default function AdminNewsletter() {
  return <NewsletterListe />;
}
