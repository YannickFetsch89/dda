"use client";
// Abmeldeseite der Geburtstagsmail (Plan Geburtstagsmail G4, Kontenplan 13a): liest das Token aus dem Fragment
// (#t=…), schickt erst beim Klick auf den Button POST /api/konto/geburtstag-abmelden. Kein Abruf beim Seitenaufruf.
import Link from "next/link";
import { useEffect, useState } from "react";
import { Meldung, fehlerText, konto } from "./konto";

type Zustand = { art: "pruefen" } | { art: "ohne" } | { art: "bereit"; token: string } | { art: "sendet"; token: string } | { art: "fertig"; text: string } | { art: "fehler"; token: string; text: string };

export function GeburtstagAbmelden() {
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
        Dieser Link ist unvollständig. Die Geburtstagsmail kannst du auch im Konto unter{" "}
        <Link href="/konto/datenschutz">Datenschutz</Link> abschalten.
      </Meldung>
    );
  }
  if (z.art === "fertig") return <Meldung art="ok">{z.text}</Meldung>;

  const senden = async () => {
    setZ({ art: "sendet", token: z.token });
    const a = await konto("geburtstag-abmelden", "POST", { token: z.token });
    if (a.status === 200) setZ({ art: "fertig", text: String(a.daten.meldung ?? "Erledigt.") });
    else setZ({ art: "fehler", token: z.token, text: fehlerText(a) });
  };

  return (
    <div className="konto-bereich">
      <section className="konto-abschnitt">
        <p>Möchtest du keine Geburtstagsmails mehr von uns bekommen? Dein Konto und deine Merkliste bleiben unverändert.</p>
        <button type="button" className="btn btn--navy" disabled={z.art === "sendet"} onClick={senden}>
          Keine Geburtstagsmails mehr
        </button>
        {z.art === "fehler" && <Meldung art="fehler">{z.text}</Meldung>}
      </section>
    </div>
  );
}
