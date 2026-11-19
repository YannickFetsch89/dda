"use client";
// Nutzerkonten – gemeinsame Client-Bausteine: Abgleich im Hintergrund, Hinweis nach dem ersten Merken,
// Anfrage-Helfer und kleine Formular-Teile. Die Seiten unter /konto sind statische Hüllen; alles Persönliche
// kommt hier über /api/konto/* (Plan 3.1).
import Link from "next/link";
import { Suspense, useEffect, useRef, useState, useSyncExternalStore, type ReactNode } from "react";
import { ERSTES_MERKEN_EVENT, useKontoZustand } from "./client";
import { usePathname } from "next/navigation";
import {
  KONTO_EVENT, abarbeiten, abgleichen, kontoAttributAbgleichen, kontoZustand, kontomodus, uebernahmePruefen,
} from "@/lib/konto/merk-store";

export type Antwort = { status: number | null; daten: Record<string, unknown> };

/** Anfrage an eine Konto-Route. JSON hin und zurück, nie mit Cache. */
export async function konto(pfad: string, methode = "GET", body?: unknown): Promise<Antwort> {
  try {
    const r = await fetch(`/api/konto/${pfad}`, {
      method: methode,
      cache: "no-store",
      credentials: "same-origin",
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    // Set-Cookie (Anmelden, Bestätigen, Alters-Häkchen, 403 …) ist angewandt → html[data-konto] nachziehen (Plan Mein Bereich 3.0)
    kontoAttributAbgleichen();
    let daten: Record<string, unknown> = {};
    try {
      daten = await r.json();
    } catch {
      // kein JSON
    }
    return { status: r.status, daten };
  } catch {
    return { status: null, daten: { fehler: "Keine Verbindung. Bitte versuch es gleich noch einmal." } };
  }
}

export const fehlerText = (a: Antwort) =>
  (typeof a.daten.fehler === "string" && a.daten.fehler) || "Das hat leider nicht geklappt. Bitte versuch es noch einmal.";

/** Im Layout: Übernahme beim Seitenaufruf, Warteschlange und Abgleich beim Fokus (Plan 5.4, 5.5). */
export function KontoSync() {
  useEffect(() => {
    // Erst den Kontozustand am <html> nachziehen, dann die Merkliste (Plan Mein Bereich 3.0)
    kontoAttributAbgleichen();
    if (kontomodus()) void uebernahmePruefen();
    const fokus = () => {
      if (document.visibilityState !== "visible") return;
      // Vor der kontomodus()-Sperre: sonst sähe ein abgemeldeter Tab das Anmelden im anderen Tab nie
      kontoAttributAbgleichen();
      if (!kontomodus()) return;
      void abarbeiten();
      void abgleichen();
    };
    window.addEventListener("focus", fokus);
    document.addEventListener("visibilitychange", fokus);
    return () => {
      window.removeEventListener("focus", fokus);
      document.removeEventListener("visibilitychange", fokus);
    };
  }, []);
  return (
    <Suspense fallback={null}>
      <KontoPfadAbgleich />
    </Suspense>
  );
}

/** Abgleich bei jedem Pfadwechsel; eigene Suspense-Grenze, weil usePathname sonst das Vorrendern blockiert. */
function KontoPfadAbgleich() {
  const pfad = usePathname();
  useEffect(() => {
    kontoAttributAbgleichen();
  }, [pfad]);
  return null;
}

// useKontoZustand liegt in client.tsx (TabBar braucht ihn; client.tsx darf diese Datei nicht importieren, Ring)
export { useKontoZustand };
// Für Aufrufer, die den Cookie-Zustand direkt brauchen (z. B. vor dem ersten Abgleich)
export { kontoZustand };

/** Einmaliger Hinweis nach dem ersten Herz-Klick, abgemeldet (Plan 7.2). Kommt nie beim Seitenaufruf. */
export function MerkHinweis() {
  const [offen, setOffen] = useState(false);
  useEffect(() => {
    const zeigen = () => setOffen(true);
    window.addEventListener(ERSTES_MERKEN_EVENT, zeigen);
    return () => window.removeEventListener(ERSTES_MERKEN_EVENT, zeigen);
  }, []);
  useEffect(() => {
    if (!offen) return;
    const t = window.setTimeout(() => setOffen(false), 8000);
    return () => window.clearTimeout(t);
  }, [offen]);
  if (!offen) return null;
  return (
    <div className="merk-hinweis" role="status">
      <span className="icon" aria-hidden data-icon="favorite" />
      <span>
        Gemerkt! Deine Merkliste liegt nur auf diesem Gerät.{" "}
        <Link href="/konto/anmelden?weiter=/merkliste">Mit Konto überall dabei</Link>
      </span>
      <button type="button" className="merk-hinweis__x" aria-label="Hinweis schließen" onClick={() => setOffen(false)}>
        <span className="icon" aria-hidden data-icon="close" />
      </button>
    </div>
  );
}

const kontoAbo = (cb: () => void) => {
  window.addEventListener("ddd-merkliste-geaendert", cb);
  window.addEventListener("focus", cb);
  window.addEventListener(KONTO_EVENT, cb);
  return () => {
    window.removeEventListener("ddd-merkliste-geaendert", cb);
    window.removeEventListener("focus", cb);
    window.removeEventListener(KONTO_EVENT, cb);
  };
};
/** Angemeldet mit Alters-Häkchen? (nur Anzeige, aus dem Hinweis-Cookie) – auf dem Server immer false */
export function useKontomodus(): boolean {
  return useSyncExternalStore(kontoAbo, kontomodus, () => false);
}

/** Passwortfeld mit „Anzeigen“-Button (Plan 5.1) */
export function PasswortFeld({
  id, label, wert, setzen, autocomplete, hinweis,
}: { id: string; label: string; wert: string; setzen: (w: string) => void; autocomplete: string; hinweis?: string }) {
  const [sichtbar, setSichtbar] = useState(false);
  return (
    <div className="formular__feld">
      <label className="formular__label" htmlFor={id}>{label}</label>
      <div className="passwort-feld">
        <input
          id={id}
          type={sichtbar ? "text" : "password"}
          autoComplete={autocomplete}
          value={wert}
          onChange={(e) => setzen(e.target.value)}
          required
          maxLength={200}
          aria-describedby={hinweis ? `${id}-hinweis` : undefined}
        />
        <button type="button" className="passwort-feld__zeigen" onClick={() => setSichtbar((s) => !s)} aria-pressed={sichtbar}>
          {sichtbar ? "Verbergen" : "Anzeigen"}
        </button>
      </div>
      {hinweis && <span id={`${id}-hinweis`} className="formular__hinweis">{hinweis}</span>}
    </div>
  );
}

/** Honeypot wie beim Newsletter: für Menschen unsichtbar */
export function Honeypot({ wert, setzen }: { wert: string; setzen: (w: string) => void }) {
  return (
    <div aria-hidden="true" style={{ position: "absolute", left: "-10000px", width: 1, height: 1, overflow: "hidden" }}>
      <label htmlFor="website">Website</label>
      <input id="website" name="website" tabIndex={-1} autoComplete="off" value={wert} onChange={(e) => setzen(e.target.value)} />
    </div>
  );
}

export function Meldung({ art = "info", children }: { art?: "info" | "fehler" | "ok"; children: ReactNode }) {
  return (
    <div className={`status ${art === "fehler" ? "status--fehler" : "status--info"}`} role={art === "fehler" ? "alert" : "status"}>
      <span className="icon" aria-hidden data-icon={art === "fehler" ? "error" : art === "ok" ? "check_circle" : "info"} />
      <div>{children}</div>
    </div>
  );
}

/**
 * Rückfrage als Popup (17.11.2026): Interessen ohne Häkchen abschicken bzw. gespeicherte Interessen widerrufen. Beide
 * Buttons sind gleich gestaltet, damit die Wahl frei bleibt. Escape bzw. Schließen zählt als „Abbrechen“ (nichts passiert).
 */
export function Rueckfrage({
  offen, titel, children, ja, nein, onJa, onNein, onAbbrechen,
}: {
  offen: boolean;
  titel: string;
  children: ReactNode;
  ja: string;
  nein: string;
  onJa: () => void;
  onNein: () => void;
  onAbbrechen: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (offen && !d.open) d.showModal();
    if (!offen && d.open) d.close();
  }, [offen]);
  return (
    <dialog ref={ref} className="konto-dialog" aria-labelledby="konto-dialog-titel" onCancel={(e) => { e.preventDefault(); onAbbrechen(); }}>
      <h2 className="d" id="konto-dialog-titel">{titel}</h2>
      <div className="konto-dialog__text">{children}</div>
      <div className="konto-dialog__knoepfe">
        <button type="button" className="btn btn--outline btn--gross" onClick={onNein}>{nein}</button>
        <button type="button" className="btn btn--outline btn--gross" onClick={onJa}>{ja}</button>
      </div>
      <button type="button" className="konto-dialog__zu icon-btn" aria-label="Schließen" onClick={onAbbrechen}>
        <span className="icon" aria-hidden data-icon="close" />
      </button>
    </dialog>
  );
}

type Gestuft = { kurz: string; mehr: string };

/**
 * Ein Häkchen mit gestuftem Text (17.11.2026): höchstens zwei Sätze sichtbar, der Rest unter „Mehr dazu“. Der Text
 * bleibt vollständig auf der Seite (GESTUFT in lib/konto/texte.ts). „Mehr dazu“ steht außerhalb des label, damit ein
 * Klick darauf das Häkchen nicht umschaltet.
 */
export function EinwilligungFeld({
  titel, intro, label, labelTitel, checked, disabled, onChange, className = "",
}: {
  titel?: string;
  intro?: Gestuft;
  label: Gestuft;
  labelTitel?: string;
  checked: boolean;
  disabled?: boolean;
  onChange: (an: boolean) => void;
  className?: string;
}) {
  // Endet der ausgeklappte Teil mit einem Doppelpunkt (Überleitung zum Häkchen), steht dort ein Punkt
  const mehr = [intro?.mehr, label.mehr].filter(Boolean).map((t) => (t as string).replace(/:$/, "."));
  return (
    <div className={`konto-einw ${className}`}>
      {(titel || intro?.kurz) && (
        <p>
          {titel && <b>{titel}</b>} {intro?.kurz}
        </p>
      )}
      <label className="formular__check">
        <input type="checkbox" checked={checked} disabled={disabled} onChange={(e) => onChange(e.target.checked)} />
        <span>
          {labelTitel && <b>{labelTitel} </b>}
          {label.kurz}
        </span>
      </label>
      {mehr.length > 0 && (
        <details className="konto-mehr">
          <summary>
            Mehr dazu
            <span className="icon" aria-hidden data-icon="expand_more" />
          </summary>
          {mehr.map((t) => (
            <p key={t}>{t}</p>
          ))}
        </details>
      )}
    </div>
  );
}

/** Art.-13-Hinweis unter jedem Formular mit Mailadresse */
export function Art13Hinweis() {
  return (
    <p className="formular__hinweis">
      Wir nutzen deine Adresse für die Anmeldung und dein Konto. Mehr dazu in der{" "}
      <Link href="/datenschutz#konto">Datenschutzerklärung</Link>.
    </p>
  );
}
