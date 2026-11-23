// Admin-Bereich – Magazin (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.6, Stufe 2).
import type { Metadata } from "next";
import { MagazinUebersicht } from "./uebersicht";

export const metadata: Metadata = { title: "Magazin" };

export default function AdminMagazin() {
  return <MagazinUebersicht />;
}
