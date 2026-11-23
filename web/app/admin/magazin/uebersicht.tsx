"use client";
// Magazin-Übersicht: Redaktionsplan (feste Termine), alle Beiträge, neuen Beitrag anlegen, Entwurf-Job starten,
// Autoren, KI-Kosten.
import Link from "next/link";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import type { ListenBeitrag, PlanTermin } from "@/lib/admin/magazin";
import { RUBRIKEN, RUBRIK_NAME } from "@/lib/magazin";

interface Autor {
  slug: string;
  name: string;
  kurzbeschreibung: string;
  schwerpunkt: string;
  rubriken: string[];
  aktiv: boolean;
}

interface Daten {
  heute: string;
  beitraege: ListenBeitrag[];
  plan: PlanTermin[];
  kosten: { summe_usd: number; je_monat: { monat: string; usd: number; laeufe: number }[] } | null;
  autoren: Autor[];
}

const KOPF = { "Content-Type": "application/json" };
const STATUS = { entwurf: "Entwurf", in_pruefung: "geprüft, wartet", veroeffentlicht: "veröffentlicht", zurueckgezogen: "zurückgezogen" } as const;

function datum(iso: string | null): string {
  return iso ? `${iso.slice(8, 10)}.${iso.slice(5, 7)}.${iso.slice(2, 4)}` : "–";
}

export function MagazinUebersicht() {
  const [daten, setDaten] = useState<Daten | null>(null);
  const [meldung, setMeldung] = useState<{ art: "ok" | "fehler"; text: string } | null>(null);
  const [filter, setFilter] = useState<string>("offen");

  const laden = useCallback(async () => {
    const r = await fetch("/api/admin/magazin", { cache: "no-store" });
    if (r.status === 401) return window.location.assign("/admin/anmelden");
    const d = (await r.json().catch(() => ({}))) as Daten & { fehler?: string };
    if (!r.ok) return setMeldung({ art: "fehler", text: d.fehler ?? "Magazin nicht ladbar." });
    setDaten(d);
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- einmaliges Laden beim Öffnen
    laden();
  }, [laden]);

  async function senden(body: unknown): Promise<Record<string, unknown> | null> {
    const r = await fetch("/api/admin/magazin", { method: "POST", headers: KOPF, body: JSON.stringify(body) });
    const d = (await r.json().catch(() => ({}))) as Record<string, unknown>;
    if (!r.ok) {
      setMeldung({ art: "fehler", text: String(d.fehler ?? "Hat nicht geklappt.") });
      return null;
    }
    return d;
  }

  async function anlegen(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const d = await senden({ aktion: "anlegen", rubrik: f.get("rubrik"), autor: f.get("autor"), titel: f.get("titel") });
    if (d && typeof d.weiter === "string") window.location.assign(d.weiter);
  }

  async function job(aufgabe: string, dryRun: boolean, von?: string) {
    if (!dryRun && !window.confirm("Entwurf mit KI erzeugen? Das kostet etwa 0,20–0,30 $ und schreibt einen neuen Entwurf.")) return;
    const d = await senden({ aktion: "job", aufgabe, dry_run: dryRun, von });
    if (d) setMeldung({ art: "ok", text: `${dryRun ? "Probelauf" : "Entwurf-Lauf"} gestartet. Der Entwurf erscheint nach einigen Minuten hier.` });
  }

  async function autorUmschalten(a: Autor) {
    const d = await senden({ aktion: "autor", slug: a.slug, felder: { aktiv: !a.aktiv } });
    if (d) laden();
  }

  if (!daten) return meldung ? <p className="admin-fehler">{meldung.text}</p> : <p className="admin-unterzeile">Wird geladen …</p>;
  const liste = daten.beitraege.filter((b) => (filter === "offen" ? b.status === "entwurf" || b.status === "in_pruefung" : filter === "alle" ? true : b.status === filter));

  return (
    <>
      <h1>Magazin</h1>
      <p className="admin-unterzeile">Redaktionsplan, Entwürfe prüfen und veröffentlichen – ohne SQL-Editor.</p>
      {meldung && <p className={meldung.art === "ok" ? "admin-karte" : "admin-fehler"} role="status">{meldung.text}</p>}

      <h2 className="admin-abschnitt">Redaktionsplan</h2>
      <ul className="admin-liste">
        {daten.plan.map((t) => (
          <li key={`${t.rubrik}-${t.von}`} className={`admin-liste__eintrag admin-liste__eintrag--${t.farbe}`}>
            <strong>
              {RUBRIK_NAME[t.rubrik]} ab {datum(t.von)}
            </strong>
            {t.beitrag ? <Link href={`/admin/magazin/${t.beitrag.id}`}>{t.beitrag.titel}</Link> : null}
            <span>{t.text}</span>
            {!t.beitrag && (
              <span className="admin-aktionen">
                <button type="button" className="admin-knopf admin-knopf--leise" onClick={() => job(`entwurf-${t.rubrik}`, true, t.von)}>
                  Probelauf
                </button>
                <button type="button" className="admin-knopf admin-knopf--leise" onClick={() => job(`entwurf-${t.rubrik}`, false, t.von)}>
                  Entwurf erzeugen
                </button>
              </span>
            )}
          </li>
        ))}
      </ul>

      <h2 className="admin-abschnitt">Beiträge</h2>
      <div className="admin-chips" role="group" aria-label="Status">
        {[
          ["offen", "offen"],
          ["veroeffentlicht", "veröffentlicht"],
          ["zurueckgezogen", "zurückgezogen"],
          ["alle", "alle"],
        ].map(([w, t]) => (
          <button key={w} type="button" className="admin-chip" aria-pressed={filter === w} onClick={() => setFilter(w)}>
            {t}
          </button>
        ))}
      </div>
      <div className="admin-tabelle-rahmen">
        <table className="admin-tabelle">
          <thead>
            <tr>
              <th>Titel</th>
              <th>Rubrik</th>
              <th>Zeitraum</th>
              <th>Status</th>
              <th>Prüfung</th>
            </tr>
          </thead>
          <tbody>
            {liste.map((b) => (
              <tr key={b.id}>
                <td>
                  <Link href={`/admin/magazin/${b.id}`}>{b.titel}</Link>
                </td>
                <td>{RUBRIK_NAME[b.rubrik as keyof typeof RUBRIK_NAME] ?? b.rubrik}</td>
                <td>
                  {b.gueltig_von ? `${datum(b.gueltig_von)}–${datum(b.gueltig_bis)}` : b.veroeffentlicht_am ? `seit ${datum(b.veroeffentlicht_am.slice(0, 10))}` : "–"}
                </td>
                <td>{STATUS[b.status]}</td>
                <td>{b.pruefung_ergebnis === "gruen" ? "grün" : b.pruefung_ergebnis === "rot" ? "rot" : "–"}</td>
              </tr>
            ))}
            {!liste.length && (
              <tr>
                <td colSpan={5}>Keine Beiträge.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="admin-empf-raster">
        <form className="admin-karte" onSubmit={anlegen}>
          <h2>Neuer Beitrag</h2>
          <label className="admin-feld">
            Rubrik
            <select name="rubrik" defaultValue="stadtleben">
              {RUBRIKEN.map((r) => (
                <option key={r} value={r}>
                  {RUBRIK_NAME[r]}
                </option>
              ))}
            </select>
          </label>
          <label className="admin-feld">
            Autor
            <select name="autor">
              {daten.autoren.filter((a) => a.aktiv).map((a) => (
                <option key={a.slug} value={a.slug}>
                  {a.name}
                </option>
              ))}
            </select>
          </label>
          <label className="admin-feld">
            Titel
            <input name="titel" maxLength={90} required />
          </label>
          <button className="admin-knopf" type="submit">
            Entwurf anlegen
          </button>
        </form>

        <section className="admin-karte">
          <h2>Autoren</h2>
          <ul className="admin-liste">
            {daten.autoren.map((a) => (
              <li key={a.slug} className="admin-liste__eintrag">
                <strong>{a.name}</strong>
                <span>{a.schwerpunkt}</span>
                <button type="button" className="admin-chip" aria-pressed={a.aktiv} onClick={() => autorUmschalten(a)}>
                  {a.aktiv ? "aktiv" : "inaktiv"}
                </button>
              </li>
            ))}
          </ul>
          {daten.kosten && (
            <p className="admin-unterzeile">
              KI-Kosten (6 Monate): {Number(daten.kosten.summe_usd).toFixed(2)} $
              {daten.kosten.je_monat.map((m) => ` · ${m.monat}: ${Number(m.usd).toFixed(2)} $`).join("")}
            </p>
          )}
        </section>
      </div>
    </>
  );
}
