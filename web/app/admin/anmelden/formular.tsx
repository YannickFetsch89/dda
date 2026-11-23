"use client";
import { useState, type FormEvent } from "react";

export function AnmeldeFormular() {
  const [fehler, setFehler] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);

  async function absenden(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setLaeuft(true);
    setFehler(null);
    try {
      const r = await fetch("/api/admin/anmelden", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: form.get("email"), passwort: form.get("passwort") }),
      });
      const daten = (await r.json().catch(() => ({}))) as { fehler?: string; weiter?: string };
      if (r.ok && daten.weiter) return window.location.assign(daten.weiter);
      setFehler(daten.fehler ?? "Anmelden hat nicht geklappt.");
    } catch {
      setFehler("Keine Verbindung. Bitte noch einmal versuchen.");
    }
    setLaeuft(false);
  }

  return (
    <form className="admin-karte" onSubmit={absenden}>
      <h1 style={{ fontSize: 24 }}>Admin-Anmeldung</h1>
      <p className="admin-unterzeile">dies.das.düsseldorf</p>
      {fehler && <p className="admin-fehler" role="alert">{fehler}</p>}
      <label className="admin-feld">
        Mailadresse
        <input name="email" type="email" autoComplete="username" required />
      </label>
      <label className="admin-feld">
        Passwort
        <input name="passwort" type="password" autoComplete="current-password" required />
      </label>
      <button className="admin-knopf" type="submit" disabled={laeuft}>
        {laeuft ? "Prüfe …" : "Weiter"}
      </button>
    </form>
  );
}
