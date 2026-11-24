"use client";
// Event-Meldungen von der Website prüfen, bearbeiten, freigeben oder ablehnen (Plan Admin-Dashboard 4.10, Stufe 5b;
// Umzug aus dashboard/meldungen.py). Nutzerangaben werden nur als Text gezeigt.
import Link from "next/link";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { MELDUNG_KATEGORIEN } from "@/lib/admin/meldungen";
import { STADTTEILE } from "@/lib/admin/orte";

interface Meldung {
  id: string;
  erstellt_am: string;
  titel: string;
  kategorie: string;
  datum: string;
  datum_bis: string | null;
  uhrzeit: string | null;
  ort: string;
  adresse: string | null;
  preis: string | null;
  beschreibung: string;
  link: string | null;
  bild_pfad: string | null;
  bild_rechte: boolean;
  bild_link: string | null;
  kontakt_name: string | null;
  kontakt_email: string;
  kontakt_rolle: string;
  anmerkung: string | null;
  stadtteil_vorschlag: string | null;
}

interface Erledigt {
  id: string;
  titel: string;
  datum: string;
  status: string;
  bearbeitet_am: string | null;
  ablehngrund: string | null;
  event_id: string | null;
  mail_status: "offen" | "gesendet" | "fehler" | "entfallen" | null;
  mail_gesendet_am: string | null;
}

/** Stand der Bestätigungsmail an den Melder (pipeline/meldung_mail.py); ältere Freigaben haben keinen */
function mailText(e: Erledigt): string {
  if (e.mail_status === "gesendet") return ` · Mail gesendet ${zeit(e.mail_gesendet_am)}`;
  if (e.mail_status === "offen") return " · Mail ausstehend";
  if (e.mail_status === "fehler") return " · Mail fehlgeschlagen";
  if (e.mail_status === "entfallen") return " · keine Mail (Event vorbei oder ausgeblendet)";
  return "";
}

function zeit(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString("de-DE", { timeZone: "Europe/Berlin", dateStyle: "short", timeStyle: "short" }) : "–";
}

function Karte({ m, nachher }: { m: Meldung; nachher: (text: string, art: "ok" | "fehler") => void }) {
  const [laeuft, setLaeuft] = useState(false);

  async function senden(body: Record<string, unknown>) {
    setLaeuft(true);
    const r = await fetch("/api/admin/meldungen", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const d = (await r.json().catch(() => ({}))) as { fehler?: string; warnung?: string; event_id?: string; mail_job?: boolean };
    setLaeuft(false);
    if (!r.ok) return nachher(d.fehler ?? "Hat nicht geklappt.", "fehler");
    const mail = d.mail_job === false
      ? "die Mail an den Melder kommt mit dem nächsten stündlichen Lauf (sofortiger Start hat nicht geklappt)."
      : "die Mail an den Melder ist unterwegs (sofern der Versand eingeschaltet ist).";
    nachher(d.warnung ?? (body.aktion === "freigeben" ? `Freigegeben – Event angelegt, ${mail}` : "Meldung abgelehnt."), d.warnung ? "fehler" : "ok");
  }

  function freigeben(ev: FormEvent<HTMLFormElement>) {
    ev.preventDefault();
    const f = new FormData(ev.currentTarget);
    const werte = Object.fromEntries(["titel", "kategorie", "datum", "datum_bis", "uhrzeit", "ort", "adresse", "stadtteil", "preis", "link", "beschreibung"].map((k) => [k, String(f.get(k) ?? "")]));
    if (window.confirm("Freigeben und veröffentlichen?")) senden({ aktion: "freigeben", id: m.id, werte });
  }

  function ablehnen() {
    const grund = window.prompt("Meldung ablehnen? Interner Grund (optional):");
    if (grund !== null) senden({ aktion: "ablehnen", id: m.id, grund });
  }

  return (
    <details className="admin-karte">
      <summary>
        <strong>{m.datum}</strong> · {m.titel} <small>– eingereicht {zeit(m.erstellt_am)}</small>
      </summary>
      <div className="admin-meldung">
        <form className="admin-formular" onSubmit={freigeben}>
          <label className="admin-feld admin-feld--breit">
            Titel
            <input name="titel" defaultValue={m.titel} maxLength={150} required />
          </label>
          <label className="admin-feld">
            Kategorie
            <select name="kategorie" defaultValue={m.kategorie}>
              {MELDUNG_KATEGORIEN.map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
          </label>
          <label className="admin-feld">
            Datum
            <input name="datum" type="date" defaultValue={m.datum} required />
          </label>
          <label className="admin-feld">
            bis (optional)
            <input name="datum_bis" type="date" defaultValue={m.datum_bis ?? ""} />
          </label>
          <label className="admin-feld">
            Uhrzeit (optional)
            <input name="uhrzeit" type="time" defaultValue={m.uhrzeit?.slice(0, 5) ?? ""} />
          </label>
          <label className="admin-feld">
            Ort
            <input name="ort" defaultValue={m.ort} maxLength={150} required />
          </label>
          <label className="admin-feld">
            Adresse
            <input name="adresse" defaultValue={m.adresse ?? ""} maxLength={200} />
          </label>
          <label className="admin-feld">
            Stadtteil {m.stadtteil_vorschlag && <small>(Vorschlag aus der PLZ)</small>}
            <input name="stadtteil" defaultValue={m.stadtteil_vorschlag ?? ""} list="admin-stadtteile-meldung" maxLength={60} />
          </label>
          <label className="admin-feld">
            Preis
            <input name="preis" defaultValue={m.preis ?? ""} maxLength={80} />
          </label>
          <label className="admin-feld admin-feld--breit">
            Link
            <input name="link" defaultValue={m.link ?? ""} maxLength={500} />
          </label>
          <label className="admin-feld admin-feld--breit">
            Beschreibung (wird auf 300 Zeichen gekürzt)
            <textarea name="beschreibung" defaultValue={m.beschreibung} rows={6} />
          </label>
          <div className="admin-feld--breit admin-knopfreihe">
            <button className="admin-knopf" type="submit" disabled={laeuft}>
              Freigeben & veröffentlichen
            </button>
            <button className="admin-knopf admin-knopf--leise" type="button" disabled={laeuft} onClick={ablehnen}>
              Ablehnen
            </button>
          </div>
        </form>
        <aside>
          {m.bild_link ? (
            <>
              {/* eslint-disable-next-line @next/next/no-img-element -- signierter Link, nur Vorschau */}
              <img src={m.bild_link} alt="Eingereichtes Bild" className="admin-bild-vorschau" />
              <p className="admin-unterzeile">{m.bild_rechte ? "Bildrechte bestätigt" : "Bildrechte NICHT bestätigt – Bild wird nicht übernommen"}</p>
            </>
          ) : (
            <p className="admin-unterzeile">Kein Bild.</p>
          )}
          <p>
            Kontakt: {m.kontakt_name || "–"} · {m.kontakt_email} · {m.kontakt_rolle === "veranstalter" ? "Veranstalter" : "Tipp von Besucher"}
          </p>
          {m.anmerkung && <p>Anmerkung: {m.anmerkung}</p>}
        </aside>
      </div>
    </details>
  );
}

export function MeldungenListe() {
  const [offen, setOffen] = useState<Meldung[] | null>(null);
  const [erledigt, setErledigt] = useState<Erledigt[]>([]);
  const [meldung, setMeldung] = useState<{ text: string; art: "ok" | "fehler" } | null>(null);

  const laden = useCallback(async () => {
    const r = await fetch("/api/admin/meldungen", { cache: "no-store" });
    if (r.status === 401) return window.location.assign("/admin/anmelden");
    const d = (await r.json().catch(() => ({}))) as { offen?: Meldung[]; erledigt?: Erledigt[]; fehler?: string };
    if (!r.ok) return setMeldung({ text: d.fehler ?? "Meldungen nicht ladbar.", art: "fehler" });
    setOffen(d.offen ?? []);
    setErledigt(d.erledigt ?? []);
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- einmaliges Laden
    laden();
  }, [laden]);

  return (
    <>
      <h1>Meldungen</h1>
      <p className="admin-unterzeile">Über „Event melden“ eingereichte Events. Freigeben legt das Event an (Bild nur mit bestätigten Rechten), ablehnen löscht das Bild.</p>
      {meldung && <p className={meldung.art === "ok" ? "admin-karte" : "admin-fehler"} role="status">{meldung.text}</p>}
      <datalist id="admin-stadtteile-meldung">
        {STADTTEILE.map((s) => (
          <option key={s} value={s} />
        ))}
      </datalist>
      {offen?.length === 0 && <p className="admin-karte">Keine offenen Meldungen.</p>}
      {offen?.map((m) => (
        <Karte
          key={m.id}
          m={m}
          nachher={(text, art) => {
            setMeldung({ text, art });
            laden();
          }}
        />
      ))}
      {erledigt.length > 0 && (
        <section className="admin-karte">
          <h2>Zuletzt bearbeitet</h2>
          <ul className="admin-liste">
            {erledigt.map((e) => (
              <li key={e.id} className="admin-liste__eintrag">
                <strong>{e.titel}</strong>
                <span>
                  {e.datum} · {e.status} · {zeit(e.bearbeitet_am)}
                  {e.ablehngrund ? ` · ${e.ablehngrund}` : ""}
                  {mailText(e)}
                </span>
                {e.event_id && <Link href={`/admin/events/${e.event_id}`}>Event</Link>}
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
