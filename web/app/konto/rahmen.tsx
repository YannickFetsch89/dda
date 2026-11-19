// Gemeinsamer Rahmen der Konto-Seiten (Plan 7.4): statische Hülle, noindex, ohne Sitzungs-Lesen auf dem Server.
// Ist der Schalter KONTEN_AKTIV aus, zeigt jede Seite nur „Noch nicht verfügbar“.
// Mein Bereich (Plan 3.2): Seitenleiste am Desktop und Zurück-Pfeil mobil, beide nur bei html[data-konto="1"] (CSS).
import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";
import { KontoSeitenleiste } from "@/components/konto-nav";
import { kontenAktiv } from "@/lib/konto/konfig";

export const KONTO_ROBOTS: Metadata["robots"] = { index: false, follow: false };

/** Raster mit Seitenleiste (Desktop, angemeldet); ohne Schalter nur der Inhalt */
export function KontoRaster({ children }: { children: ReactNode }) {
  if (!kontenAktiv()) return <>{children}</>;
  return (
    <div className="konto-raster">
      <KontoSeitenleiste />
      <div className="konto-raster__haupt">{children}</div>
    </div>
  );
}

/** zurueck: mobiler Pfeil zur Übersicht (nicht auf /konto selbst); breit: ohne 720er-Grenze, für Kartenraster */
export function KontoRahmen({
  titel, unter, zurueck = true, breit = false, children,
}: { titel: string; unter?: string; zurueck?: boolean; breit?: boolean; children: ReactNode }) {
  const an = kontenAktiv();
  return (
    <div className="container sektion">
      <KontoRaster>
        <div className={breit ? "konto-seite konto-seite--breit" : "konto-seite"}>
          <div className="seitentitel">
            {an && zurueck && (
              <Link href="/konto" className="konto-zurueck" aria-label="Zurück zur Übersicht">
                <span className="icon" aria-hidden data-icon="arrow_back" />
              </Link>
            )}
            <h1 className="d">{titel}</h1>
            {unter && <span>{unter}</span>}
          </div>
          {an ? (
            children
          ) : (
            <div className="status status--info" role="status">
              <span className="icon" aria-hidden data-icon="info" />
              <div>Konten sind noch nicht verfügbar. Deine Merkliste funktioniert wie gewohnt auf diesem Gerät.</div>
            </div>
          )}
        </div>
      </KontoRaster>
    </div>
  );
}
