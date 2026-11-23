"use client";
// Empfehlungen: Was zeigt die Startseite an einem Tag, und warum? Flaggen direkt setzen; Kalender der nächsten 30 Tage.
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import type { EmpfehlungsDaten, EventKurz, Flagge } from "@/lib/admin/empfehlungen";

const KOPF = { "Content-Type": "application/json" };
const WT = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];

function tagText(iso: string): string {
  const d = new Date(`${iso}T12:00:00Z`);
  return `${WT[d.getUTCDay()]} ${iso.slice(8, 10)}.${iso.slice(5, 7)}.`;
}

function Zeile({ e, kompakt }: { e: EventKurz; kompakt?: boolean }) {
  return (
    <div className="admin-empf-zeile">
      <div>
        <Link href={`/admin/events/${e.id}`}>
          <strong>{e.titel}</strong>
        </Link>
        <small>
          {" "}
          {e.uhrzeit?.slice(0, 5) ?? ""} · {e.ort} · {e.kategorie}
          {!e.bild && " · kein Bild"}
          {e.ausserhalbFokus && " · nicht am Fokustag"}
        </small>
      </div>
      {!kompakt && (
        <div className="admin-empf-gruende">
          <span className="admin-marke-klein">Stufe {e.stufe ?? "–"}</span>
          {e.gruende.join(" · ")}
          {e.flaggen.tipp && <span className="admin-marke-klein">Tipp{e.flaggen.tippGilt ? "" : " (gilt heute nicht)"}</span>}
          {e.flaggen.highlight && <span className="admin-marke-klein">Highlight</span>}
          {e.flaggen.top && <span className="admin-marke-klein">Top</span>}
        </div>
      )}
    </div>
  );
}

export function Empfehlungen() {
  const router = useRouter();
  const params = useSearchParams();
  const [daten, setDaten] = useState<EmpfehlungsDaten | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [arbeitet, setArbeitet] = useState<string | null>(null);
  const tag = params.get("tag") ?? "";

  const laden = useCallback(async () => {
    const r = await fetch(`/api/admin/empfehlungen${tag ? `?tag=${tag}` : ""}`, { cache: "no-store" });
    if (r.status === 401) return window.location.assign("/admin/anmelden");
    const d = (await r.json().catch(() => ({}))) as EmpfehlungsDaten & { fehler?: string };
    if (!r.ok) return setFehler(d.fehler ?? "Vorschau nicht ladbar.");
    setDaten(d);
    setFehler(null);
  }, [tag]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- Laden bei Wechsel des Tags
    laden();
  }, [laden]);

  function tagSetzen(t: string) {
    router.push(`/admin/empfehlungen?tag=${t}`);
  }

  async function flagge(e: EventKurz, f: Flagge, wert: boolean) {
    setArbeitet(`${e.id}-${f}`);
    const r = await fetch("/api/admin/empfehlungen", { method: "POST", headers: KOPF, body: JSON.stringify({ event: e.id, flagge: f, wert }) });
    const d = (await r.json().catch(() => ({}))) as { fehler?: string };
    setArbeitet(null);
    if (!r.ok) return setFehler(d.fehler ?? "Hat nicht geklappt.");
    laden();
  }

  if (!daten) return fehler ? <p className="admin-fehler">{fehler}</p> : <p className="admin-unterzeile">Wird geladen …</p>;

  return (
    <>
      <div className="admin-kopfzeile">
        <div>
          <h1>Empfehlungen</h1>
          <p className="admin-unterzeile">
            So sieht die Startseite am {tagText(daten.tag)} aus ({" "}
            <a href={`https://diesdas.events/?datum=${daten.tag}`} target="_blank" rel="noreferrer noopener">
              live ansehen
            </a>
            ). Änderungen sind sofort sichtbar.
          </p>
        </div>
        <label className="admin-feld">
          Tag
          <input type="date" value={daten.tag} min={daten.heute} max={daten.bisTag} onChange={(x) => x.target.value && tagSetzen(x.target.value)} />
        </label>
      </div>
      {daten.quelle === "beispiel" && <p className="admin-fehler">Die Datenbank ist gerade nicht erreichbar – das sind Beispieldaten.</p>}
      {fehler && <p className="admin-fehler" role="alert">{fehler}</p>}

      <div className="admin-empf-raster">
        <section className="admin-karte">
          <h2>Tipp des Tages {daten.vonRedaktion && <span className="admin-marke-klein">Von der Redaktion</span>}</h2>
          {daten.tipp ? <Zeile e={daten.tipp} /> : <p>Kein Tipp an diesem Tag.</p>}
        </section>
        <section className="admin-karte">
          <h2>Picks</h2>
          {daten.picks.length ? daten.picks.map((e) => <Zeile key={e.id} e={e} />) : <p>Keine Picks.</p>}
        </section>
        <section className="admin-karte">
          <h2>Diese Woche beliebt</h2>
          {daten.beliebt.map((e) => (
            <Zeile key={e.id} e={e} kompakt />
          ))}
        </section>
        <section className="admin-karte">
          <h2>Highlight der Woche · Top-Event des Monats</h2>
          <p className="admin-unterzeile">Stand heute, unabhängig vom gewählten Tag.</p>
          {daten.highlight && <Zeile e={daten.highlight} kompakt />}
          {daten.top && <Zeile e={daten.top} kompakt />}
        </section>
      </div>

      <h2 className="admin-abschnitt">Wochenend-Tipps (hängen am heutigen Tag)</h2>
      <div className="admin-empf-raster admin-empf-raster--drei">
        {daten.wochenende.map((w) => (
          <section key={w.tag} className="admin-karte">
            <h2>
              {w.name} {tagText(w.tag)}
            </h2>
            {w.events.map((e) => (
              <Zeile key={e.id} e={e} kompakt />
            ))}
          </section>
        ))}
      </div>

      <h2 className="admin-abschnitt">Alle Kandidaten am {tagText(daten.tag)} (Reihenfolge wie auf der Startseite)</h2>
      <ul className="admin-liste">
        {daten.kandidaten.map((e) => (
          <li key={e.id} className="admin-liste__eintrag admin-empf-kandidat">
            <Zeile e={e} />
            <span className="admin-aktionen">
              {(
                [
                  ["tipp", "Tipp", e.flaggen.tipp],
                  ["highlight", "Highlight", e.flaggen.highlight],
                  ["top", "Top", e.flaggen.top],
                  ["nicht_empfehlen", "nicht empfehlen", e.flaggen.nichtEmpfehlen],
                ] as [Flagge, string, boolean][]
              ).map(([f, text, an]) => (
                <button key={f} type="button" className="admin-chip" aria-pressed={an} disabled={arbeitet === `${e.id}-${f}`} onClick={() => flagge(e, f, !an)}>
                  {text}
                </button>
              ))}
            </span>
          </li>
        ))}
      </ul>

      <h2 className="admin-abschnitt">Kalender: Tipp der nächsten 30 Tage</h2>
      <div className="admin-kalender">
        {daten.kalender.map((k) => (
          <button
            key={k.tag}
            type="button"
            className={`admin-kalender__tag${k.redaktion ? " admin-kalender__tag--redaktion" : ""}${k.tag === daten.tag ? " admin-kalender__tag--aktiv" : ""}`}
            onClick={() => tagSetzen(k.tag)}
          >
            <strong>{tagText(k.tag)}</strong>
            <span>{k.tipp ? k.tipp.titel : "kein Tipp"}</span>
            <small>{k.redaktion ? "Redaktion" : "automatisch"}{k.tipp && !k.tipp.bild ? " · kein Bild" : ""}</small>
          </button>
        ))}
      </div>
    </>
  );
}
