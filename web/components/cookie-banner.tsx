"use client";
import Link from "next/link";
import Script from "next/script";
import { useEffect, useState } from "react";

const CONSENT_KEY = "ddd-cookie-consent";
const GA_ID = "G-EQWEWLYL35";

type Consent = "granted" | "denied" | null;

function consentLesen(): Consent {
  try {
    const wert = localStorage.getItem(CONSENT_KEY);
    if (wert === "granted" || wert === "denied") return wert;
  } catch {}
  return null;
}

export function CookieBanner() {
  const [consent, setConsent] = useState<Consent>(null);
  const [geladen, setGeladen] = useState(false);

  useEffect(() => {
    setConsent(consentLesen());
    setGeladen(true);
  }, []);

  function speichern(wert: "granted" | "denied") {
    try {
      localStorage.setItem(CONSENT_KEY, wert);
    } catch {}
    setConsent(wert);
  }

  if (!geladen || consent !== null) {
    return consent === "granted" ? <AnalyticsScripts /> : null;
  }

  return (
    <>
      <div className="cookie-banner" role="dialog" aria-label="Cookie-Hinweis">
        <p>
          Wir nutzen Cookies und Google Analytics, um diese Seite zu verbessern.{" "}
          <Link href="/datenschutz">Mehr erfahren</Link>
        </p>
        <div className="cookie-banner__btns">
          <button type="button" className="btn btn--gold btn--klein" onClick={() => speichern("granted")}>
            Akzeptieren
          </button>
          <button type="button" className="btn btn--outline btn--klein" onClick={() => speichern("denied")}>
            Ablehnen
          </button>
        </div>
      </div>
    </>
  );
}

function AnalyticsScripts() {
  return (
    <>
      <Script src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`} strategy="afterInteractive" />
      <Script id="gtag-init" strategy="afterInteractive">
        {`window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${GA_ID}',{anonymize_ip:true});`}
      </Script>
    </>
  );
}
