"use client";
// Ort bearbeiten: Stammdaten, Score, Text (Spielstätten, mit Quellen und Freigabe), kommende Events mit „Zuordnung
// lösen“, Zusammenlegen und Schließen – beides immer mit Weiterleitung (Trigger orte_schutz, Plan 4.7).
// Stufe 3b: Bild, Club-Hub, Weihnachtsmarkt, Spielplatz (guide-abschnitte.tsx).
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { CLUB_TYPEN } from "@/lib/admin/guides";
import { CSV_FELDER, ORT_TYPEN, STADTTEILE } from "@/lib/admin/orte";
import { BildAbschnitt, ClubAbschnitt, SpielplatzAbschnitt, WmAbschnitt, type GuideOrt } from "./guide-abschnitte";

interface Ort extends Omit<GuideOrt, "club"> {
  id: string;
  name: string;
  slug: string;
  typ: string;
  untertitel: string | null;
  beschreibung: string | null;
  highlight: string | null;
  adresse: string | null;
  stadtteil: string | null;
  latitude: number | null;
  longitude: number | null;
  bild_url: string | null;
  preis_niveau: string | null;
  oeffnungszeiten: string | null;
  webseite: string | null;
  telefon: string | null;
  instagram: string | null;
  google_place_id: string | null;
  google_rating: number | null;
  qualitaets_score: number | null;
  sortierung: number | null;
  aktiv: boolean | null;
  parent_id: string | null;
  aktualisiert_am: string | null;
  spielstaette: {
    event_orte?: string[];
    text_freigegeben?: { datum?: string; quellen?: string[] };
    text_entwurf?: { text?: string; quellen?: string[]; datum?: string };
  } | null;
  club: { event_orte?: string[] } | null;
  score_manuell: unknown;
}

interface Kurz {
  id: string;
  name: string;
  slug: string;
  aktiv: boolean | null;
  typ?: string;
  stadtteil?: string | null;
}

interface EventZeile {
  id: string;
  titel: string;
  datum: string;
  datum_bis: string | null;
  uhrzeit: string | null;
  ort: string;
  abgelehnt: boolean;
  abgesagt: boolean;
  quelle_name: string | null;
}

interface Daten {
  ort: Ort;
  pfad: string | null;
  haus: Kurz | null;
  saele: Kurz[];
  weiterleitungen: { alter_slug: string; grund: string | null }[];
  eigeneWeiterleitung: { alter_slug: string; ziel_ort_id: string | null; grund: string | null } | null;
  events: EventZeile[];
  eventsGesamt: number;
  vergangene: boolean;
}

const KOPF = { "Content-Type": "application/json" };
const TYP_TEXT = new Map(ORT_TYPEN.map((t) => [t.wert as string, t.text]));

const FELDER: { feld: keyof Ort; text: string; lang?: boolean; liste?: string }[] = [
  { feld: "name", text: "Name" },
  { feld: "untertitel", text: "Untertitel" },
  { feld: "adresse", text: "Adresse" },
  { feld: "stadtteil", text: "Stadtteil", liste: "admin-stadtteile" },
  { feld: "latitude", text: "Breite (lat)" },
  { feld: "longitude", text: "Länge (lon)" },
  { feld: "webseite", text: "Website" },
  { feld: "telefon", text: "Telefon" },
  { feld: "instagram", text: "Instagram" },
  { feld: "preis_niveau", text: "Preisniveau (€, €€, €€€)" },
  { feld: "sortierung", text: "Sortierung" },
  { feld: "highlight", text: "Highlight", lang: true },
  { feld: "oeffnungszeiten", text: "Öffnungszeiten", lang: true },
  { feld: "beschreibung", text: "Beschreibung", lang: true },
];

function datumDe(iso: string | null | undefined): string {
  return iso ? iso.slice(0, 10).split("-").reverse().join(".") : "–";
}

async function senden(id: string, body: unknown): Promise<{ ok: boolean; daten: Record<string, unknown> }> {
  const r = await fetch(`/api/admin/orte/${id}`, { method: "POST", headers: KOPF, body: JSON.stringify(body) });
  const daten = (await r.json().catch(() => ({}))) as Record<string, unknown>;
  return { ok: r.ok, daten };
}

/** Suche nach einem aktiven Ziel-Ort (für Zusammenlegen und Schließen) */
function OrtSuche({ ohne, onWaehlen, knopf }: { ohne: string; onWaehlen: (o: Kurz) => void; knopf: string }) {
  const [q, setQ] = useState("");
  const [treffer, setTreffer] = useState<Kurz[] | null>(null);

  async function suchen(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const r = await fetch(`/api/admin/orte?${new URLSearchParams({ q }).toString()}`, { cache: "no-store" });
    const d = (await r.json().catch(() => ({}))) as { orte?: Kurz[] };
    setTreffer((d.orte ?? []).filter((o) => o.id !== ohne));
  }

  return (
    <>
      <form onSubmit={suchen} className="admin-filterleiste">
        <label className="admin-feld">
          Aktiven Ort suchen
          <input value={q} onChange={(x) => setQ(x.target.value)} placeholder="Name, Slug oder Adresse" />
        </label>
        <button className="admin-knopf admin-knopf--leise" type="submit">
          Suchen
        </button>
      </form>
      {treffer && (
        <ul className="admin-liste">
          {treffer.length === 0 && <li className="admin-liste__eintrag">Kein aktiver Ort gefunden.</li>}
          {treffer.map((t) => (
            <li key={t.id} className="admin-liste__eintrag">
              <strong>{t.name}</strong>
              <span>
                {TYP_TEXT.get(t.typ ?? "") ?? t.typ} · {t.stadtteil ?? "–"} · {t.slug}
              </span>
              <button type="button" className="admin-knopf admin-knopf--leise" onClick={() => onWaehlen(t)}>
                {knopf}
              </button>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

export function OrtBearbeiten() {
  const { id } = useParams<{ id: string }>();
  const [d, setD] = useState<Daten | null>(null);
  const [meldung, setMeldung] = useState<{ art: "ok" | "fehler"; text: string } | null>(null);
  const [laeuft, setLaeuft] = useState(false);
  const [zielZusammen, setZielZusammen] = useState<Kurz | null>(null);
  const [zielSchliessen, setZielSchliessen] = useState<Kurz | null>(null);
  const [vergangene, setVergangene] = useState(false);

  const laden = useCallback(async () => {
    const r = await fetch(`/api/admin/orte/${id}${vergangene ? "?vergangene=1" : ""}`, { cache: "no-store" });
    if (r.status === 401) return window.location.assign("/admin/anmelden");
    const x = (await r.json().catch(() => ({}))) as Daten & { fehler?: string };
    if (!r.ok || !x.ort) return setMeldung({ art: "fehler", text: x.fehler ?? "Ort nicht gefunden." });
    setD(x);
  }, [id, vergangene]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- einmaliges Laden beim Öffnen
    laden();
  }, [laden]);

  async function ausfuehren(body: Record<string, unknown>, okText: string) {
    setLaeuft(true);
    const { ok, daten } = await senden(id, body);
    setLaeuft(false);
    if (!ok) {
      setMeldung({ art: "fehler", text: String(daten.fehler ?? "Hat nicht geklappt.") });
      return false;
    }
    if (typeof daten.weiter === "string") {
      window.location.assign(daten.weiter);
      return true;
    }
    setMeldung({ art: "ok", text: okText });
    laden();
    return true;
  }

  async function stammdatenSpeichern(ev: FormEvent<HTMLFormElement>) {
    ev.preventDefault();
    if (!d) return;
    const o = d.ort;
    const f = new FormData(ev.currentTarget);
    const norm = (w: unknown) => (w === null || w === undefined ? "" : String(w).trim());
    const felder: Record<string, unknown> = {};
    for (const t of FELDER) {
      if (t.feld === "beschreibung" && o.typ === "spielstaette") continue;
      if (CSV_FELDER[o.typ]?.felder.includes(t.feld)) continue; // kommt aus der CSV des Imports (gesperrt)
      const neu = String(f.get(t.feld) ?? "");
      if (norm(neu) !== norm(o[t.feld])) felder[t.feld] = neu;
    }
    // Geo nur zusammen
    if ("latitude" in felder || "longitude" in felder) {
      felder.latitude = String(f.get("latitude") ?? "");
      felder.longitude = String(f.get("longitude") ?? "");
    }
    if (!o.aktiv && f.get("aktiv") === "on") felder.aktiv = true;
    if (!Object.keys(felder).length) return setMeldung({ art: "ok", text: "Keine Änderung." });
    await ausfuehren({ felder }, "Gespeichert.");
  }

  async function scoreSpeichern(ev: FormEvent<HTMLFormElement>) {
    ev.preventDefault();
    const f = new FormData(ev.currentTarget);
    await ausfuehren({ aktion: "score", score: String(f.get("score") ?? "") || null, grund: String(f.get("grund") ?? "") }, "Score gespeichert.");
  }

  async function textSpeichern(ev: FormEvent<HTMLFormElement>) {
    ev.preventDefault();
    // Zwei Buttons im selben Formular: der auslösende sagt, ob freigegeben wird
    const freigeben = ((ev.nativeEvent as SubmitEvent).submitter as HTMLButtonElement | null)?.value === "freigeben";
    const f = new FormData(ev.currentTarget);
    if (freigeben && !window.confirm("Text freigeben? Er erscheint danach auf der Ortsseite.")) return;
    await ausfuehren(
      { aktion: "text", text: String(f.get("text") ?? ""), quellen: String(f.get("quellen") ?? ""), freigeben },
      freigeben ? "Text freigegeben – er steht jetzt auf der Ortsseite." : "Entwurf gespeichert.",
    );
  }

  async function zuordnungLoesen(e: EventZeile) {
    if (!window.confirm(`„${e.titel}“ von diesem Ort lösen? Die Pipeline ordnet das Event danach nicht wieder zu.`)) return;
    await ausfuehren({ aktion: "zuordnung_loesen", event: e.id }, "Zuordnung gelöst.");
  }

  async function zusammenlegen(ev: FormEvent<HTMLFormElement>) {
    ev.preventDefault();
    if (!d || !zielZusammen) return;
    const grund = String(new FormData(ev.currentTarget).get("grund") ?? "");
    if (!window.confirm(`„${d.ort.name}“ in „${zielZusammen.name}“ aufgehen lassen? Die Zeile wird gelöscht, /orte/${d.ort.slug} leitet weiter, Events ziehen um.`)) return;
    await ausfuehren({ aktion: "zusammenlegen", nach: zielZusammen.id, grund }, "Zusammengelegt.");
  }

  async function schliessen(ev: FormEvent<HTMLFormElement>) {
    ev.preventDefault();
    if (!d) return;
    const f = new FormData(ev.currentTarget);
    const loeschen = f.get("loeschen") === "on";
    const ziel = zielSchliessen ? `„${zielSchliessen.name}“` : "die Übersicht /orte";
    if (!window.confirm(`„${d.ort.name}“ ${loeschen ? "endgültig löschen" : "abschalten"}? Die alte Adresse leitet auf ${ziel} weiter.`)) return;
    await ausfuehren({ aktion: "schliessen", ziel: zielSchliessen?.id ?? null, grund: String(f.get("grund") ?? ""), loeschen }, "Abgeschaltet.");
  }

  if (!d) return meldung ? <p className="admin-fehler">{meldung.text}</p> : <p className="admin-unterzeile">Wird geladen …</p>;
  const o = d.ort;
  const istSpielstaette = o.typ === "spielstaette";
  const eigenerScore = o.typ !== "spielplatz" && o.typ !== "weihnachtsmarkt";
  const entwurf = o.spielstaette?.text_entwurf;
  const freigabe = o.spielstaette?.text_freigegeben;
  const schreibweisen = o.spielstaette?.event_orte ?? o.club?.event_orte ?? [];
  // Spielplätze und Weihnachtsmärkte: Freischalten und Löschen erst mit der Guide-Pflege (3b), Cursor 3a Befund 2
  const guideTyp = o.typ === "spielplatz" || o.typ === "weihnachtsmarkt";

  return (
    <>
      <p className="admin-unterzeile">
        <Link href="/admin/orte">← Orte</Link>
        {d.pfad && (
          <>
            {" · "}
            <a href={`https://diesdas.events${d.pfad}`} target="_blank" rel="noreferrer noopener">
              Live-Seite
            </a>
          </>
        )}
        {" · "}
        {TYP_TEXT.get(o.typ) ?? o.typ} · {o.slug} · {o.aktiv ? "aktiv" : "inaktiv"}
        {!d.pfad && o.aktiv && " · keine öffentliche Seite (Score unter der Schwelle oder ohne Hub)"}
      </p>
      <h1>{o.name}</h1>
      {meldung && <p className={meldung.art === "ok" ? "admin-karte" : "admin-fehler"} role="status">{meldung.text}</p>}

      {(d.haus || d.saele.length > 0 || d.weiterleitungen.length > 0 || d.eigeneWeiterleitung || schreibweisen.length > 0) && (
        <section className="admin-karte">
          <h2>Bezüge</h2>
          {d.haus && (
            <p>
              Saal von <Link href={`/admin/orte/${d.haus.id}`}>{d.haus.name}</Link>
            </p>
          )}
          {d.saele.length > 0 && (
            <p>
              Säle:{" "}
              {d.saele.map((s, i) => (
                <span key={s.id}>
                  {i > 0 && ", "}
                  <Link href={`/admin/orte/${s.id}`}>{s.name}</Link>
                  {!s.aktiv && " (inaktiv)"}
                </span>
              ))}
            </p>
          )}
          {d.weiterleitungen.length > 0 && <p>Alte Adressen, die hierher leiten: {d.weiterleitungen.map((w) => w.alter_slug).join(", ")}</p>}
          {d.eigeneWeiterleitung && (
            <p>
              Für /orte/{o.slug} gibt es eine Weiterleitung ({d.eigeneWeiterleitung.grund ?? "ohne Grund"}). Sie greift, solange dieser Ort inaktiv ist.
            </p>
          )}
          {schreibweisen.length > 0 && <p>Schreibweisen im Kalender (event_orte): {schreibweisen.join(" · ")}</p>}
        </section>
      )}

      <form className="admin-karte admin-formular" onSubmit={stammdatenSpeichern} key={`s-${o.aktualisiert_am}`}>
        <h2 className="admin-feld--breit">Stammdaten</h2>
        {FELDER.map((t) => {
          const csv = CSV_FELDER[o.typ]?.felder.includes(t.feld) ? CSV_FELDER[o.typ].quelle : null;
          const gesperrt = (t.feld === "beschreibung" && istSpielstaette) || !!csv;
          const wert = o[t.feld] === null || o[t.feld] === undefined ? "" : String(o[t.feld]);
          return (
            <label key={t.feld} className={`admin-feld${t.lang ? " admin-feld--breit" : ""}`}>
              <span>
                {t.text}
                {gesperrt && <small> · {csv ? `aus ${csv}` : "nur über „Text“ unten"}</small>}
              </span>
              {t.lang ? (
                <textarea name={t.feld} defaultValue={wert} rows={t.feld === "beschreibung" ? 8 : 3} disabled={gesperrt} />
              ) : (
                <input name={t.feld} defaultValue={wert} list={t.liste} disabled={gesperrt} />
              )}
            </label>
          );
        })}
        <datalist id="admin-stadtteile">
          {STADTTEILE.map((s) => (
            <option key={s} value={s} />
          ))}
        </datalist>
        {!o.aktiv && !guideTyp && (
          <fieldset className="admin-feld admin-feld--breit admin-schalter">
            <label>
              <input type="checkbox" name="aktiv" /> freischalten (aktiv)
            </label>
          </fieldset>
        )}
        {!o.aktiv && guideTyp && <p className="admin-feld--breit">Freischalten im Abschnitt „{o.typ === "spielplatz" ? "Spielplatz" : "Weihnachtsmarkt"}“ unten.</p>}
        <div className="admin-feld--breit">
          <button className="admin-knopf" type="submit" disabled={laeuft}>
            {laeuft ? "Speichert …" : "Stammdaten speichern"}
          </button>
        </div>
      </form>

      {eigenerScore && (
        <form className="admin-karte admin-formular" onSubmit={scoreSpeichern} key={`sc-${o.aktualisiert_am}`}>
          <h2 className="admin-feld--breit">Score</h2>
          <p className="admin-feld--breit">
            Sichtbar in den Guides ab 7. Mit Begründung bleibt der Score fest, auch wenn die Orte-Skripte neu rechnen.
            {o.google_rating !== null && ` Google: ${o.google_rating}.`}
          </p>
          <label className="admin-feld">
            Score (1–10, leer = keiner)
            <input name="score" type="number" min={1} max={10} defaultValue={o.qualitaets_score ?? ""} />
          </label>
          <label className="admin-feld admin-feld--breit">
            Begründung (leer = Score nicht fest)
            <input name="grund" defaultValue={typeof o.score_manuell === "string" ? o.score_manuell : ""} />
          </label>
          <div className="admin-feld--breit">
            <button className="admin-knopf" type="submit" disabled={laeuft}>
              Score speichern
            </button>
          </div>
        </form>
      )}

      {istSpielstaette && (
        <form className="admin-karte admin-formular" onSubmit={textSpeichern} key={`t-${o.aktualisiert_am}`}>
          <h2 className="admin-feld--breit">Text der Ortsseite</h2>
          <p className="admin-feld--breit">
            {freigabe ? `Live seit ${datumDe(freigabe.datum)} mit ${freigabe.quellen?.length ?? 0} Quellen.` : "Noch kein Text freigegeben – die Ortsseite zeigt keinen Text."}
            {entwurf && ` Entwurf vom ${datumDe(entwurf.datum)} unten.`} Jeder Satz braucht eine Quelle. Absätze per Leerzeile, **fett** zeigt die Ortsseite.
          </p>
          {freigabe && entwurf && (
            <details className="admin-feld--breit">
              <summary>Live-Fassung ansehen</summary>
              <p style={{ whiteSpace: "pre-wrap" }}>{o.beschreibung}</p>
            </details>
          )}
          <label className="admin-feld admin-feld--breit">
            {entwurf ? "Entwurf" : "Text"}
            <textarea name="text" rows={12} defaultValue={entwurf?.text ?? o.beschreibung ?? ""} />
          </label>
          <label className="admin-feld admin-feld--breit">
            Quellen (eine Adresse je Zeile, https://)
            <textarea name="quellen" rows={4} defaultValue={(entwurf?.quellen ?? freigabe?.quellen ?? []).join("\n")} />
          </label>
          <div className="admin-feld--breit admin-knopfreihe">
            <button className="admin-knopf admin-knopf--leise" type="submit" value="entwurf" disabled={laeuft}>
              Als Entwurf speichern
            </button>
            <button className="admin-knopf" type="submit" value="freigeben" disabled={laeuft}>
              Text freigeben
            </button>
          </div>
        </form>
      )}

      <BildAbschnitt o={o} ausfuehren={ausfuehren} laeuft={laeuft} />
      {CLUB_TYPEN.includes(o.typ) && <ClubAbschnitt o={o} ausfuehren={ausfuehren} laeuft={laeuft} />}
      {o.typ === "weihnachtsmarkt" && <WmAbschnitt o={o} ausfuehren={ausfuehren} laeuft={laeuft} />}
      {o.typ === "spielplatz" && <SpielplatzAbschnitt o={o} ausfuehren={ausfuehren} laeuft={laeuft} />}

      <section className="admin-karte">
        <h2>
          {d.vergangene ? "Alle zugeordneten Events" : "Kommende Events"} ({d.eventsGesamt})
        </h2>
        <p>
          <button type="button" className="admin-knopf admin-knopf--leise" onClick={() => setVergangene(!vergangene)}>
            {vergangene ? "nur kommende zeigen" : "auch vergangene zeigen"}
          </button>
        </p>
        {d.events.length === 0 ? (
          <p>Keine Events zugeordnet.</p>
        ) : (
          <ul className="admin-liste">
            {d.events.map((e) => (
              <li key={e.id} className="admin-liste__eintrag">
                <strong>
                  <Link href={`/admin/events/${e.id}`}>{e.titel}</Link>
                </strong>
                <span>
                  {datumDe(e.datum)}
                  {e.uhrzeit ? ` ${e.uhrzeit.slice(0, 5)}` : ""} · „{e.ort}“ · {e.quelle_name ?? "–"}
                  {e.abgesagt && " · abgesagt"}
                  {e.abgelehnt && " · abgelehnt"}
                </span>
                <button type="button" className="admin-knopf admin-knopf--leise" disabled={laeuft} onClick={() => zuordnungLoesen(e)}>
                  Zuordnung lösen
                </button>
              </li>
            ))}
          </ul>
        )}
        {d.eventsGesamt > d.events.length && (
          <p className="admin-unterzeile">
            Gezeigt: {d.vergangene ? `die neuesten ${d.events.length}` : `die nächsten ${d.events.length}`}.
          </p>
        )}
      </section>

      <section className="admin-karte">
        <h2>Zusammenlegen</h2>
        <p>
          Dieser Ort ist dasselbe Haus wie ein anderer: Er geht im anderen auf. Die Zeile wird gelöscht, /orte/{o.slug} leitet weiter, Events und Säle
          ziehen um. Ist das Ziel ein Club oder eine Spielstätte, kommen die Schreibweisen im Kalender und der Name dazu (nur dort ordnet die Pipeline
          über Schreibweisen zu).
        </p>
        {zielZusammen ? (
          <form onSubmit={zusammenlegen} className="admin-filterleiste">
            <p>
              Ziel: <strong>{zielZusammen.name}</strong> ({zielZusammen.slug}){" "}
              <button type="button" className="admin-knopf admin-knopf--leise" onClick={() => setZielZusammen(null)}>
                anderes Ziel
              </button>
            </p>
            <label className="admin-feld">
              Grund
              <input name="grund" required minLength={3} placeholder="z. B. gleiche Adresse, Probenhaus" />
            </label>
            <button className="admin-knopf" type="submit" disabled={laeuft}>
              Zusammenlegen
            </button>
          </form>
        ) : (
          <OrtSuche ohne={o.id} onWaehlen={setZielZusammen} knopf="Hierhin zusammenlegen" />
        )}
      </section>

      {o.aktiv && (
        <section className="admin-karte">
          <h2>Schließen oder löschen</h2>
          <p>
            Die alte Adresse leitet immer weiter: auf einen anderen Ort oder auf die Übersicht /orte. „Schließen“ behält die Zeile (später wieder
            freischaltbar), „Löschen“ entfernt sie.
          </p>
          {zielSchliessen ? (
            <p>
              Weiterleitung auf <strong>{zielSchliessen.name}</strong>{" "}
              <button type="button" className="admin-knopf admin-knopf--leise" onClick={() => setZielSchliessen(null)}>
                auf /orte statt dessen
              </button>
            </p>
          ) : (
            <details>
              <summary>Ziel-Ort wählen (sonst /orte)</summary>
              <OrtSuche ohne={o.id} onWaehlen={setZielSchliessen} knopf="Dorthin weiterleiten" />
            </details>
          )}
          <form onSubmit={schliessen} className="admin-filterleiste">
            <label className="admin-feld">
              Grund
              <input name="grund" required minLength={3} placeholder="z. B. dauerhaft geschlossen" />
            </label>
            {!guideTyp && (
              <label className="admin-schalter">
                <input type="checkbox" name="loeschen" /> Zeile löschen
              </label>
            )}
            <button className="admin-knopf" type="submit" disabled={laeuft}>
              Schließen
            </button>
          </form>
        </section>
      )}
    </>
  );
}
