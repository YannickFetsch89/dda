"use client";
import { useEffect, useState, type FormEvent } from "react";

type Start =
  | { art: "code"; faktorId: string }
  | { art: "einrichten"; faktorId: string; qr: string; geheimnis: string };

const KOPF = { "Content-Type": "application/json" };

export function ZweiFaktor() {
  const [start, setStart] = useState<Start | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);

  useEffect(() => {
    fetch("/api/admin/zwei-faktor/start", { method: "POST", headers: KOPF, body: "{}" })
      .then(async (r) => {
        if (r.status === 401 || r.status === 403) return window.location.assign("/admin/anmelden");
        const daten = (await r.json().catch(() => ({}))) as Start & { fehler?: string };
        if (r.ok && (daten.art === "code" || daten.art === "einrichten")) setStart(daten);
        else setFehler(daten.fehler ?? "Zwei-Faktor ist gerade nicht verfügbar.");
      })
      .catch(() => setFehler("Keine Verbindung. Bitte die Seite neu laden."));
  }, []);

  async function pruefen(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!start) return;
    const code = String(new FormData(e.currentTarget).get("code") ?? "");
    setLaeuft(true);
    setFehler(null);
    try {
      const r = await fetch("/api/admin/zwei-faktor/pruefen", {
        method: "POST",
        headers: KOPF,
        body: JSON.stringify({ faktorId: start.faktorId, code }),
      });
      const daten = (await r.json().catch(() => ({}))) as { fehler?: string; weiter?: string };
      if (r.ok && daten.weiter) return window.location.assign(daten.weiter);
      setFehler(daten.fehler ?? "Der Code stimmt nicht.");
    } catch {
      setFehler("Keine Verbindung. Bitte noch einmal versuchen.");
    }
    setLaeuft(false);
  }

  return (
    <form className="admin-karte" onSubmit={pruefen}>
      <h1 style={{ fontSize: 24 }}>Zwei-Faktor</h1>
      {start?.art === "einrichten" && (
        <>
          <p>
            Einmalig einrichten: Scanne den QR-Code mit einer Authenticator-App (zum Beispiel Google Authenticator,
            Microsoft Authenticator oder 1Password) und gib dann den sechsstelligen Code ein.
          </p>
          {/* eslint-disable-next-line @next/next/no-img-element -- QR-Code kommt als data:-SVG von Supabase */}
          <img className="admin-qr" src={start.qr} alt="QR-Code für die Authenticator-App" />
          <p style={{ fontSize: 13 }}>Ohne Kamera: diesen Schlüssel in der App eintragen</p>
          <p className="admin-geheimnis">{start.geheimnis}</p>
        </>
      )}
      {start?.art === "code" && <p>Gib den sechsstelligen Code aus deiner Authenticator-App ein.</p>}
      {!start && !fehler && <p className="admin-unterzeile">Wird geladen …</p>}
      {fehler && <p className="admin-fehler" role="alert">{fehler}</p>}
      {start && (
        <>
          <label className="admin-feld">
            Code
            <input name="code" inputMode="numeric" autoComplete="one-time-code" pattern="\d{6}" maxLength={6} required autoFocus />
          </label>
          <button className="admin-knopf" type="submit" disabled={laeuft}>
            {laeuft ? "Prüfe …" : "Bestätigen"}
          </button>
        </>
      )}
    </form>
  );
}
