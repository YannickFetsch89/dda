// Admin-Bereich unter admin.diesdas.events (Plan docs/plan-admin-dashboard-2026-11-23.md, Stufe 1a).
// Statische Hülle: Daten kommen nur aus /api/admin/*, das Sitzung, Rolle und Zwei-Faktor serverseitig prüft.
import type { Metadata } from "next";
import { AdminRahmen } from "./rahmen";
import "./admin.css";

export const metadata: Metadata = {
  title: { default: "Admin", template: "%s · Admin · dies.das.düsseldorf" },
  robots: { index: false, follow: false, nocache: true, googleBot: { index: false, follow: false } },
};

export default function AdminLayout({ children }: LayoutProps<"/admin">) {
  return <AdminRahmen>{children}</AdminRahmen>;
}
