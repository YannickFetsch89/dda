"use client";
// Technik und Kosten (Plan Admin-Dashboard 4.10, Stufe 5a): Speicherplatz, Ordnergrößen, KI-Kosten Magazin, Schalter.
import { useEffect, useState } from "react";

interface Ordner {
  bytes: number;
  dateien: number;
  vollstaendig: boolean;
}

interface Antwort {
  platte: { gesamt: number; frei: number } | null;
  ordner: { logs: Ordner | null; next: Ordner | null };
  magazin_kosten: { summe_usd: number; je_monat: { monat: string; usd: number; laeufe: number }[] } | null;
  schalter: { art: "ok"; werte: Record<string, string | null>; link: string } | { art: "kein_token" } | { art: "fehler"; meldung: string };
  hinweis_kosten: string;
}

const SCHALTER_TEXT: Record<string, string> = {
  KONTEN_AKTIV: "Nutzerkonten",
  MAGAZIN_AKTIV: "Magazin-Job",
  GEBURTSTAG_AKTIV: "Geburtstagsmail",
  NEWSLETTER_AKTIV: "Newsletter-Bestätigung",
  ORTSSEITEN_MELDEN: "Ortsseiten an IndexNow melden",
};

function groesse(b: number): string {
  if (b >= 1024 ** 3) return `${(b / 1024 ** 3).toFixed(1)} GB`;
  if (b >= 1024 ** 2) return `${(b / 1024 ** 2).toFixed(0)} MB`;
  return `${Math.round(b / 1024)} KB`;
}

export function TechnikAnsicht() {
  const [d, setD] = useState<Antwort | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/admin/technik", { cache: "no-store" })
      .then(async (r) => {
        if (r.status === 401) return window.location.assign("/admin/anmelden");
        const x = (await r.json().catch(() => ({}))) as Antwort & { fehler?: string };
        if (!r.ok) return setFehler(x.fehler ?? "Nicht ladbar.");
        setD(x);
      })
      .catch(() => setFehler("Keine Verbindung."));
  }, []);

  if (fehler) return <p className="admin-fehler">{fehler}</p>;
  if (!d) return <p className="admin-unterzeile">Wird geladen …</p>;
  const belegt = d.platte ? 1 - d.platte.frei / d.platte.gesamt : null;

  return (
    <>
      <h1>Technik</h1>
      <div className="admin-kacheln">
        <div className="admin-karte">
          <strong>{d.platte ? groesse(d.platte.frei) : "–"}</strong> frei auf dem Server
          {belegt !== null && <small> ({Math.round(belegt * 100)} % belegt)</small>}
        </div>
        <div className="admin-karte">
          <strong>{d.ordner.logs ? groesse(d.ordner.logs.bytes) : "–"}</strong> logs/
          {d.ordner.logs && !d.ordner.logs.vollstaendig && <small> (mindestens)</small>}
        </div>
        <div className="admin-karte">
          <strong>{d.ordner.next ? groesse(d.ordner.next.bytes) : "–"}</strong> web/.next
          {d.ordner.next && !d.ordner.next.vollstaendig && <small> (mindestens)</small>}
        </div>
        <div className="admin-karte">
          <strong>{d.magazin_kosten ? `${Number(d.magazin_kosten.summe_usd).toFixed(2)} $` : "–"}</strong> KI-Kosten Magazin dieses Jahr
        </div>
      </div>
      {d.magazin_kosten?.je_monat?.length ? (
        <section className="admin-karte">
          <h2>KI-Kosten Magazin je Monat</h2>
          <p>{d.magazin_kosten.je_monat.map((m) => `${m.monat}: ${Number(m.usd).toFixed(2)} $ (${m.laeufe} Läufe)`).join(" · ")}</p>
        </section>
      ) : null}
      <p className="admin-unterzeile">{d.hinweis_kosten}</p>

      <section className="admin-karte">
        <h2>Schalter</h2>
        {d.schalter.art === "ok" ? (
          <>
            <ul className="admin-liste">
              {Object.entries(d.schalter.werte).map(([name, wert]) => (
                <li key={name} className="admin-liste__eintrag">
                  <strong>{SCHALTER_TEXT[name] ?? name}</strong>
                  <span>
                    {name} = {wert ?? "nicht gesetzt"} → {wert === "1" ? "an" : "aus"}
                  </span>
                </li>
              ))}
            </ul>
            <p>
              Ändern nur auf GitHub (E4), danach wirkt der Schalter beim nächsten Lauf bzw. Deploy:{" "}
              <a href={d.schalter.link} target="_blank" rel="noreferrer noopener">
                Repository-Variablen öffnen
              </a>
            </p>
          </>
        ) : (
          <p>{d.schalter.art === "kein_token" ? "GitHub nicht verbunden (ADMIN_GITHUB_TOKEN fehlt)." : `GitHub: ${d.schalter.meldung}`}</p>
        )}
      </section>
    </>
  );
}
