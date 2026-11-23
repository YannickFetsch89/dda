"use client";
// Event bearbeiten: Felder (Whitelist), Schalter, Redaktionsänderungen zurücksetzen, als Dublette markieren.
// Jede gespeicherte Änderung schützt das Feld vor der Pipeline (redaktion_felder, Plan 4.4).
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { KATEGORIEN, kategorieAusDb } from "@/lib/kategorien";

interface Event {
  id: string;
  slug: string | null;
  titel: string;
  datum: string;
  datum_bis: string | null;
  uhrzeit: string | null;
  ort: string;
  adresse: string | null;
  stadtteil: string | null;
  kategorie: string;
  unterkategorie: string | null;
  preis: string | null;
  beschreibung: string | null;
  bild_url: string | null;
  ort_id: string | null;
  quelle_name: string | null;
  quelle_url: string | null;
  abgelehnt: boolean;
  abgesagt: boolean;
  nicht_empfehlen: boolean;
  tipp_des_tages: boolean;
  erstellt_am: string | null;
  redaktion_felder: string[] | null;
  abgleich_titel: string | null;
  abgleich_datum: string | null;
  abgleich_uhrzeit: string | null;
  abgleich_ort: string | null;
}

interface Treffer {
  id: string;
  titel: string;
  datum: string;
  uhrzeit: string | null;
  ort: string;
  quelle_name: string | null;
}

const KOPF = { "Content-Type": "application/json" };
const TEXTFELDER: { feld: keyof Event; text: string; lang?: boolean; typ?: string }[] = [
  { feld: "titel", text: "Titel" },
  { feld: "datum", text: "Datum", typ: "date" },
  { feld: "datum_bis", text: "bis (mehrtägig)", typ: "date" },
  { feld: "uhrzeit", text: "Uhrzeit", typ: "time" },
  { feld: "ort", text: "Ort" },
  { feld: "adresse", text: "Adresse" },
  { feld: "stadtteil", text: "Stadtteil" },
  { feld: "unterkategorie", text: "Unterkategorie" },
  { feld: "preis", text: "Preis" },
  { feld: "bild_url", text: "Bild-Adresse" },
  { feld: "ort_id", text: "Ortszuordnung (ID)" },
  { feld: "beschreibung", text: "Beschreibung", lang: true },
];

async function senden(id: string, body: unknown): Promise<{ ok: boolean; daten: Record<string, unknown> }> {
  const r = await fetch(`/api/admin/events/${id}`, { method: "POST", headers: KOPF, body: JSON.stringify(body) });
  const daten = (await r.json().catch(() => ({}))) as Record<string, unknown>;
  return { ok: r.ok, daten };
}

export function EventBearbeiten() {
  const { id } = useParams<{ id: string }>();
  const [e, setE] = useState<Event | null>(null);
  const [pfad, setPfad] = useState<string | null>(null);
  const [meldung, setMeldung] = useState<{ art: "ok" | "fehler"; text: string } | null>(null);
  const [laeuft, setLaeuft] = useState(false);
  const [suche, setSuche] = useState("");
  const [treffer, setTreffer] = useState<Treffer[] | null>(null);

  const laden = useCallback(async () => {
    const r = await fetch(`/api/admin/events/${id}`, { cache: "no-store" });
    if (r.status === 401) return window.location.assign("/admin/anmelden");
    const d = (await r.json().catch(() => ({}))) as { event?: Event; pfad?: string; fehler?: string };
    if (!r.ok || !d.event) return setMeldung({ art: "fehler", text: d.fehler ?? "Event nicht gefunden." });
    setE(d.event);
    setPfad(d.pfad ?? null);
  }, [id]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- einmaliges Laden beim Öffnen
    laden();
  }, [laden]);

  async function speichern(ev: FormEvent<HTMLFormElement>) {
    ev.preventDefault();
    if (!e) return;
    const f = new FormData(ev.currentTarget);
    const felder: Record<string, unknown> = {};
    for (const t of TEXTFELDER) felder[t.feld] = String(f.get(t.feld) ?? "");
    felder.kategorie = String(f.get("kategorie") ?? "");
    for (const s of ["abgesagt", "abgelehnt", "nicht_empfehlen"]) felder[s] = f.get(s) === "on";
    setLaeuft(true);
    const { ok, daten } = await senden(e.id, { felder });
    setLaeuft(false);
    if (!ok) return setMeldung({ art: "fehler", text: String(daten.fehler ?? "Speichern hat nicht geklappt.") });
    const geaendert = (daten.geaendert as string[] | undefined) ?? [];
    setMeldung({ art: "ok", text: geaendert.length ? `Gespeichert: ${geaendert.join(", ")}. Die Pipeline lässt diese Felder jetzt in Ruhe.` : "Keine Änderung." });
    laden();
  }

  async function zuruecksetzen() {
    if (!e || !window.confirm("Redaktionsänderungen zurücksetzen? Danach darf die Pipeline alle Felder wieder füllen.")) return;
    const { ok, daten } = await senden(e.id, { aktion: "zuruecksetzen" });
    setMeldung(ok ? { art: "ok", text: "Zurückgesetzt." } : { art: "fehler", text: String(daten.fehler ?? "Hat nicht geklappt.") });
    laden();
  }

  async function dublettenSuche(ev: FormEvent<HTMLFormElement>) {
    ev.preventDefault();
    if (!e) return;
    const p = new URLSearchParams({ von: e.datum, bis: e.datum_bis ?? e.datum, q: suche });
    const r = await fetch(`/api/admin/events?${p.toString()}`, { cache: "no-store" });
    const d = (await r.json().catch(() => ({}))) as { events?: Treffer[] };
    setTreffer((d.events ?? []).filter((t) => t.id !== e.id));
  }

  async function alsDublette(behalten: Treffer) {
    if (!e || !window.confirm(`Dieses Event als Dublette von „${behalten.titel}“ ausblenden und dorthin umleiten?`)) return;
    const { ok, daten } = await senden(e.id, { aktion: "dublette", behalten: behalten.id });
    if (ok && typeof daten.weiter === "string") return window.location.assign(daten.weiter);
    setMeldung({ art: "fehler", text: String(daten.fehler ?? "Zusammenlegen hat nicht geklappt.") });
  }

  if (!e) return meldung ? <p className="admin-fehler">{meldung.text}</p> : <p className="admin-unterzeile">Wird geladen …</p>;
  const geschuetzt = new Set(e.redaktion_felder ?? []);

  return (
    <>
      <p className="admin-unterzeile">
        <Link href="/admin/events">← Events</Link>
        {pfad && !e.abgelehnt && (
          <>
            {" · "}
            <a href={`https://diesdas.events${pfad}`} target="_blank" rel="noreferrer noopener">
              Live-Seite
            </a>
          </>
        )}
        {e.quelle_url && (
          <>
            {" · "}
            <a href={e.quelle_url} target="_blank" rel="noreferrer noopener">
              Quelle ({e.quelle_name})
            </a>
          </>
        )}
      </p>
      <h1>{e.titel}</h1>
      {meldung && <p className={meldung.art === "ok" ? "admin-karte" : "admin-fehler"} role="status">{meldung.text}</p>}

      {geschuetzt.size > 0 && (
        <section className="admin-karte">
          <h2>Von der Redaktion geändert</h2>
          <p>
            Geschützt vor der Pipeline: <strong>{[...geschuetzt].join(", ")}</strong>.
            {e.abgleich_datum && (
              <>
                {" "}Die Pipeline erkennt das Event weiter an den Werten der Quelle: „{e.abgleich_titel}“, {e.abgleich_datum}
                {e.abgleich_uhrzeit ? ` ${e.abgleich_uhrzeit.slice(0, 5)}` : ""}, {e.abgleich_ort}.
              </>
            )}
          </p>
          <button type="button" className="admin-knopf admin-knopf--leise" onClick={zuruecksetzen}>
            Redaktionsänderungen zurücksetzen
          </button>
        </section>
      )}

      <form className="admin-karte admin-formular" onSubmit={speichern} key={JSON.stringify(e)}>
        {TEXTFELDER.map((t) => {
          const wert = t.feld === "uhrzeit" ? (e.uhrzeit ?? "").slice(0, 5) : String(e[t.feld] ?? "");
          return (
            <label key={t.feld} className={`admin-feld${t.lang ? " admin-feld--breit" : ""}`}>
              <span>
                {t.text}
                {geschuetzt.has(t.feld) && <small> · geschützt</small>}
              </span>
              {t.lang ? <textarea name={t.feld} defaultValue={wert} rows={6} /> : <input name={t.feld} type={t.typ ?? "text"} defaultValue={wert} />}
            </label>
          );
        })}
        <label className="admin-feld">
          <span>Kategorie{geschuetzt.has("kategorie") && <small> · geschützt</small>}</span>
          <select name="kategorie" defaultValue={kategorieAusDb(e.kategorie)}>
            {KATEGORIEN.map((k) => (
              <option key={k.slug} value={k.slug}>
                {k.name}
              </option>
            ))}
          </select>
        </label>
        <fieldset className="admin-feld admin-feld--breit admin-schalter">
          <label><input type="checkbox" name="abgesagt" defaultChecked={e.abgesagt} /> abgesagt</label>
          <label><input type="checkbox" name="nicht_empfehlen" defaultChecked={e.nicht_empfehlen} /> nicht empfehlen</label>
          <label><input type="checkbox" name="abgelehnt" defaultChecked={e.abgelehnt} /> abgelehnt (von der Website nehmen)</label>
        </fieldset>
        <div className="admin-feld--breit">
          <button className="admin-knopf" type="submit" disabled={laeuft}>
            {laeuft ? "Speichert …" : "Speichern"}
          </button>
        </div>
      </form>

      {!e.abgelehnt && (
        <section className="admin-karte">
          <h2>Als Dublette markieren</h2>
          <p>Dieses Event ausblenden und auf das richtige Event umleiten. Merklisten ziehen mit um.</p>
          <form onSubmit={dublettenSuche} className="admin-filterleiste">
            <label className="admin-feld">
              Richtiges Event suchen (am selben Tag)
              <input value={suche} onChange={(x) => setSuche(x.target.value)} placeholder="Titel oder Ort" />
            </label>
            <button className="admin-knopf admin-knopf--leise" type="submit">
              Suchen
            </button>
          </form>
          {treffer && (
            <ul className="admin-liste">
              {treffer.length === 0 && <li className="admin-liste__eintrag">Kein anderes Event gefunden.</li>}
              {treffer.map((t) => (
                <li key={t.id} className="admin-liste__eintrag">
                  <strong>{t.titel}</strong>
                  <span>
                    {t.uhrzeit?.slice(0, 5) ?? "–"} · {t.ort} · {t.quelle_name ?? "–"}
                  </span>
                  <button type="button" className="admin-knopf admin-knopf--leise" onClick={() => alsDublette(t)}>
                    Das ist das richtige
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </>
  );
}
