"use client";
// Abschnitte der Ort-Bearbeitung für Stufe 3b (Plan Admin-Dashboard 4.7): Bild (Google-Kandidaten auf Knopfdruck,
// eigene Dateien, Bildausschnitt per Klick), Club-Hub, Weihnachtsmarkt, Spielplatz. Geschrieben wird über
// /api/admin/orte/[id] → Funktionen in database/admin_guides_2026-11-23.sql.
import { useState, type FormEvent, type MouseEvent } from "react";
import {
  clubStand,
  codeBestaetigbar,
  fokusAusKlick,
  PRUEF_CODE_TEXT,
  spielplatzFreischaltbar,
  spielplatzSperren,
  wmFreischaltbar,
  wmHatSaison,
  type GoogleFoto,
  type SpielplatzStand,
  type WmStand,
} from "@/lib/admin/guides";

export interface GuideOrt {
  id: string;
  slug: string;
  typ: string;
  aktiv: boolean | null;
  qualitaets_score: number | null;
  bild_url: string | null;
  bild_attribution: string | null;
  google_place_id: string | null;
  google_foto: { name?: string; autor?: string | null } | null;
  bild_fokus: string | null;
  bild_link: string | null;
  foto_manuell: string | null;
  club: unknown;
  club_score: unknown;
  club_freigegeben: unknown;
  auch_club: unknown;
  kein_club: unknown;
  vorher_typ: string | null;
  weihnachtsmarkt: WmStand | null;
  spielplatz: (SpielplatzStand & { redaktion?: string[] | null }) | null;
}

export type Ausfuehren = (body: Record<string, unknown>, okText: string) => Promise<boolean>;

const fotoVorschau = (name: string) => `/api/admin/orte/foto?name=${encodeURIComponent(name)}`;

/** Aktuelles Bild für die Vorschau im Admin (eigene Datei direkt, Google über die Admin-Route) */
function aktuellesBild(o: GuideOrt): string | null {
  if (o.bild_url?.startsWith("/ort-bilder/")) return o.bild_url;
  if (o.bild_url && /^https:\/\//.test(o.bild_url)) return null; // fremde Adresse: nur als Link
  return o.google_foto?.name ? fotoVorschau(o.google_foto.name) : null;
}

function fokusLage(f: string | null): string {
  if (f === "oben") return "center top";
  if (f === "unten") return "center bottom";
  return f && /^\d{1,3}%$/.test(f) ? `center ${f}` : "center";
}

export function BildAbschnitt({ o, ausfuehren, laeuft }: { o: GuideOrt; ausfuehren: Ausfuehren; laeuft: boolean }) {
  const [kandidaten, setKandidaten] = useState<GoogleFoto[] | null>(null);
  const [eigene, setEigene] = useState<string[] | null>(null);
  const [hinweis, setHinweis] = useState<string | null>(null);
  const bild = aktuellesBild(o);
  const googleErlaubt = o.typ !== "spielstaette" && !!o.google_place_id;
  const personenHinweis =
    o.typ === "spielplatz" ? "Nur Fotos ohne erkennbare Personen (Kinder!)." : o.typ === "weihnachtsmarkt" ? "Nur Fotos ohne erkennbare Gesichter (W4)." : null;

  async function googleLaden() {
    setHinweis(null);
    const r = await fetch(`/api/admin/orte/${o.id}/google-fotos`, { cache: "no-store" });
    const d = (await r.json().catch(() => ({}))) as { fotos?: GoogleFoto[]; fehler?: string };
    if (!r.ok) return setHinweis(d.fehler ?? "Google-Fotos nicht ladbar.");
    setKandidaten(d.fotos ?? []);
  }

  async function eigeneLaden() {
    const ordner = o.typ === "weihnachtsmarkt" ? "weihnachtsmaerkte" : o.typ === "spielstaette" ? "orte" : "";
    const r = await fetch(`/api/admin/orte/eigene-bilder${ordner ? `?ordner=${ordner}` : ""}`, { cache: "no-store" });
    const d = (await r.json().catch(() => ({}))) as { bilder?: string[] };
    setEigene(d.bilder ?? []);
  }

  async function fokusKlick(e: MouseEvent<HTMLImageElement>) {
    const r = e.currentTarget.getBoundingClientRect();
    const fokus = fokusAusKlick(e.clientY - r.top, r.height);
    await ausfuehren({ aktion: "bild_fokus", fokus }, `Bildausschnitt auf ${fokus} gesetzt.`);
  }

  async function eigenesWaehlen(ev: FormEvent<HTMLFormElement>) {
    ev.preventDefault();
    const f = new FormData(ev.currentTarget);
    await ausfuehren(
      { aktion: "bild", bild: { art: "eigen", bild_url: String(f.get("bild_url") ?? ""), bild_attribution: String(f.get("nachweis") ?? ""), bild_link: String(f.get("link") ?? "") } },
      "Eigenes Bild gesetzt.",
    );
  }

  return (
    <section className="admin-karte">
      <h2>Bild</h2>
      <p>
        {o.bild_url ? `Eigenes Bild: ${o.bild_url}` : o.google_foto?.name ? `Google-Foto${o.bild_attribution ? ` von ${o.bild_attribution}` : ""}` : "Kein Bild."}
        {o.foto_manuell && ` · von Hand gewählt am ${o.foto_manuell.split("-").reverse().join(".")}`}
        {o.bild_url && o.bild_attribution && ` · Nachweis: ${o.bild_attribution}`}
      </p>
      {bild && (
        <>
          {/* eslint-disable-next-line @next/next/no-img-element -- Admin-Vorschau, kein Bild-Optimierer */}
          <img
            src={bild}
            alt="Aktuelles Bild"
            onClick={fokusKlick}
            className="admin-bild-vorschau"
            style={{ objectPosition: fokusLage(o.bild_fokus) }}
            title="Klicken: diese Höhe bleibt im Ausschnitt sichtbar"
          />
          <p className="admin-unterzeile">
            Ausschnitt: {o.bild_fokus ?? "Mitte"} – ins Bild klicken, um die sichtbare Höhe zu setzen.{" "}
            {o.bild_fokus && (
              <button type="button" className="admin-knopf admin-knopf--leise" disabled={laeuft} onClick={() => ausfuehren({ aktion: "bild_fokus", fokus: null }, "Ausschnitt zurückgesetzt.")}>
                Mitte
              </button>
            )}
          </p>
        </>
      )}
      {personenHinweis && <p className="admin-unterzeile">{personenHinweis}</p>}
      {hinweis && <p className="admin-fehler">{hinweis}</p>}

      <div className="admin-knopfreihe">
        {googleErlaubt && (
          <button type="button" className="admin-knopf admin-knopf--leise" onClick={googleLaden} disabled={laeuft}>
            Google-Fotos laden (kostet je Ort ca. 2–9 Cent)
          </button>
        )}
        <button type="button" className="admin-knopf admin-knopf--leise" onClick={eigeneLaden} disabled={laeuft}>
          Eigene Bilder zeigen
        </button>
        {(o.bild_url || o.google_foto?.name) && (
          <button
            type="button"
            className="admin-knopf admin-knopf--leise"
            disabled={laeuft}
            onClick={() => window.confirm("Bild entfernen? Die Seite zeigt dann das Symbolbild.") && ausfuehren({ aktion: "bild", bild: { art: "keins" } }, "Bild entfernt.")}
          >
            Kein Bild
          </button>
        )}
      </div>
      {!googleErlaubt && o.typ !== "spielstaette" && <p className="admin-unterzeile">Kein Google-Eintrag hinterlegt – nur eigene Bilder.</p>}

      {kandidaten && (
        <div className="admin-bild-raster">
          {kandidaten.length === 0 && <p>Google hat keine Fotos zu diesem Ort.</p>}
          {kandidaten.map((k) => (
            <figure key={k.name}>
              {/* eslint-disable-next-line @next/next/no-img-element -- Vorschau über die Admin-Route */}
              <img src={fotoVorschau(k.name)} alt={`Foto von ${k.autor ?? "Google"}`} loading="lazy" />
              <figcaption>
                {k.autor ?? "Google"} {k.breite && k.hoehe ? `· ${k.breite}×${k.hoehe}` : ""}
                <button
                  type="button"
                  className="admin-knopf admin-knopf--leise"
                  disabled={laeuft}
                  onClick={() => ausfuehren({ aktion: "bild", bild: { art: "google", google_foto: k } }, `Foto von ${k.autor ?? "Google"} gesetzt.`)}
                >
                  Dieses nehmen
                </button>
              </figcaption>
            </figure>
          ))}
        </div>
      )}

      {eigene && (
        <form onSubmit={eigenesWaehlen} className="admin-formular">
          <label className="admin-feld admin-feld--breit">
            Datei ({eigene.length} unter /ort-bilder{o.typ === "weihnachtsmarkt" ? "/weihnachtsmaerkte" : o.typ === "spielstaette" ? "/orte" : ""})
            <select name="bild_url" defaultValue={o.bild_url ?? ""} required>
              <option value="">– wählen –</option>
              {eigene.map((p) => (
                <option key={p} value={p}>
                  {p.replace("/ort-bilder/", "")}
                </option>
              ))}
            </select>
          </label>
          <label className="admin-feld">
            Nachweis (leer = eigenes Foto)
            <input name="nachweis" defaultValue={o.bild_url ? (o.bild_attribution ?? "") : ""} />
          </label>
          <label className="admin-feld">
            Link zum Nachweis (https)
            <input name="link" defaultValue={o.bild_link ?? ""} />
          </label>
          <div className="admin-feld--breit">
            <button className="admin-knopf" type="submit" disabled={laeuft}>
              Eigenes Bild setzen
            </button>
          </div>
          <p className="admin-feld--breit admin-unterzeile">Neue eigene Bilder kommen weiter als Datei ins Repo (Deploy), z. B. über scraper/orte/ortsbilder.py.</p>
        </form>
      )}
    </section>
  );
}

export function ClubAbschnitt({ o, ausfuehren, laeuft }: { o: GuideOrt; ausfuehren: Ausfuehren; laeuft: boolean }) {
  const s = clubStand(o);
  const [grund, setGrund] = useState("");
  return (
    <section className="admin-karte">
      <h2>Club-Hub</h2>
      <p>
        {s.imHub ? "Im Club-Hub" : "Nicht im Club-Hub"}
        {o.kein_club ? ` (herausgenommen: ${String(o.kein_club)})` : ""} · Club-Profil {s.profil ? "vorhanden" : "fehlt"} · Club-Score{" "}
        {s.score ?? "–"} · {s.freigegeben ? `Top-Empfehlung seit ${String(o.club_freigegeben)}` : "keine Top-Empfehlung"}
        {o.vorher_typ ? ` · früher Typ „${o.vorher_typ}“` : ""}
      </p>
      {s.imHub && !s.profil && <p className="admin-unterzeile">Sichtbar wird ein Ort im Club-Hub erst mit Profil und Score (scraper/orte/clubs_profil.py).</p>}
      <div className="admin-knopfreihe">
        {s.imHub && s.profil && !s.freigegeben && (
          <button type="button" className="admin-knopf admin-knopf--leise" disabled={laeuft} onClick={() => ausfuehren({ aktion: "club", club: "freigeben" }, "Als Top-Empfehlung freigegeben.")}>
            Als Top-Empfehlung freigeben
          </button>
        )}
        {s.freigegeben && (
          <button type="button" className="admin-knopf admin-knopf--leise" disabled={laeuft} onClick={() => ausfuehren({ aktion: "club", club: "freigabe_entziehen" }, "Top-Empfehlung entzogen.")}>
            Top-Empfehlung entziehen
          </button>
        )}
        {!s.imHub && (
          <button type="button" className="admin-knopf admin-knopf--leise" disabled={laeuft} onClick={() => ausfuehren({ aktion: "club", club: "in_hub" }, "In den Club-Hub aufgenommen.")}>
            In den Club-Hub aufnehmen
          </button>
        )}
      </div>
      {s.imHub && (
        <form
          className="admin-filterleiste"
          onSubmit={(e) => {
            e.preventDefault();
            const text =
              o.typ === "club"
                ? "Aus dem Club-Hub nehmen? Der Ort wird zur Bar (Typ kneipe). Die alte Club-Adresse leitet auf den Bar-Hub, sobald der Score dort mindestens 7 ist – sonst endet sie als 404."
                : "Aus dem Club-Hub nehmen? Die Club-Adresse leitet dann auf die Hauptseite des Ortes, wenn sie sichtbar ist.";
            if (window.confirm(text)) ausfuehren({ aktion: "club", club: "aus_hub", grund }, "Aus dem Club-Hub genommen.");
          }}
        >
          <label className="admin-feld">
            Grund (aus dem Club-Hub nehmen)
            <input value={grund} onChange={(e) => setGrund(e.target.value)} required minLength={3} placeholder="z. B. Bar mit DJ-Abenden, kein Club" />
          </label>
          <button className="admin-knopf" type="submit" disabled={laeuft}>
            {o.typ === "club" ? "Zur Bar machen" : "Aus dem Club-Hub nehmen"}
          </button>
        </form>
      )}
      {o.typ === "club" && s.imHub && (o.qualitaets_score ?? 0) < 7 && (
        <p className="admin-unterzeile">Vorher den Score (oben) auf mindestens 7 setzen, damit die Bar-Seite sichtbar ist.</p>
      )}
    </section>
  );
}

export function WmAbschnitt({ o, ausfuehren, laeuft }: { o: GuideOrt; ausfuehren: Ausfuehren; laeuft: boolean }) {
  const wm = o.weihnachtsmarkt ?? {};
  const [grund, setGrund] = useState("");
  return (
    <section className="admin-karte">
      <h2>Weihnachtsmarkt</h2>
      <p>
        {o.aktiv ? "Freigeschaltet" : "Nicht sichtbar"}
        {wm.freigeschaltet_am ? ` (erstmals ${wm.freigeschaltet_am.split("-").reverse().join(".")})` : ""} · Saison mit Zeiten:{" "}
        {wmHatSaison(wm) ? "ja" : "nein"}
        {wm.ausgeschlossen ? ` · ausgeschlossen: ${wm.ausgeschlossen}` : ""}
      </p>
      <form
        className="admin-filterleiste"
        onSubmit={(e) => {
          e.preventDefault();
          const rang = String(new FormData(e.currentTarget).get("rang") ?? "");
          ausfuehren({ aktion: "wm", wm: "rang", wert: rang }, rang ? `Top-5-Rang ${rang} gesetzt (ein anderer Markt mit diesem Rang verliert ihn).` : "Top-5-Rang entfernt.");
        }}
        key={`rang-${wm.top5_rang ?? ""}`}
      >
        <label className="admin-feld">
          Top-5-Rang
          <select name="rang" defaultValue={wm.top5_rang ? String(wm.top5_rang) : ""}>
            <option value="">kein Rang</option>
            {[1, 2, 3, 4, 5].map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </label>
        <button className="admin-knopf admin-knopf--leise" type="submit" disabled={laeuft}>
          Rang speichern
        </button>
      </form>
      <div className="admin-knopfreihe">
        {wmFreischaltbar(!!o.aktiv, wm) && (
          <button type="button" className="admin-knopf" disabled={laeuft} onClick={() => ausfuehren({ aktion: "wm", wm: "freischalten" }, "Markt freigeschaltet.")}>
            Freischalten
          </button>
        )}
        {wm.ausgeschlossen && (
          <button type="button" className="admin-knopf admin-knopf--leise" disabled={laeuft} onClick={() => ausfuehren({ aktion: "wm", wm: "einschliessen" }, "Ausschluss aufgehoben.")}>
            Ausschluss aufheben
          </button>
        )}
      </div>
      {!o.aktiv && !wm.ausgeschlossen && !wmHatSaison(wm) && (
        <p className="admin-unterzeile">Freischalten geht erst mit Saison (Zeitraum und Zeiten) aus data/weihnachtsmaerkte/saison-2026.csv und Import.</p>
      )}
      {!wm.ausgeschlossen && (
        <form
          className="admin-filterleiste"
          onSubmit={(e) => {
            e.preventDefault();
            if (window.confirm("Markt ausschließen? Er verschwindet aus dem Guide; die Adresse leitet auf den Hub (wenn er schon einmal freigeschaltet war)."))
              ausfuehren({ aktion: "wm", wm: "ausschliessen", wert: grund }, "Markt ausgeschlossen.");
          }}
        >
          <label className="admin-feld">
            Grund (ausschließen)
            <input value={grund} onChange={(e) => setGrund(e.target.value)} required minLength={3} placeholder="z. B. findet 2026 nicht statt" />
          </label>
          <button className="admin-knopf admin-knopf--leise" type="submit" disabled={laeuft}>
            Ausschließen
          </button>
        </form>
      )}
      <p className="admin-unterzeile">Saisonzeiten und Ruhetage bleiben in den CSV-Dateien (Import). Rang und Ausschluss gelten ab jetzt aus dem Dashboard.</p>
    </section>
  );
}

export function SpielplatzAbschnitt({ o, ausfuehren, laeuft }: { o: GuideOrt; ausfuehren: Ausfuehren; laeuft: boolean }) {
  const sp = o.spielplatz ?? {};
  const [grund, setGrund] = useState("");
  const sperren = spielplatzSperren(sp);
  const bestaetigt = new Set(sp.bestaetigt ?? []);
  return (
    <section className="admin-karte">
      <h2>Spielplatz</h2>
      <p>
        {o.aktiv ? "Freigeschaltet" : "Nicht sichtbar"}
        {sp.freigeschaltet_am ? ` (erstmals ${sp.freigeschaltet_am.split("-").reverse().join(".")})` : ""}
        {sp.ausgeschlossen ? ` · ausgeschlossen: ${sp.ausgeschlossen}` : ""}
        {sperren.length > 0 && ` · gesperrt durch: ${sperren.map((c) => PRUEF_CODE_TEXT[c] ?? c).join(", ")}`}
      </p>
      {(sp.pruefung ?? []).length > 0 && (
        <ul className="admin-liste">
          {(sp.pruefung ?? []).map((c) => (
            <li key={c} className="admin-liste__eintrag">
              <strong>{PRUEF_CODE_TEXT[c] ?? c}</strong>
              <span>{bestaetigt.has(c) ? "bestätigt" : codeBestaetigbar(c) ? "offen" : "sperrt immer – Korrektur über korrekturen.csv"}</span>
              {codeBestaetigbar(c) && (
                <button
                  type="button"
                  className="admin-knopf admin-knopf--leise"
                  disabled={laeuft}
                  onClick={() =>
                    ausfuehren(
                      { aktion: "spielplatz", spielplatz: bestaetigt.has(c) ? "bestaetigung_entziehen" : "bestaetigen", wert: c },
                      bestaetigt.has(c) ? "Bestätigung entzogen." : "Code bestätigt.",
                    )
                  }
                >
                  {bestaetigt.has(c) ? "Bestätigung entziehen" : "Bestätigen"}
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
      <div className="admin-knopfreihe">
        {spielplatzFreischaltbar(!!o.aktiv, sp) && (
          <button type="button" className="admin-knopf" disabled={laeuft} onClick={() => ausfuehren({ aktion: "spielplatz", spielplatz: "freischalten" }, "Spielplatz freigeschaltet.")}>
            Freischalten
          </button>
        )}
        {sp.ausgeschlossen && (
          <button type="button" className="admin-knopf admin-knopf--leise" disabled={laeuft} onClick={() => ausfuehren({ aktion: "spielplatz", spielplatz: "einschliessen" }, "Ausschluss aufgehoben.")}>
            Ausschluss aufheben
          </button>
        )}
      </div>
      {!sp.ausgeschlossen && (
        <form
          className="admin-filterleiste"
          onSubmit={(e) => {
            e.preventDefault();
            if (window.confirm("Spielplatz ausschließen? Er verschwindet aus dem Guide; die Adresse leitet auf die Stadtteilseite (wenn er schon einmal freigeschaltet war)."))
              ausfuehren({ aktion: "spielplatz", spielplatz: "ausschliessen", wert: grund }, "Spielplatz ausgeschlossen.");
          }}
        >
          <label className="admin-feld">
            Grund (ausschließen)
            <input value={grund} onChange={(e) => setGrund(e.target.value)} required minLength={3} placeholder="z. B. Schulhof, nicht öffentlich" />
          </label>
          <button className="admin-knopf admin-knopf--leise" type="submit" disabled={laeuft}>
            Ausschließen
          </button>
        </form>
      )}
      <p className="admin-unterzeile">
        Bestätigungen und Ausschluss gelten ab jetzt aus dem Dashboard (die Importe lassen sie stehen). Name und Stadtteil kommen weiter aus
        data/spielplaetze/korrekturen.csv.
      </p>
    </section>
  );
}
