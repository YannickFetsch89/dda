"use client";
// Seiten /newsletter/bestaetigen und /newsletter/abmelden (Plan Admin-Dashboard 4.9, Stufe 4): liest das Token aus dem
// Fragment (#t=…) und schickt es erst beim Klick auf den Button an /api/newsletter/<aktion>. Kein Abruf beim
// Seitenaufruf – so lösen Link-Scanner der Mailprogramme weder Bestätigung noch Abmeldung aus.
import Link from "next/link";
import { useEffect, useState } from "react";
import { Meldung } from "./konto";

type Zustand =
  | { art: "pruefen" }
  | { art: "ohne" }
  | { art: "bereit"; token: string }
  | { art: "sendet"; token: string }
  | { art: "fertig"; text: string }
  | { art: "fehler"; token: string; text: string };

const TEXTE = {
  bestaetigen: {
    frage: "Möchtest du den Newsletter von dies.das.düsseldorf bekommen? Ein Klick, und deine Anmeldung ist bestätigt.",
    knopf: "Anmeldung bestätigen",
  },
  abmelden: {
    frage: "Möchtest du keine Mails mehr von uns bekommen? Wir löschen deine Adresse dann sofort.",
    knopf: "Abmelden und Adresse löschen",
  },
} as const;

export function NewsletterLink({ aktion }: { aktion: "bestaetigen" | "abmelden" }) {
  const [z, setZ] = useState<Zustand>({ art: "pruefen" });

  useEffect(() => {
    const t = new URLSearchParams(window.location.hash.slice(1)).get("t");
    // eslint-disable-next-line react-hooks/set-state-in-effect -- Fragment ist erst im Browser lesbar
    setZ(t ? { art: "bereit", token: t } : { art: "ohne" });
  }, []);

  if (z.art === "pruefen") return <div className="skeleton" style={{ height: 120 }} />;
  if (z.art === "ohne") {
    return (
      <Meldung>
        Dieser Link ist unvollständig. Bitte öffne ihn direkt aus der Mail. Fragen? <a href="mailto:hallo@diesdas.events">hallo@diesdas.events</a>
      </Meldung>
    );
  }
  if (z.art === "fertig") {
    return (
      <Meldung art="ok">
        {z.text} <Link href="/">Zur Startseite</Link>
      </Meldung>
    );
  }

  const senden = async () => {
    setZ({ art: "sendet", token: z.token });
    try {
      const r = await fetch(`/api/newsletter/${aktion}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ token: z.token }) });
      const d = (await r.json().catch(() => ({}))) as { meldung?: string; fehler?: string };
      if (r.ok) setZ({ art: "fertig", text: d.meldung ?? "Erledigt." });
      else setZ({ art: "fehler", token: z.token, text: d.fehler ?? "Das hat leider nicht geklappt." });
    } catch {
      setZ({ art: "fehler", token: z.token, text: "Keine Verbindung. Bitte versuch es noch einmal." });
    }
  };

  return (
    <section className="konto-abschnitt">
      <p>{TEXTE[aktion].frage}</p>
      <button type="button" className="btn btn--navy" disabled={z.art === "sendet"} onClick={senden}>
        {TEXTE[aktion].knopf}
      </button>
      {z.art === "fehler" && <Meldung art="fehler">{z.text}</Meldung>}
    </section>
  );
}
