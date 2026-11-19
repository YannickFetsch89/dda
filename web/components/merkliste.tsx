"use client";
// Merkliste: abgemeldet IDs aus localStorage, Events über /api/events; angemeldet Konto-Liste über
// /api/konto/merkliste?mit=events (ohne 100er-Grenze). Kommende nach Datum, „Vorbei (n)“ eingeklappt (E9);
// angemeldet (data-konto="1") stattdessen ein Link „Erlebt (n)“ auf /konto/erlebt (Plan Mein Bereich 3.4).
// Untertitel und Konto-Hinweis sind Client-Teile, damit der Server nichts über die Sitzung weiß (Plan 7.1).
import Link from "next/link";
import { useEffect, useState, useSyncExternalStore } from "react";
import { useMerkliste } from "./client";
import { EventKarte, Leer, SkeletonKarten } from "./karten";
import { useKontoZustand, useKontomodus } from "./konto";
import {
  abgleichen, angemeldetOhneAlter, kontoAttributAbgleichen, meldungSchliessen, nachfrageUebernehmen, nachfrageVerwerfen, STATUS_LEER,
  statusAbonnieren, statusSnapshot,
} from "@/lib/konto/merk-store";
import { merklisteAufteilen } from "@/lib/konto/merk-logik";
import type { DddEvent } from "@/lib/typen";

type Zustand = { status: "laden" } | { status: "fehler" } | { status: "fertig"; heute: string; events: DddEvent[] };

const useMerkStatus = () => useSyncExternalStore(statusAbonnieren, statusSnapshot, () => STATUS_LEER);

/** Untertitel: „Nur auf diesem Gerät gespeichert“ bzw. angemeldet „In deinem Konto gespeichert“ */
export function MerklisteUntertitel() {
  return <span>{useKontomodus() ? "In deinem Konto gespeichert" : "Nur auf diesem Gerät gespeichert"}</span>;
}

async function eventsLaden(ids: string[], konto: boolean): Promise<{ heute: string; events: DddEvent[] }> {
  if (!ids.length) return { heute: "", events: [] };
  if (konto) {
    const r = await fetch("/api/konto/merkliste?mit=events", { cache: "no-store" });
    // Läuft weder über konto() noch über abruf(): bei 403 setzt der Server ddd_konto=0 (Plan Mein Bereich 3.0)
    kontoAttributAbgleichen();
    if (!r.ok) throw new Error(String(r.status));
    const d = (await r.json()) as { heute?: string; events?: DddEvent[] };
    const gefunden = new Set((d.events ?? []).map((e) => e.id));
    // Merkungen, die nur auf diesem Gerät liegen, über die öffentliche Route nachladen
    const rest = ids.filter((id) => !gefunden.has(id)).slice(0, 100);
    if (!rest.length) return { heute: d.heute ?? "", events: d.events ?? [] };
    const r2 = await fetch(`/api/events?ids=${encodeURIComponent(rest.join(","))}`);
    const d2 = r2.ok ? ((await r2.json()) as { heute: string; events: DddEvent[] }) : { heute: d.heute ?? "", events: [] };
    return { heute: d.heute || d2.heute, events: [...(d.events ?? []), ...d2.events] };
  }
  const r = await fetch(`/api/events?ids=${encodeURIComponent(ids.join(","))}`);
  if (!r.ok) throw new Error(String(r.status));
  return r.json();
}

export function MerklisteInhalt({ kontenAn }: { kontenAn: boolean }) {
  const ids = useMerkliste();
  const konto = useKontomodus();
  const kontoZustand = useKontoZustand();
  const status = useMerkStatus();
  const schluessel = ids.join(",");
  const [zustand, setZustand] = useState<Zustand>({ status: "laden" });
  const [versuch, setVersuch] = useState(0);
  const [vorbeiOffen, setVorbeiOffen] = useState(false);

  // Angemeldet: beim Öffnen mit dem Konto abgleichen (höchstens alle 60 s, Plan 5.5)
  useEffect(() => {
    if (konto) void abgleichen();
  }, [konto]);

  useEffect(() => {
    if (!schluessel) return;
    let abgebrochen = false;
    eventsLaden(schluessel.split(","), konto)
      .then((d) => {
        if (!abgebrochen) setZustand({ status: "fertig", heute: d.heute, events: d.events });
      })
      .catch(() => {
        if (!abgebrochen) setZustand({ status: "fehler" });
      });
    return () => {
      abgebrochen = true;
    };
  }, [schluessel, versuch, konto]);

  const kopf = (
    <>
      {kontenAn && !konto && <KontoHinweis leer={!ids.length} />}
      {status.meldung && (
        <div className="status status--info" role="status" style={{ marginBottom: 16 }}>
          <span className="icon" aria-hidden data-icon="cloud_done" />
          <div>
            {status.meldung}{" "}
            <button type="button" className="link konto-textknopf" onClick={meldungSchliessen}>OK</button>
          </div>
        </div>
      )}
      {status.nichtGespeichert && (
        <div className="status status--info" role="status" style={{ marginBottom: 16 }}>
          <span className="icon" aria-hidden data-icon="sync_problem" />
          <div>Noch nicht gespeichert, wir versuchen es weiter.</div>
        </div>
      )}
    </>
  );

  if (!ids.length) {
    return (
      <>
        {kopf}
        <Leer titel="Noch nichts gemerkt.">
          <span>Tipp aufs Herz, dann landet ein Event hier.</span>
          <Link href="/entdecken" className="link">Events entdecken</Link>
        </Leer>
        {konto && <NurAufDemGeraet ids={status.nachfrage} />}
      </>
    );
  }
  if (zustand.status === "laden") return <>{kopf}<SkeletonKarten anzahl={Math.min(ids.length, 8)} /></>;
  if (zustand.status === "fehler") {
    return (
      <>
        {kopf}
        <div className="status status--fehler" role="alert">
          <span className="icon" aria-hidden data-icon="error" />
          <div>
            Die Merkliste konnte nicht geladen werden.{" "}
            <button type="button" className="link" onClick={() => setVersuch((v) => v + 1)} style={{ color: "inherit", textDecoration: "underline" }}>
              Nochmal versuchen
            </button>
          </div>
        </div>
      </>
    );
  }

  const vorhanden = zustand.events.filter((e) => ids.includes(e.id));
  const { kommend, vorbei } = merklisteAufteilen(vorhanden, zustand.heute);
  const fehlend = ids.length - vorhanden.length;
  return (
    <>
      {kopf}
      {kommend.length > 0 ? (
        <div className="raster" role="list">
          {kommend.map((e) => <EventKarte key={e.id} e={e} heute={zustand.heute} variante="grid" />)}
        </div>
      ) : (
        <Leer titel={vorbei.length ? "Deine gemerkten Events sind vorbei." : "Gerade nichts Kommendes gemerkt."} />
      )}
      {/* Angemeldet (data-konto="1") eigene Seite „Erlebt“; abgemeldet und bei Cookie 0 „Vorbei“ wie bisher (S6) */}
      {vorbei.length > 0 && kontoZustand === "1" && (
        <p className="merk-erlebt">
          <Link href="/konto/erlebt" className="link">Erlebt ({vorbei.length}) →</Link>
        </p>
      )}
      {vorbei.length > 0 && kontoZustand !== "1" && (
        <details className="merk-vorbei" open={vorbeiOffen} onToggle={(e) => setVorbeiOffen(e.currentTarget.open)}>
          <summary>Vorbei ({vorbei.length})</summary>
          <div className="raster" role="list">
            {vorbei.map((e) => <EventKarte key={e.id} e={e} heute={zustand.heute} variante="grid" />)}
          </div>
        </details>
      )}
      {fehlend > 0 && (
        <p className="zuordnungs-hinweis" style={{ marginTop: 16 }}>
          {fehlend} gemerkte{fehlend === 1 ? "s Event ist" : " Events sind"} nicht mehr verfügbar.
        </p>
      )}
      {konto && <NurAufDemGeraet ids={status.nachfrage} />}
    </>
  );
}

/** Hinweiskasten abgemeldet (Plan 7.1); ohne Alters-Häkchen mit Link auf /konto/willkommen (5.4 Schritt 0a). */
function KontoHinweis({ leer }: { leer: boolean }) {
  const ohneAlter = useSyncExternalStore(
    (cb) => {
      window.addEventListener("ddd-merkliste-geaendert", cb);
      return () => window.removeEventListener("ddd-merkliste-geaendert", cb);
    },
    angemeldetOhneAlter,
    () => false,
  );
  if (ohneAlter) {
    return (
      <div className="konto-hinweis" role="note">
        <span className="icon" aria-hidden data-icon="cloud_sync" />
        <div>
          Bestätige kurz dein Alter, dann landet deine Merkliste im Konto.{" "}
          <Link href="/konto/willkommen" className="btn btn--gold btn--klein">Alter bestätigen</Link>
        </div>
      </div>
    );
  }
  if (leer) {
    return (
      <p className="formular__hinweis" style={{ marginBottom: 16 }}>
        Schon ein Konto? <Link href="/konto/anmelden?weiter=/merkliste">Anmelden</Link>, dann siehst du deine Merkliste von anderen Geräten.
      </p>
    );
  }
  return (
    <div className="konto-hinweis" role="note">
      <span className="icon" aria-hidden data-icon="cloud_sync" />
      <div>
        <b>Deine Merkliste auf allen Geräten</b>
        <p>
          Mit einem kostenlosen Konto liegt sie sicher bei uns – auf dem Handy, am Laptop und bald in unserer App. Beim
          ersten Konto nehmen wir sie mit. Hast du schon eine Merkliste im Konto, fragt die Seite nach, was dazukommen soll.
        </p>
        <p>
          <Link href="/konto/anmelden?weiter=/merkliste" className="btn btn--gold btn--klein">Anmelden oder Konto anlegen</Link>{" "}
          <span className="formular__hinweis">Kostenlos, mit Mailadresse und Passwort.</span>
        </p>
      </div>
    </div>
  );
}

/** Block „Nur auf diesem Gerät“ mit Nachfrage (Plan 5.4 Schritt 3, 7.1) */
function NurAufDemGeraet({ ids }: { ids: string[] }) {
  const [sendet, setSendet] = useState(false);
  if (!ids.length) return null;
  const n = ids.length;
  return (
    <section className="konto-hinweis konto-hinweis--geraet" aria-label="Nur auf diesem Gerät">
      <span className="icon" aria-hidden data-icon="smartphone" />
      <div>
        <b>Nur auf diesem Gerät</b>
        <p>Auf diesem Gerät {n === 1 ? "ist noch 1 Event" : `sind noch ${n} Events`} gemerkt, {n === 1 ? "das" : "die"} nicht in deinem Konto {n === 1 ? "ist" : "sind"}.</p>
        <p className="formular__aktionen">
          <button type="button" className="btn btn--gold btn--klein" disabled={sendet}
            onClick={async () => { setSendet(true); await nachfrageUebernehmen(); setSendet(false); }}>
            Ins Konto übernehmen
          </button>
          <button type="button" className="btn btn--outline btn--klein" disabled={sendet}
            onClick={() => { if (window.confirm(`${n} ${n === 1 ? "Event" : "Events"} von diesem Gerät entfernen?`)) nachfrageVerwerfen(ids); }}>
            Auf diesem Gerät verwerfen
          </button>
        </p>
      </div>
    </section>
  );
}
