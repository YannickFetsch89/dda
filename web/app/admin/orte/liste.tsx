"use client";
// Orte-Liste: Typ, Suche, Status und Filter-Chips; 50 je Seite. Filter stehen in der Adresse, damit „Zurück“ aus der
// Bearbeitung wieder dieselbe Liste zeigt (wie die Event-Liste).
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState, type FormEvent } from "react";
import { ORT_TYPEN } from "@/lib/admin/orte";

interface Zeile {
  id: string;
  name: string;
  slug: string;
  typ: string;
  stadtteil: string | null;
  adresse: string | null;
  aktiv: boolean | null;
  qualitaets_score: number | null;
  bild_url: string | null;
  google_foto: unknown;
  latitude: number | null;
  parent_id: string | null;
  hat_text: boolean;
  text_freigegeben: unknown;
  text_entwurf: string | null;
  score_manuell: unknown;
}

interface Antwort {
  seite: number;
  proSeite: number;
  gesamt: number;
  orte: Zeile[];
}

const FILTER: { wert: string; text: string }[] = [
  { wert: "inaktiv", text: "nur inaktive" },
  { wert: "ohne_text", text: "ohne Text" },
  { wert: "text_entwurf", text: "Text-Entwurf wartet" },
  { wert: "ohne_bild", text: "ohne Bild" },
  { wert: "ohne_geo", text: "ohne Geo" },
  { wert: "ohne_adresse", text: "ohne Adresse" },
];

const TYP_TEXT = new Map(ORT_TYPEN.map((t) => [t.wert as string, t.text]));

function Liste() {
  const router = useRouter();
  const params = useSearchParams();
  const [daten, setDaten] = useState<Antwort | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const filter = (params.get("filter") ?? "").split(",").filter(Boolean);

  const laden = useCallback(async () => {
    try {
      const r = await fetch(`/api/admin/orte?${params.toString()}`, { cache: "no-store" });
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
    router.push(`/admin/orte?${p.toString()}`);
  }

  function suchen(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setzen({ q: String(f.get("q") ?? "") || null, typ: String(f.get("typ") ?? "") || null });
  }

  function filterUmschalten(wert: string) {
    const neu = filter.includes(wert) ? filter.filter((f) => f !== wert) : [...filter, wert];
    setzen({ filter: neu.join(",") || null });
  }

  const seiten = daten ? Math.ceil(daten.gesamt / daten.proSeite) : 0;

  return (
    <>
      <h1>Orte</h1>
      <p className="admin-unterzeile">
        {daten ? `${daten.gesamt.toLocaleString("de-DE")} ${filter.includes("inaktiv") ? "inaktive" : "aktive"} Orte` : "Wird geladen …"}
        {" · "}Guide-Pflege (Clubs ↔ Bar, Weihnachtsmärkte, Spielplätze), Bilder und Vorschläge folgen in Stufe 3b.
      </p>

      <form className="admin-karte admin-filterleiste" onSubmit={suchen} key={params.toString()}>
        <label className="admin-feld">
          Suche (Name, Slug, Adresse)
          <input name="q" defaultValue={params.get("q") ?? ""} />
        </label>
        <label className="admin-feld">
          Typ
          <select name="typ" defaultValue={params.get("typ") ?? ""}>
            <option value="">alle</option>
            {ORT_TYPEN.map((t) => (
              <option key={t.wert} value={t.wert}>
                {t.text}
              </option>
            ))}
          </select>
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
                <th>Name</th>
                <th>Typ</th>
                <th>Stadtteil</th>
                <th>Score</th>
                <th>Hinweise</th>
              </tr>
            </thead>
            <tbody>
              {daten.orte.map((o) => (
                <tr key={o.id} className={o.aktiv ? undefined : "admin-zeile--grau"}>
                  <td>
                    <Link href={`/admin/orte/${o.id}`}>{o.name}</Link>
                    <br />
                    <small>{o.slug}</small>
                  </td>
                  <td>{TYP_TEXT.get(o.typ) ?? o.typ}</td>
                  <td>{o.stadtteil ?? "–"}</td>
                  <td>
                    {o.qualitaets_score ?? "–"}
                    {!!o.score_manuell && <small title={String(o.score_manuell)}> fest</small>}
                  </td>
                  <td className="admin-hinweise">
                    {!o.aktiv && <span className="admin-marke-klein">inaktiv</span>}
                    {o.parent_id && <span className="admin-marke-klein">Saal</span>}
                    {!o.hat_text && <span className="admin-marke-klein">kein Text</span>}
                    {o.typ === "spielstaette" && !o.text_freigegeben && <span className="admin-marke-klein">Text nicht freigegeben</span>}
                    {o.text_entwurf && <span className="admin-marke-klein">Entwurf vom {o.text_entwurf.split("-").reverse().join(".")}</span>}
                    {!o.bild_url && !o.google_foto && <span className="admin-marke-klein">kein Bild</span>}
                    {o.latitude === null && <span className="admin-marke-klein">keine Geo</span>}
                    {!o.adresse && <span className="admin-marke-klein">keine Adresse</span>}
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

export function OrteListe() {
  return (
    <Suspense fallback={<p className="admin-unterzeile">Wird geladen …</p>}>
      <Liste />
    </Suspense>
  );
}
