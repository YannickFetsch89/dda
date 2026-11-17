"use client";
// Interessen-Fragebogen und Abschlussseite (Plan 5.3, 8). Seiteninhalt, kein Dialog. Bedienmuster und Klassen
// wie components/fragebogen.tsx (der selbst unverändert bleibt).
// Die Antworten bleiben bis „Fertig“ nur im Zustand dieser Komponente – kein localStorage, keine Anfrage.
import { useState } from "react";
import { Icon } from "./karten";
import { Meldung } from "./konto";
import { TEXT } from "@/lib/konto/texte";
import type { CSSProperties } from "react";

export interface FragebogenDaten {
  kategorien: { slug: string; name: string; icon: string; stil: CSSProperties; anzahl: number; unter: { slug: string; name: string }[] }[];
  bezirke: { name: string; stadtteile: { slug: string; name: string }[] }[];
  nachbarn: { slug: string; name: string }[];
}

export interface Antworten {
  kategorien: string[];
  unterkategorien: string[];
  stadtteile: string[];
  merkmale: string[];
  orte: string[];
}
export const KEINE: Antworten = { kategorien: [], unterkategorien: [], stadtteile: [], merkmale: [], orte: [] };

const MERKMALE = [
  { slug: "kostenlos", name: "Gern kostenlos", icon: "savings" },
  { slug: "mit-kindern", name: "Mit Kindern unterwegs", icon: "family_restroom" },
  { slug: "abends", name: "Eher abends", icon: "dark_mode" },
  { slug: "tagsueber", name: "Eher tagsüber", icon: "light_mode" },
  { slug: "wochenende", name: "Am liebsten am Wochenende", icon: "weekend" },
];
const ORTE = [
  { slug: "restaurants-cafes", name: "Restaurants & Cafés", icon: "restaurant" },
  { slug: "kneipen-bars", name: "Kneipen & Bars", icon: "sports_bar" },
  { slug: "clubs", name: "Clubs", icon: "nightlife" },
  { slug: "spielplaetze", name: "Spielplätze", icon: "toys" },
];

type Schritt = "kategorien" | "unter" | "ort" | "merkmale" | "ueber" | "abschluss";

export interface AbschlussWerte {
  interessen_ok: boolean;
  sensibel_ok: boolean;
  widerspruch: boolean;
  geburtstagsmail_ok: boolean;
  // Pflichtangaben (E16), Schritt „Über dich“ nach den Interessen
  vorname: string;
  nachname: string;
  geburtsdatum: string;
}

/** Heute als YYYY-MM-DD in Ortszeit (Obergrenze fürs Datumsfeld) */
const heute = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

/**
 * Fragebogen. modus „onboarding“: nach den Interessen der Schritt „Über dich“ (Name, Geburtsdatum, Pflicht, E16),
 * dann alle Einwilligungen (a)–(d). modus „interessen“ (im Konto ändern):
 * endet mit Einwilligung (a), wenn sie noch nicht gilt, sonst speichert er direkt.
 */
export function InteressenFragebogen({
  daten, start = KEINE, stammStart, modus, personalisierungGilt, speichern, fehler, sendet,
}: {
  daten: FragebogenDaten;
  start?: Antworten;
  stammStart?: { vorname: string; nachname: string; geburtsdatum: string };
  modus: "onboarding" | "interessen";
  personalisierungGilt: boolean;
  speichern: (antworten: Antworten | null, werte: AbschlussWerte) => void;
  fehler: string | null;
  sendet: boolean;
}) {
  const [a, setA] = useState<Antworten>(start);
  const [verworfen, setVerworfen] = useState(false);
  const [schritt, setSchritt] = useState<Schritt>("kategorien");
  const [werte, setWerte] = useState<AbschlussWerte>({
    interessen_ok: false, sensibel_ok: false, widerspruch: false, geburtstagsmail_ok: false,
    vorname: stammStart?.vorname ?? "", nachname: stammStart?.nachname ?? "", geburtsdatum: stammStart?.geburtsdatum ?? "",
  });
  const stammFertig = !!(werte.vorname.trim() && werte.nachname.trim() && werte.geburtsdatum);

  const mitUnter = a.kategorien.some((k) => daten.kategorien.find((x) => x.slug === k)?.unter.length);
  const schritte: Schritt[] = [
    "kategorien", ...(mitUnter ? (["unter"] as Schritt[]) : []), "ort", "merkmale",
    ...(modus === "onboarding" ? (["ueber"] as Schritt[]) : []), "abschluss",
  ];
  const nummer = schritte.indexOf(schritt) + 1;
  const weiter = () => setSchritt(schritte[Math.min(schritte.length - 1, nummer)]);
  const zurueck = () => setSchritt(schritte[Math.max(0, nummer - 2)]);
  const umschalten = (liste: string[], w: string) => (liste.includes(w) ? liste.filter((x) => x !== w) : [...liste, w]);
  const ohneInteressen = () => {
    setA(KEINE);
    setVerworfen(true);
    setSchritt(modus === "onboarding" ? "ueber" : "abschluss");
  };
  const hatAntworten = !verworfen && Object.values(a).some((l) => l.length);

  // Im Konto mit schon erteilter Einwilligung (a): kein Abschluss nötig, gleich speichern
  if (schritt === "abschluss" && modus === "interessen" && personalisierungGilt) {
    return (
      <div className="fb__inhalt konto-fb">
        <h2 className="d">Interessen speichern?</h2>
        {fehler && <Meldung art="fehler">{fehler}</Meldung>}
        <div className="fb__fuss">
          <button type="button" className="fb__zurueck" onClick={zurueck}><Icon name="arrow_back" />Zurück</button>
          <button type="button" className="fb__weiter" disabled={sendet} onClick={() => speichern(a, { ...werte, interessen_ok: true })}>
            Speichern<Icon name="check" />
          </button>
        </div>
      </div>
    );
  }

  const chip = (an: boolean, onClick: () => void, inhalt: React.ReactNode, key?: string) => (
    <button key={key} type="button" className={`gd-chip gd-chip--gross ${an ? "gd-chip--an" : ""}`} aria-pressed={an} onClick={onClick}>
      {an && <Icon name="check" />}
      {inhalt}
    </button>
  );
  const fuss = (
    <div className="fb__fuss konto-fb__fuss">
      <button type="button" className="fb__weiter" onClick={weiter}>Weiter<Icon name="arrow_forward" /></button>
      <button type="button" className="link konto-textknopf" onClick={ohneInteressen}>Ohne Interessen weiter</button>
    </div>
  );

  return (
    <div className="konto-fb">
      <div className="fb__kopf">
        {nummer > 1 ? (
          <button type="button" className="fb__zurueck" onClick={zurueck}><Icon name="arrow_back" />Zurück</button>
        ) : <span />}
        <span className="fb__schritt" aria-hidden>
          {schritt === "abschluss" ? "Fast fertig" : `Frage ${nummer} von ${schritte.length - 1}`}
        </span>
        <span />
      </div>
      <div className="fb__fortschritt" aria-hidden><span style={{ width: `${(nummer / schritte.length) * 100}%` }} /></div>

      {schritt === "kategorien" && (
        <div className="fb__inhalt">
          {modus === "onboarding" && (
            <div className="konto-fb__einleitung">
              <h2 className="d">{TEXT.einleitung.titel}</h2>
              <p className="fb__hinweis">{TEXT.einleitung.text}</p>
            </div>
          )}
          <h2 className="d" id="fb-frage">Worauf hast du Lust?</h2>
          <div className="fb__chips">
            {chip(!a.kategorien.length, () => setA({ ...a, kategorien: [], unterkategorien: [] }), <><Icon name="done_all" />Von allem etwas</>)}
          </div>
          <div className="fb__karten">
            {daten.kategorien.map((k) => {
              const an = a.kategorien.includes(k.slug);
              return (
                <button key={k.slug} type="button" className={`fb__karte konto-fb__kat ${an ? "is-an" : ""}`} style={k.stil} aria-pressed={an}
                  onClick={() => setA({
                    ...a,
                    kategorien: umschalten(a.kategorien, k.slug),
                    unterkategorien: an ? a.unterkategorien.filter((u) => !u.startsWith(`${k.slug}/`)) : a.unterkategorien,
                  })}>
                  <Icon name={k.icon} />
                  <b>{k.name}</b>
                  <span className="fb__zahl">{k.anzahl.toLocaleString("de-DE")} Events in 30 Tagen</span>
                </button>
              );
            })}
          </div>
          {fuss}
        </div>
      )}

      {schritt === "unter" && (
        <div className="fb__inhalt">
          <h2 className="d" id="fb-frage">Was genau?</h2>
          <p className="fb__hinweis">Nichts gewählt heißt: alles aus diesen Kategorien.</p>
          {daten.kategorien.filter((k) => a.kategorien.includes(k.slug) && k.unter.length).map((k) => (
            <div key={k.slug} className="konto-fb__gruppe">
              <b>{k.name}</b>
              <div className="fb__chips">
                {k.unter.map((u) => {
                  const wert = `${k.slug}/${u.slug}`;
                  return chip(a.unterkategorien.includes(wert), () => setA({ ...a, unterkategorien: umschalten(a.unterkategorien, wert) }), u.name, wert);
                })}
              </div>
            </div>
          ))}
          {fuss}
        </div>
      )}

      {schritt === "ort" && (
        <div className="fb__inhalt">
          <h2 className="d" id="fb-frage">Wo bist du unterwegs?</h2>
          <div className="fb__chips">
            {chip(!a.stadtteile.length, () => setA({ ...a, stadtteile: [] }), <><Icon name="explore" />Überall in Düsseldorf</>)}
          </div>
          {[...daten.bezirke, { name: "Nachbarstädte", stadtteile: daten.nachbarn }].map((b) => (
            <div key={b.name} className="konto-fb__gruppe">
              <b>{b.name}</b>
              <div className="fb__chips">
                {b.stadtteile.map((s) => chip(a.stadtteile.includes(s.slug), () => setA({ ...a, stadtteile: umschalten(a.stadtteile, s.slug) }), s.name, s.slug))}
              </div>
            </div>
          ))}
          {fuss}
        </div>
      )}

      {schritt === "merkmale" && (
        <div className="fb__inhalt">
          <h2 className="d" id="fb-frage">Was passt zu dir?</h2>
          <div className="fb__chips">
            {MERKMALE.map((m) => chip(a.merkmale.includes(m.slug), () => setA({ ...a, merkmale: umschalten(a.merkmale, m.slug) }), <><Icon name={m.icon} />{m.name}</>, m.slug))}
          </div>
          <b>Auch Orte entdecken</b>
          <div className="fb__chips">
            {ORTE.map((o) => chip(a.orte.includes(o.slug), () => setA({ ...a, orte: umschalten(a.orte, o.slug) }), <><Icon name={o.icon} />{o.name}</>, o.slug))}
          </div>
          {fuss}
        </div>
      )}

      {schritt === "ueber" && (
        <form
          className="fb__inhalt formular konto-abschluss"
          onSubmit={(e) => {
            e.preventDefault();
            if (stammFertig) weiter();
          }}
        >
          <h2 className="d" id="fb-frage">{TEXT.stammdaten.titel}</h2>
          <div className="konto-stamm">
            <div className="formular__feld">
              <label className="formular__label" htmlFor="vorname">Vorname</label>
              <input id="vorname" type="text" autoComplete="given-name" maxLength={60} required value={werte.vorname}
                onChange={(e) => setWerte({ ...werte, vorname: e.target.value })} />
            </div>
            <div className="formular__feld">
              <label className="formular__label" htmlFor="nachname">Nachname</label>
              <input id="nachname" type="text" autoComplete="family-name" maxLength={60} required value={werte.nachname}
                onChange={(e) => setWerte({ ...werte, nachname: e.target.value })} />
            </div>
          </div>
          <div className="formular__feld">
            <label className="formular__label" htmlFor="geburtsdatum">Geburtsdatum</label>
            <input id="geburtsdatum" type="date" autoComplete="bday" min="1900-01-01" max={heute()} required value={werte.geburtsdatum}
              onChange={(e) => setWerte({ ...werte, geburtsdatum: e.target.value })} />
          </div>
          <p className="formular__hinweis">
            {TEXT.stammdaten.text} Mehr dazu in der <a href="/datenschutz#konto">Datenschutzerklärung</a>.
          </p>
          <div className="fb__fuss">
            <button type="submit" className="fb__weiter" disabled={!stammFertig}>Weiter<Icon name="arrow_forward" /></button>
          </div>
        </form>
      )}

      {schritt === "abschluss" && (
        <form
          className="fb__inhalt formular konto-abschluss"
          onSubmit={(e) => {
            e.preventDefault();
            // Antworten gehen nur mit Häkchen (a) mit (Plan 5.3)
            speichern(werte.interessen_ok && hatAntworten ? a : null, werte);
          }}
        >
          <h2 className="d" id="fb-frage">Fast fertig</h2>
          {hatAntworten && (
            <label className="formular__check">
              <input type="checkbox" checked={werte.interessen_ok} onChange={(e) => setWerte({ ...werte, interessen_ok: e.target.checked })} />
              <span>{TEXT.personalisierung}</span>
            </label>
          )}
          {modus === "onboarding" && (
            <>
              <div className="konto-kasten">
                <p><b>Datenschutz ist uns hier besonders wichtig.</b> {TEXT.sensibelErklaerung}</p>
                <label className="formular__check">
                  <input type="checkbox" checked={werte.sensibel_ok} onChange={(e) => setWerte({ ...werte, sensibel_ok: e.target.checked })} />
                  <span>{TEXT.sensibel}</span>
                </label>
              </div>
              <div className="konto-kasten konto-kasten--hinweis">
                <p><b>Dein Widerspruchsrecht:</b> {TEXT.widerspruchErklaerung}</p>
                <label className="formular__check">
                  <input type="checkbox" checked={werte.widerspruch} onChange={(e) => setWerte({ ...werte, widerspruch: e.target.checked })} />
                  <span>{TEXT.widerspruch}</span>
                </label>
              </div>
              <div className="konto-kasten">
                <label className="formular__check">
                  <input type="checkbox" checked={werte.geburtstagsmail_ok} onChange={(e) => setWerte({ ...werte, geburtstagsmail_ok: e.target.checked })} />
                  <span>{TEXT.geburtstag}</span>
                </label>
              </div>
            </>
          )}
          {modus === "interessen" && !hatAntworten && <p className="fb__hinweis">Du hast keine Interessen ausgewählt.</p>}
          {fehler && <Meldung art="fehler">{fehler}</Meldung>}
          <div className="fb__fuss">
            <button type="submit" className="fb__weiter" disabled={sendet || (modus === "onboarding" && !stammFertig)}>
              Fertig<Icon name="check" />
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
