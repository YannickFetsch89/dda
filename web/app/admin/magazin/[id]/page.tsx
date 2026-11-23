// Admin-Bereich – Magazin-Beitrag bearbeiten, prüfen, veröffentlichen (Plan Admin-Dashboard 4.6, Stufe 2).
import type { Metadata } from "next";
import { Suspense } from "react";
import { MagazinBearbeiten } from "./bearbeiten";

export const metadata: Metadata = { title: "Magazin-Beitrag" };

export default function AdminMagazinBeitrag() {
  return (
    <Suspense fallback={<p className="admin-unterzeile">Wird geladen …</p>}>
      <MagazinBearbeiten />
    </Suspense>
  );
}
