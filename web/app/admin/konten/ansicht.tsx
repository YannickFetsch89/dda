"use client";
// Konten in Zahlen und Sensibel-Treffer (Plan Admin-Dashboard 4.10, Stufe 5a). Nur Zahlen, nie Personen, keine Suche.
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

interface Zahlen {
  konten: number;
  onboarding_fertig: number;
  aktiv_30_tage: number;
  unter16_gesperrt: number;
  neu_je_woche: { woche: string; anzahl: number }[];
  einwilligungen: { personalisierung: number; sensible_events: number; analyse: number; geburtstagsmail: number };
  interessen: { wert: string; anzahl: number }[];
  interessen_ausgeblendet: number;
  merkliste: { konten_mit_eintraegen: number; eintraege: number };
  geburtstagsmails_dieses_jahr: number;
}

interface Treffer {
  event_id: string;
  grund: string;
  quelle: string;
  gesetzt_am: string;
  titel: string;
  datum: string;
  ort: string | null;
  abgelehnt: boolean;
  gemerkt: number;
}

interface Ausnahme {
  event_id: string;
  notiz: string | null;
  gesetzt_am: string;
  titel: string;
  datum: string;
}

const GRUND: Record<string, string> = {
  gesundheit: "Gesundheit",
  religion: "Religion",
  sexualitaet: "Sexualität",
  politik: "Politik",
  gewerkschaft: "Gewerkschaft",
  herkunft: "Herkunft",
};

function datum(iso: string): string {
  return iso.slice(0, 10).split("-").reverse().join(".");
}

export function KontenAnsicht() {
  const [tage, setTage] = useState(30);
  const [z, setZ] = useState<Zahlen | null>(null);
  const [treffer, setTreffer] = useState<Treffer[]>([]);
  const [ausnahmen, setAusnahmen] = useState<Ausnahme[]>([]);
  const [fehler, setFehler] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);

  const laden = useCallback(async () => {
    const r = await fetch(`/api/admin/konten?tage=${tage}`, { cache: "no-store" });
    if (r.status === 401) return window.location.assign("/admin/anmelden");
    const d = (await r.json().catch(() => ({}))) as { zahlen?: Zahlen; sensibel?: { treffer: Treffer[]; ausnahmen: Ausnahme[] }; fehler?: string };
    if (!r.ok) return setFehler(d.fehler ?? "Zahlen nicht ladbar.");
    setZ(d.zahlen ?? null);
    setTreffer(d.sensibel?.treffer ?? []);
    setAusnahmen(d.sensibel?.ausnahmen ?? []);
    setFehler(null);
  }, [tage]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- Laden beim Öffnen und bei anderem Zeitraum
    laden();
  }, [laden]);

  async function senden(body: Record<string, unknown>) {
    setLaeuft(true);
    const r = await fetch("/api/admin/konten", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const d = (await r.json().catch(() => ({}))) as { fehler?: string };
    setLaeuft(false);
    if (!r.ok) return setFehler(d.fehler ?? "Hat nicht geklappt.");
    laden();
  }

  function alsFehltreffer(t: Treffer) {
    const notiz = window.prompt(`„${t.titel}“ ist kein sensibles Event? Kurz begründen (z. B. Theaterstück, Film):`);
    if (notiz) senden({ aktion: "ausnahme", event: t.event_id, notiz });
  }

  return (
    <>
      <h1>Konten</h1>
      <p className="admin-unterzeile">Nur Zahlen, nie einzelne Personen. Löschung und Auskunft bleiben im Supabase-Dashboard.</p>
      {fehler && <p className="admin-fehler" role="alert">{fehler}</p>}
      {z && (
        <>
          <div className="admin-kacheln">
            <div className="admin-karte"><strong>{z.konten}</strong> Konten</div>
            <div className="admin-karte"><strong>{z.onboarding_fertig}</strong> Profil fertig</div>
            <div className="admin-karte"><strong>{z.aktiv_30_tage}</strong> aktiv in 30 Tagen</div>
            <div className="admin-karte"><strong>{z.merkliste.konten_mit_eintraegen}</strong> mit Merkliste ({z.merkliste.eintraege} Einträge)</div>
            <div className="admin-karte"><strong>{z.geburtstagsmails_dieses_jahr}</strong> Geburtstagsmails dieses Jahr</div>
            <div className="admin-karte"><strong>{z.unter16_gesperrt}</strong> unter 16 gesperrt</div>
          </div>
          <section className="admin-karte">
            <h2>Einwilligungen</h2>
            <p>
              Personalisierung {z.einwilligungen.personalisierung} · sensible Events {z.einwilligungen.sensible_events} · Analyse{" "}
              {z.einwilligungen.analyse} · Geburtstagsmail {z.einwilligungen.geburtstagsmail}
            </p>
            <h2>Neue Konten je Woche</h2>
            <p>{z.neu_je_woche.length ? z.neu_je_woche.map((w) => `ab ${datum(w.woche)}: ${w.anzahl}`).join(" · ") : "keine in den letzten 8 Wochen"}</p>
            <h2>Interessen (Kategorien)</h2>
            <p>
              {z.interessen.length ? z.interessen.map((i) => `${i.wert}: ${i.anzahl}`).join(" · ") : "noch keine mit mindestens 3 Konten"}
              {z.interessen_ausgeblendet > 0 && ` · ${z.interessen_ausgeblendet} weitere mit weniger als 3 Konten ausgeblendet`}
            </p>
          </section>
        </>
      )}

      <section className="admin-karte">
        <h2>Sensible Events</h2>
        <p>
          Kennzeichnungen der letzten{" "}
          <select value={tage} onChange={(e) => setTage(Number(e.target.value))} aria-label="Zeitraum">
            {[7, 30, 90, 365].map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>{" "}
          Tage. Gekennzeichnete Events landen nur mit Einwilligung (b) in der Merkliste eines Kontos. Ein Fehltreffer (Stichwort nur in der
          Inhaltsbeschreibung eines Stücks, Films, Konzerts) wird zur Ausnahme – im Zweifel bleibt ein Treffer sensibel.
        </p>
        <ul className="admin-liste">
          {treffer.length === 0 && <li className="admin-liste__eintrag">Keine Kennzeichnungen in diesem Zeitraum.</li>}
          {treffer.map((t) => (
            <li key={t.event_id} className="admin-liste__eintrag">
              <strong>
                <Link href={`/admin/events/${t.event_id}`}>{t.titel}</Link>
              </strong>
              <span>
                {datum(t.datum)} · {t.ort ?? "–"} · {GRUND[t.grund] ?? t.grund} ({t.quelle}) · gekennzeichnet {datum(t.gesetzt_am)}
                {t.gemerkt ? ` · ${t.gemerkt}× gemerkt` : ""}
                {t.abgelehnt ? " · abgelehnt" : ""}
              </span>
              <button type="button" className="admin-knopf admin-knopf--leise" disabled={laeuft} onClick={() => alsFehltreffer(t)}>
                Fehltreffer
              </button>
            </li>
          ))}
        </ul>
        {ausnahmen.length > 0 && (
          <>
            <h2>Ausnahmen in diesem Zeitraum</h2>
            <ul className="admin-liste">
              {ausnahmen.map((a) => (
                <li key={a.event_id} className="admin-liste__eintrag">
                  <strong>
                    <Link href={`/admin/events/${a.event_id}`}>{a.titel}</Link>
                  </strong>
                  <span>
                    {datum(a.datum)} · {a.notiz ?? "–"}
                  </span>
                  <button
                    type="button"
                    className="admin-knopf admin-knopf--leise"
                    disabled={laeuft}
                    onClick={() => window.confirm("Ausnahme aufheben? Die Regeln prüfen das Event dann neu.") && senden({ aktion: "aufheben", event: a.event_id })}
                  >
                    Ausnahme aufheben
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>
    </>
  );
}
