"use client";
// Nutzerkonten – Anmelden, Konto anlegen, Link bestätigen, Passwort vergessen, neues Passwort (Plan 5.1, 5.2).
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState, type FormEvent } from "react";
import { Art13Hinweis, Honeypot, Meldung, PasswortFeld, fehlerText, konto } from "./konto";
import { uebernahmePruefen } from "@/lib/konto/merk-store";
import { weiterPruefen } from "@/lib/konto/weiter";

const PASSWORT_REGEL = "Mindestens 10 Zeichen. Länge schützt besser als Sonderzeichen.";

// ── Anmelden / Konto anlegen ─────────────────────────────────────────────────
export function AnmeldenSeite() {
  return (
    <Suspense fallback={null}>
      <AnmeldenFormular />
    </Suspense>
  );
}

function AnmeldenFormular() {
  const router = useRouter();
  const suche = useSearchParams();
  const weiter = weiterPruefen(suche.get("weiter"));
  const [modus, setModus] = useState<"anmelden" | "neu">(suche.get("neu") === "1" ? "neu" : "anmelden");
  const [email, setEmail] = useState("");
  const [passwort, setPasswort] = useState("");
  const [alter, setAlter] = useState(false);
  const [falle, setFalle] = useState("");
  const [sendet, setSendet] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [nichtBestaetigt, setNichtBestaetigt] = useState(false);
  const [fertig, setFertig] = useState<string | null>(null);

  async function absenden(ev: FormEvent) {
    ev.preventDefault();
    setFehler(null);
    setNichtBestaetigt(false);
    setSendet(true);
    if (modus === "anmelden") {
      const a = await konto("anmelden", "POST", { email, passwort, weiter });
      setSendet(false);
      if (a.status === 200) {
        setPasswort("");
        void uebernahmePruefen();
        router.push(typeof a.daten.ziel === "string" ? a.daten.ziel : weiter);
        return;
      }
      if (a.daten.code === "nicht_bestaetigt") setNichtBestaetigt(true);
      setFehler(fehlerText(a));
      return;
    }
    const a = await konto("registrieren", "POST", { email, passwort, alter_ok: alter, website: falle });
    setSendet(false);
    if (a.status === 200) {
      setPasswort("");
      setFertig(typeof a.daten.meldung === "string" ? a.daten.meldung : "Fast geschafft!");
      return;
    }
    setFehler(fehlerText(a));
  }

  if (fertig) {
    return (
      <div className="formular__danke">
        <span className="icon" aria-hidden data-icon="mark_email_read" />
        <h2 className="d">Schau in dein Postfach</h2>
        <p>{fertig}</p>
        <ErneutSenden email={email} />
      </div>
    );
  }

  return (
    <form className="formular konto-form" onSubmit={absenden} noValidate>
      <div className="konto-umschalter" role="tablist" aria-label="Anmelden oder Konto anlegen">
        <button type="button" role="tab" aria-selected={modus === "anmelden"} onClick={() => { setModus("anmelden"); setFehler(null); }}>
          Anmelden
        </button>
        <button type="button" role="tab" aria-selected={modus === "neu"} onClick={() => { setModus("neu"); setFehler(null); }}>
          Konto anlegen
        </button>
      </div>
      <Honeypot wert={falle} setzen={setFalle} />
      <div className="formular__feld">
        <label className="formular__label" htmlFor="konto-email">Mailadresse</label>
        <input id="konto-email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required maxLength={254} />
      </div>
      <PasswortFeld
        id="konto-passwort"
        label="Passwort"
        wert={passwort}
        setzen={setPasswort}
        autocomplete={modus === "neu" ? "new-password" : "current-password"}
        hinweis={modus === "neu" ? PASSWORT_REGEL : undefined}
      />
      {modus === "neu" && (
        <label className="formular__check">
          <input type="checkbox" checked={alter} onChange={(e) => setAlter(e.target.checked)} required />
          <span>Ich bin mindestens 16 Jahre alt.</span>
        </label>
      )}
      {fehler && (
        <Meldung art="fehler">
          {fehler}
          {nichtBestaetigt && <ErneutSenden email={email} />}
        </Meldung>
      )}
      {modus === "neu" && (
        <p className="formular__hinweis">
          {/* Art.-13-Hinweis hier mit drin statt unter dem Button (17.11.2026). Der Satz zu den Nutzungsbedingungen
              bleibt wörtlich und am Stück so, wie er als Nachweis gespeichert ist (NACHWEIS_TEXT.nutzungsbedingungen). */}
          Wir nutzen deine Adresse für die Anmeldung und dein Konto. Mit „Konto anlegen“ akzeptierst du unsere <Link href="/nutzungsbedingungen">Nutzungsbedingungen</Link> (mit{" "}
          <Link href="/nutzungsbedingungen#widerruf">Widerrufsbelehrung</Link>). Wie wir deine Daten verarbeiten, steht in der{" "}
          <Link href="/datenschutz#konto">Datenschutzerklärung</Link>.
        </p>
      )}
      <div className="formular__aktionen">
        <button type="submit" className="btn btn--navy btn--gross" aria-disabled={sendet || (modus === "neu" && !alter)} disabled={sendet || (modus === "neu" && !alter)}>
          {modus === "neu" ? "Konto anlegen" : "Anmelden"}
        </button>
        {modus === "anmelden" && <Link href="/konto/passwort-vergessen" className="link">Passwort vergessen?</Link>}
      </div>
      {modus === "anmelden" && (
        <p className="formular__hinweis">
          Noch kein Konto?{" "}
          <button type="button" className="link konto-textknopf" onClick={() => setModus("neu")}>Konto anlegen</button>
        </p>
      )}
      {modus === "anmelden" && <Art13Hinweis />}
    </form>
  );
}

/** „Keine Mail bekommen?“ – frühestens nach 60 Sekunden erneut (Plan 5.1 Schritt 4) */
function ErneutSenden({ email }: { email: string }) {
  const [zustand, setZustand] = useState<"bereit" | "sendet" | "gesendet">("bereit");
  const [text, setText] = useState<string | null>(null);
  if (!email) return null;
  return (
    <p className="formular__hinweis" style={{ marginTop: 8 }}>
      {zustand === "gesendet" ? (
        text
      ) : (
        <button
          type="button"
          className="link konto-textknopf"
          disabled={zustand === "sendet"}
          onClick={async () => {
            setZustand("sendet");
            const a = await konto("bestaetigung-erneut", "POST", { email });
            setText(a.status === 200 ? String(a.daten.meldung) : fehlerText(a));
            setZustand("gesendet");
          }}
        >
          Keine Mail bekommen? Bestätigungsmail erneut senden
        </button>
      )}
    </p>
  );
}

// ── Link aus der Mail (Plan 5.2): prüft erst nach dem Klick, nie beim Laden ─────
export function BestaetigenSeite() {
  const router = useRouter();
  const gelesen = useRef(false);
  const [link, setLink] = useState<{ tokenHash: string; art: "neu" | "reset" } | null | "leer">(null);
  const [sendet, setSendet] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");

  useEffect(() => {
    if (gelesen.current) return;
    gelesen.current = true;
    const frag = new URLSearchParams(window.location.hash.slice(1));
    const tokenHash = frag.get("token_hash");
    const art = frag.get("art") === "reset" ? "reset" : "neu";
    // Fragment sofort aus der Adresszeile entfernen (Plan 5.2)
    if (window.location.hash) history.replaceState(null, "", window.location.pathname + window.location.search);
    // Ohne Fragment angekommen (z. B. Outlook Safe Links): Code-Eingabe bzw. neuer Link
    setLink(tokenHash ? { tokenHash, art } : frag.get("art") === "reset" || new URLSearchParams(window.location.search).get("art") === "reset" ? { tokenHash: "", art: "reset" } : "leer");
  }, []);

  async function pruefen(body: Record<string, unknown>) {
    setSendet(true);
    setFehler(null);
    const a = await konto("link-pruefen", "POST", body);
    setSendet(false);
    if (a.status === 200 && typeof a.daten.ziel === "string") {
      if (body.art === "neu") void uebernahmePruefen();
      router.push(a.daten.ziel);
      return;
    }
    setFehler(fehlerText(a));
  }

  if (link === null) return null;
  if (link !== "leer" && link.art === "reset" && !link.tokenHash) {
    return (
      <Meldung>
        Der Link ist unvollständig angekommen. Fordere bitte einen neuen an.{" "}
        <Link href="/konto/passwort-vergessen">Neuen Link anfordern</Link>
      </Meldung>
    );
  }
  if (link === "leer") {
    return (
      <form className="formular konto-form" onSubmit={(e) => { e.preventDefault(); void pruefen({ email, code, art: "neu" }); }}>
        <Meldung>Der Link ist unvollständig angekommen. Gib einfach deine Mailadresse und den 6-stelligen Code aus der Mail ein.</Meldung>
        <div className="formular__feld">
          <label className="formular__label" htmlFor="code-email">Mailadresse</label>
          <input id="code-email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="formular__feld">
          <label className="formular__label" htmlFor="code">Code aus der Mail</label>
          <input id="code" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9 ]*" maxLength={7} value={code} onChange={(e) => setCode(e.target.value)} required />
        </div>
        {fehler && <Meldung art="fehler">{fehler}</Meldung>}
        <div className="formular__aktionen">
          <button type="submit" className="btn btn--navy btn--gross" disabled={sendet}>Adresse bestätigen</button>
        </div>
      </form>
    );
  }
  return (
    <div className="formular konto-form">
      <p>{link.art === "reset" ? "Klick auf den Button, um ein neues Passwort festzulegen." : "Fast geschafft: Klick auf den Button, um deine Mailadresse zu bestätigen."}</p>
      {fehler && (
        <Meldung art="fehler">
          {fehler}{" "}
          {link.art === "reset" ? <Link href="/konto/passwort-vergessen">Neuen Link anfordern</Link> : <Link href="/konto/anmelden">Zur Anmeldung</Link>}
        </Meldung>
      )}
      <div className="formular__aktionen">
        <button type="button" className="btn btn--navy btn--gross" disabled={sendet} onClick={() => pruefen({ token_hash: link.tokenHash, art: link.art })}>
          {link.art === "reset" ? "Neues Passwort festlegen" : "Adresse bestätigen"}
        </button>
      </div>
    </div>
  );
}

// ── Passwort vergessen (Plan 5.1 Schritt 8) ──────────────────────────────────
export function PasswortVergessenSeite() {
  const [email, setEmail] = useState("");
  const [falle, setFalle] = useState("");
  const [text, setText] = useState<string | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [sendet, setSendet] = useState(false);
  if (text) return <Meldung art="ok">{text}</Meldung>;
  return (
    <form
      className="formular konto-form"
      noValidate
      onSubmit={async (e) => {
        e.preventDefault();
        setSendet(true);
        const a = await konto("passwort-vergessen", "POST", { email, website: falle });
        setSendet(false);
        if (a.status === 200) setText(String(a.daten.meldung));
        else setFehler(fehlerText(a));
      }}
    >
      <Honeypot wert={falle} setzen={setFalle} />
      <div className="formular__feld">
        <label className="formular__label" htmlFor="vergessen-email">Mailadresse</label>
        <input id="vergessen-email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      </div>
      {fehler && <Meldung art="fehler">{fehler}</Meldung>}
      <div className="formular__aktionen">
        <button type="submit" className="btn btn--navy btn--gross" disabled={sendet}>Link schicken</button>
        <Link href="/konto/anmelden" className="link">Zurück zur Anmeldung</Link>
      </div>
      <Art13Hinweis />
    </form>
  );
}

// ── Neues Passwort nach Reset (Plan 5.1 Schritt 10) ──────────────────────────
export function PasswortNeuSeite() {
  const router = useRouter();
  const [passwort, setPasswort] = useState("");
  const [fehler, setFehler] = useState<string | null>(null);
  const [sendet, setSendet] = useState(false);
  return (
    <form
      className="formular konto-form"
      onSubmit={async (e) => {
        e.preventDefault();
        setSendet(true);
        setFehler(null);
        const a = await konto("passwort-setzen", "POST", { passwort });
        setSendet(false);
        if (a.status === 200) {
          setPasswort("");
          void uebernahmePruefen();
          router.push(typeof a.daten.ziel === "string" ? a.daten.ziel : "/konto");
          return;
        }
        setFehler(a.status === 401 ? "Der Link ist abgelaufen. Fordere bitte einen neuen an." : fehlerText(a));
      }}
    >
      <PasswortFeld id="neues-passwort" label="Neues Passwort" wert={passwort} setzen={setPasswort} autocomplete="new-password" hinweis={PASSWORT_REGEL} />
      {fehler && (
        <Meldung art="fehler">
          {fehler} <Link href="/konto/passwort-vergessen">Neuen Link anfordern</Link>
        </Meldung>
      )}
      <div className="formular__aktionen">
        <button type="submit" className="btn btn--navy btn--gross" disabled={sendet}>Passwort speichern</button>
      </div>
    </form>
  );
}
