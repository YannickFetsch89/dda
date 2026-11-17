// Gemeinsamer Rahmen der Konto-Seiten (Plan 7.4): statische Hülle, noindex, ohne Sitzungs-Lesen auf dem Server.
// Ist der Schalter KONTEN_AKTIV aus, zeigt jede Seite nur „Noch nicht verfügbar“.
import type { Metadata } from "next";
import type { ReactNode } from "react";
import { kontenAktiv } from "@/lib/konto/konfig";

export const KONTO_ROBOTS: Metadata["robots"] = { index: false, follow: false };

export function KontoRahmen({ titel, unter, children }: { titel: string; unter?: string; children: ReactNode }) {
  return (
    <div className="container sektion konto-seite">
      <div className="seitentitel">
        <h1 className="d">{titel}</h1>
        {unter && <span>{unter}</span>}
      </div>
      {kontenAktiv() ? (
        children
      ) : (
        <div className="status status--info" role="status">
          <span className="icon" aria-hidden data-icon="info" />
          <div>Konten sind noch nicht verfügbar. Deine Merkliste funktioniert wie gewohnt auf diesem Gerät.</div>
        </div>
      )}
    </div>
  );
}
