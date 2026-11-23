"use client";
// Event-Liste: Zeitraum, Suche, Kategorie, Quelle und Filter-Chips; 50 je Seite. Filter stehen in der Adresse,
// damit „Zurück“ aus der Bearbeitung wieder dieselbe Liste zeigt.
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState, type FormEvent } from "react";
import { KATEGORIEN, kategorieAusDb } from "@/lib/kategorien";

interface Zeile {
  id: string;
  titel: string;
  datum: string;
  datum_bis: string | null;
  uhrzeit: string | null;
  ort: string;
  stadtteil: string | null;
  adresse: string | null;
  kategorie: string;
  quelle_name: string | null;
  bild_url: string | null;
  abgelehnt: boolean;
  abgesagt: boolean;
  nicht_empfehlen: boolean;
  tipp_des_tages: boolean;
  redaktion_felder: string[] | null;
}

interface Antwort {
  von: string;
  bis: string;
  seite: number;
  proSeite: number;
  gesamt: number;
  events: Zeile[];
}

const FILTER: { wert: string; text: string }[] = [
  { wert: "ohne_bild", text: "ohne Bild" },
  { wert: "ohne_stadtteil", text: "ohne Stadtteil" },
  { wert: "ohne_adresse", text: "ohne Adresse" },
  { wert: "ohne_ort_id", text: "ohne Ortszuordnung" },
  { wert: "abgesagt", text: "abgesagt" },
  { wert: "nicht_empfehlen", text: "nicht empfehlen" },
  { wert: "redaktion", text: "von Redaktion geändert" },
  { wert: "abgelehnt", text: "abgelehnt (ausgeblendet)" },
];

function datumKurz(iso: string): string {
  return `${iso.slice(8, 10)}.${iso.slice(5, 7)}.`;
}

function Liste() {
  const router = useRouter();
  const params = useSearchParams();
  const [daten, setDaten] = useState<Antwort | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const filter = (params.get("filter") ?? "").split(",").filter(Boolean);

  const laden = useCallback(async () => {
    try {
      const r = await fetch(`/api/admin/events?${params.toString()}`, { cache: "no-store" });
      if (r.status === 401) return window.location.assign("/admin/anmelden");
      const d = (await r.json()) as Antwort & { fehler?: string };
      if (!r.ok) throw new Error(d.fehler ?? `Fehler ${r.status}`);
      setDaten(d);
      setFehler(null);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Liste nicht ladbar.");
    }
  }, [params]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- Laden bei jeder Änderung der Filter
    laden();
  }, [laden]);

  function setzen(neu: Record<string, string | null>) {
    const p = new URLSearchParams(params.toString());
    for (const [k, v] of Object.entries(neu)) {
      if (v) p.set(k, v);
      else p.delete(k);
    }
    if (!("seite" in neu)) p.delete("seite");
    router.push(`/admin/events?${p.toString()}`);
  }

  function suchen(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setzen({
      q: String(f.get("q") ?? "") || null,
      von: String(f.get("von") ?? "") || null,
      bis: String(f.get("bis") ?? "") || null,
      kategorie: String(f.get("kategorie") ?? "") || null,
      quelle: String(f.get("quelle") ?? "") || null,
    });
  }

  function filterUmschalten(wert: string) {
    const neu = filter.includes(wert) ? filter.filter((f) => f !== wert) : [...filter, wert];
    setzen({ filter: neu.join(",") || null });
  }

  const seiten = daten ? Math.ceil(daten.gesamt / daten.proSeite) : 0;

  return (
    <>
      <h1>Events</h1>
      <p className="admin-unterzeile">
        {daten ? `${daten.gesamt.toLocaleString("de-DE")} Events vom ${datumKurz(daten.von)} bis ${datumKurz(daten.bis)}` : "Wird geladen …"}
      </p>

      <form className="admin-karte admin-filterleiste" onSubmit={suchen} key={params.toString()}>
        <label className="admin-feld">
          Suche (Titel, Ort)
          <input name="q" defaultValue={params.get("q") ?? ""} />
        </label>
        <label className="admin-feld">
          von
          <input name="von" type="date" defaultValue={params.get("von") ?? daten?.von ?? ""} />
        </label>
        <label className="admin-feld">
          bis
          <input name="bis" type="date" defaultValue={params.get("bis") ?? daten?.bis ?? ""} />
        </label>
        <label className="admin-feld">
          Kategorie
          <select name="kategorie" defaultValue={params.get("kategorie") ?? ""}>
            <option value="">alle</option>
            {KATEGORIEN.map((k) => (
              <option key={k.slug} value={k.slug}>
                {k.name}
              </option>
            ))}
          </select>
        </label>
        <label className="admin-feld">
          Quelle
          <input name="quelle" defaultValue={params.get("quelle") ?? ""} />
        </label>
        <button className="admin-knopf" type="submit">
          Suchen
        </button>
      </form>

      <div className="admin-chips" role="group" aria-label="Filter">
        {FILTER.map((f) => (
          <button key={f.wert} type="button" className="admin-chip" aria-pressed={filter.includes(f.wert)} onClick={() => filterUmschalten(f.wert)}>
            {f.text}
          </button>
        ))}
      </div>

      {fehler && <p className="admin-fehler" role="alert">{fehler}</p>}

      {daten && (
        <div className="admin-tabelle-rahmen">
          <table className="admin-tabelle">
            <thead>
              <tr>
                <th>Datum</th>
                <th>Titel</th>
                <th>Ort</th>
                <th>Kategorie</th>
                <th>Quelle</th>
                <th>Hinweise</th>
              </tr>
            </thead>
            <tbody>
              {daten.events.map((e) => (
                <tr key={e.id} className={e.abgelehnt ? "admin-zeile--grau" : undefined}>
                  <td>
                    {datumKurz(e.datum)}
                    {e.datum_bis && e.datum_bis > e.datum ? `–${datumKurz(e.datum_bis)}` : ""}
                    <br />
                    <small>{e.uhrzeit?.slice(0, 5) ?? ""}</small>
                  </td>
                  <td>
                    <Link href={`/admin/events/${e.id}`}>{e.titel}</Link>
                  </td>
                  <td>
                    {e.ort}
                    <br />
                    <small>{e.stadtteil ?? "– kein Stadtteil –"}</small>
                  </td>
                  <td>{kategorieAusDb(e.kategorie)}</td>
                  <td><small>{e.quelle_name ?? "–"}</small></td>
                  <td className="admin-hinweise">
                    {!e.bild_url && <span className="admin-marke-klein">kein Bild</span>}
                    {!e.adresse && <span className="admin-marke-klein">keine Adresse</span>}
                    {e.abgesagt && <span className="admin-marke-klein">abgesagt</span>}
                    {e.nicht_empfehlen && <span className="admin-marke-klein">nicht empfehlen</span>}
                    {e.tipp_des_tages && <span className="admin-marke-klein">Tipp</span>}
                    {e.abgelehnt && <span className="admin-marke-klein">abgelehnt</span>}
                    {!!e.redaktion_felder?.length && <span className="admin-marke-klein" title={e.redaktion_felder.join(", ")}>Redaktion</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {seiten > 1 && daten && (
        <nav className="admin-seiten" aria-label="Seiten">
          <button type="button" className="admin-knopf admin-knopf--leise" disabled={daten.seite === 0} onClick={() => setzen({ seite: String(daten.seite - 1) })}>
            zurück
          </button>
          <span>
            Seite {daten.seite + 1} von {seiten}
          </span>
          <button type="button" className="admin-knopf admin-knopf--leise" disabled={daten.seite + 1 >= seiten} onClick={() => setzen({ seite: String(daten.seite + 1) })}>
            weiter
          </button>
        </nav>
      )}
    </>
  );
}

export function EventListe() {
  return (
    <Suspense fallback={<p className="admin-unterzeile">Wird geladen …</p>}>
      <Liste />
    </Suspense>
  );
}
