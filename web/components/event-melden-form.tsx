"use client";
// Formular „Event melden“ – sendet an /api/event-melden (multipart). Bilder werden vorher im Browser
// verkleinert (max. 1600 px, JPEG), damit der Upload klein bleibt und kein Server-Limit reißt.
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

export interface KategorieOption {
  wert: string; // DB-Wert (z.B. "family")
  name: string;
}

type Felder = Record<string, string>;

const MAX_KANTE = 1600;
const ZIEL_BYTES = 1.5 * 1024 * 1024;
const MAX_PIXEL = 50_000_000; // wie auf dem Server – größere Bilder würden beim Dekodieren den Speicher sprengen

/** Abmessungen lesen, ohne das ganze Bild zu dekodieren (der Browser liest dafür nur den Dateikopf). */
function bildMasse(datei: File): Promise<{ breite: number; hoehe: number }> {
  return new Promise((fertig, fehler) => {
    const url = URL.createObjectURL(datei);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      fertig({ breite: img.naturalWidth, hoehe: img.naturalHeight });
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      fehler(new Error("Bild nicht lesbar"));
    };
    img.src = url;
  });
}

/** Bild im Browser verkleinern und als JPEG neu kodieren (weißer Hintergrund für Transparenz). */
async function bildVerkleinern(datei: File): Promise<Blob> {
  const { breite, hoehe } = await bildMasse(datei);
  if (!breite || !hoehe || breite * hoehe > MAX_PIXEL) throw new Error("Bild zu groß");
  const faktor = Math.min(1, MAX_KANTE / Math.max(breite, hoehe));
  // Schon beim Dekodieren verkleinern (wo der Browser es kann) – spart Speicher bei großen Fotos
  const bitmap = await createImageBitmap(datei, {
    resizeWidth: Math.max(1, Math.round(breite * faktor)),
    resizeHeight: Math.max(1, Math.round(hoehe * faktor)),
    resizeQuality: "high",
  });
  const canvas = document.createElement("canvas");
  canvas.width = bitmap.width;
  canvas.height = bitmap.height;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Bild konnte nicht verarbeitet werden.");
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  for (const qualitaet of [0.85, 0.75, 0.6]) {
    const blob = await new Promise<Blob | null>((r) => canvas.toBlob(r, "image/jpeg", qualitaet));
    if (blob && (blob.size <= ZIEL_BYTES || qualitaet === 0.6)) return blob;
  }
  throw new Error("Bild konnte nicht verarbeitet werden.");
}

function heuteLokal(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function Fehler({ felder, name }: { felder: Felder; name: string }) {
  return felder[name] ? (
    <span className="formular__fehler" id={`fehler-${name}`} role="alert">
      {felder[name]}
    </span>
  ) : null;
}

export function EventMeldenForm({ kategorien }: { kategorien: KategorieOption[] }) {
  const formRef = useRef<HTMLFormElement>(null);
  const [zustand, setZustand] = useState<"bereit" | "sendet" | "fertig">("bereit");
  const [fehler, setFehler] = useState<string | null>(null);
  const [felder, setFelder] = useState<Felder>({});
  const [bild, setBild] = useState<{ blob: Blob; vorschau: string } | null>(null);
  const [bildInfo, setBildInfo] = useState<string | null>(null);
  const [kostenlos, setKostenlos] = useState(false);
  const [mehrtaegig, setMehrtaegig] = useState(false);
  const auswahlNr = useRef(0); // nur das Ergebnis der letzten Bildauswahl übernehmen

  // Vorschau-URL freigeben, wenn sie ersetzt wird oder das Formular verschwindet
  useEffect(() => {
    if (!bild) return;
    return () => URL.revokeObjectURL(bild.vorschau);
  }, [bild]);

  const fehlerAttr = (name: string) =>
    felder[name] ? { "aria-invalid": true as const, "aria-describedby": `fehler-${name}` } : {};

  async function bildGewaehlt(datei: File | undefined) {
    setFelder((f) => Object.fromEntries(Object.entries(f).filter(([k]) => k !== "bild")));
    const nr = ++auswahlNr.current;
    setBild(null);
    setBildInfo(null);
    if (!datei) return;
    if (!/^image\/(jpeg|png|webp)$/.test(datei.type)) {
      setFelder((f) => ({ ...f, bild: "Bitte wähle ein JPG-, PNG- oder WebP-Bild." }));
      return;
    }
    if (datei.size > 25 * 1024 * 1024) {
      setFelder((f) => ({ ...f, bild: "Das Bild ist zu groß (max. 25 MB vor dem Verkleinern)." }));
      return;
    }
    try {
      setBildInfo("Bild wird vorbereitet…");
      const blob = await bildVerkleinern(datei);
      if (nr !== auswahlNr.current) return; // inzwischen wurde ein anderes Bild gewählt
      setBild({ blob, vorschau: URL.createObjectURL(blob) });
      setBildInfo(`${Math.round(blob.size / 1024)} KB, bereit zum Hochladen`);
    } catch (err) {
      if (nr !== auswahlNr.current) return;
      setBildInfo(null);
      const zuGross = err instanceof Error && err.message === "Bild zu groß";
      setFelder((f) => ({
        ...f,
        bild: zuGross
          ? "Das Bild hat zu viele Pixel (max. 50 Megapixel). Bitte verkleinere es vorher."
          : "Das Bild konnte nicht gelesen werden. Bitte versuch ein anderes.",
      }));
    }
  }

  async function absenden(ev: React.FormEvent<HTMLFormElement>) {
    ev.preventDefault();
    const daten = new FormData(ev.currentTarget);
    daten.delete("bild_datei");
    if (bild) daten.set("bild", bild.blob, "meldung.jpg");
    setZustand("sendet");
    setFehler(null);
    setFelder({});
    try {
      const r = await fetch("/api/event-melden", { method: "POST", body: daten });
      const antwort = (await r.json().catch(() => ({}))) as { fehler?: string; felder?: Felder };
      if (!r.ok) {
        setFelder(antwort.felder ?? {});
        setFehler(antwort.fehler ?? "Das hat leider nicht geklappt.");
        setZustand("bereit");
        // Zum ersten markierten Feld springen
        requestAnimationFrame(() => {
          const erstes = formRef.current?.querySelector<HTMLElement>("[aria-invalid='true'], .formular__fehler");
          erstes?.scrollIntoView({ block: "center", behavior: "smooth" });
          if (erstes instanceof HTMLInputElement || erstes instanceof HTMLTextAreaElement || erstes instanceof HTMLSelectElement) erstes.focus({ preventScroll: true });
        });
        return;
      }
      setBild(null); // gibt die Vorschau-URL frei (useEffect oben)
      setZustand("fertig");
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch {
      setFehler("Keine Verbindung. Bitte prüfe deine Internetverbindung und versuch es noch einmal.");
      setZustand("bereit");
    }
  }

  if (zustand === "fertig") {
    return (
      <div className="formular__danke" role="status">
        <span className="icon" aria-hidden>check_circle</span>
        <h2 className="d">Danke für deine Meldung!</h2>
        <p>Wir schauen uns dein Event an und schalten es nach der Prüfung frei – meist innerhalb von ein bis zwei Tagen. Bei Rückfragen melden wir uns per E-Mail.</p>
        <div className="formular__aktionen">
          <button type="button" className="btn btn--gold" onClick={() => { setZustand("bereit"); setKostenlos(false); setMehrtaegig(false); setBildInfo(null); }}>
            Weiteres Event melden
          </button>
          <Link href="/" className="btn btn--outline">Zur Startseite</Link>
        </div>
      </div>
    );
  }

  return (
    <form ref={formRef} className="formular" onSubmit={absenden} noValidate>
      {fehler && <p className="formular__meldung" role="alert">{fehler}</p>}

      <fieldset className="formular__gruppe">
        <legend className="d">Das Event</legend>
        <label className="formular__feld">
          <span className="formular__label">Titel *</span>
          <input name="titel" required minLength={3} maxLength={150} placeholder="z.B. Flohmarkt im Hofgarten" {...fehlerAttr("titel")} />
          <Fehler felder={felder} name="titel" />
        </label>
        <label className="formular__feld">
          <span className="formular__label">Kategorie *</span>
          <select name="kategorie" required defaultValue="" {...fehlerAttr("kategorie")}>
            <option value="" disabled>Bitte wählen</option>
            {kategorien.map((k) => <option key={k.wert} value={k.wert}>{k.name}</option>)}
          </select>
          <Fehler felder={felder} name="kategorie" />
        </label>
        <label className="formular__feld">
          <span className="formular__label">Beschreibung *</span>
          <textarea name="beschreibung" required minLength={20} maxLength={2000} rows={6}
            placeholder="Was erwartet die Besucher? Programm, Besonderheiten, für wen ist es geeignet?" {...fehlerAttr("beschreibung")} />
          <span className="formular__hinweis">20–2.000 Zeichen. Wir kürzen den Text bei Bedarf für die Website.</span>
          <Fehler felder={felder} name="beschreibung" />
        </label>
      </fieldset>

      <fieldset className="formular__gruppe">
        <legend className="d">Wann?</legend>
        <div className="formular__reihe">
          <label className="formular__feld">
            <span className="formular__label">{mehrtaegig ? "Von *" : "Datum *"}</span>
            <input type="date" name="datum" required onFocus={(e) => { e.currentTarget.min = heuteLokal(); }} {...fehlerAttr("datum")} />
            <Fehler felder={felder} name="datum" />
          </label>
          {mehrtaegig && (
            <label className="formular__feld">
              <span className="formular__label">Bis</span>
              <input type="date" name="datum_bis" onFocus={(e) => { e.currentTarget.min = heuteLokal(); }} {...fehlerAttr("datum_bis")} />
              <Fehler felder={felder} name="datum_bis" />
            </label>
          )}
          <label className="formular__feld">
            <span className="formular__label">Beginn</span>
            <input type="time" name="uhrzeit" {...fehlerAttr("uhrzeit")} />
            <Fehler felder={felder} name="uhrzeit" />
          </label>
        </div>
        <label className="formular__check">
          <input type="checkbox" checked={mehrtaegig} onChange={(e) => setMehrtaegig(e.target.checked)} />
          <span>Das Event geht über mehrere Tage (z.B. Ausstellung, Festival)</span>
        </label>
      </fieldset>

      <fieldset className="formular__gruppe">
        <legend className="d">Wo?</legend>
        <label className="formular__feld">
          <span className="formular__label">Veranstaltungsort *</span>
          <input name="ort" required minLength={2} maxLength={150} placeholder="z.B. zakk, Kunstpalast, Rheinwiesen" {...fehlerAttr("ort")} />
          <Fehler felder={felder} name="ort" />
        </label>
        <label className="formular__feld">
          <span className="formular__label">Adresse</span>
          <input name="adresse" maxLength={200} placeholder="Straße Hausnummer, PLZ Düsseldorf" autoComplete="off" />
        </label>
      </fieldset>

      <fieldset className="formular__gruppe">
        <legend className="d">Eintritt &amp; Tickets</legend>
        <label className="formular__check">
          <input type="checkbox" name="kostenlos" value="ja" checked={kostenlos} onChange={(e) => setKostenlos(e.target.checked)} />
          <span>Eintritt frei</span>
        </label>
        {!kostenlos && (
          <label className="formular__feld">
            <span className="formular__label">Preis</span>
            <input name="preis" maxLength={80} placeholder="z.B. ab 12 €, VVK 15 € / AK 18 €" />
          </label>
        )}
        <label className="formular__feld">
          <span className="formular__label">Link zum Event oder zu Tickets</span>
          <input type="url" name="link" maxLength={500} placeholder="https://…" inputMode="url" {...fehlerAttr("link")} />
          <Fehler felder={felder} name="link" />
        </label>
      </fieldset>

      <fieldset className="formular__gruppe">
        <legend className="d">Bild</legend>
        <label className="formular__datei">
          <input type="file" name="bild_datei" accept="image/jpeg,image/png,image/webp"
            onChange={(e) => bildGewaehlt(e.target.files?.[0])} {...fehlerAttr("bild")} />
          <span className="icon" aria-hidden>add_photo_alternate</span>
          <span>{bild ? "Anderes Bild wählen" : "Bild auswählen (JPG, PNG oder WebP)"}</span>
        </label>
        {bildInfo && <span className="formular__hinweis">{bildInfo}</span>}
        <Fehler felder={felder} name="bild" />
        {bild && (
          // eslint-disable-next-line @next/next/no-img-element -- lokale Vorschau (Blob-URL)
          <img src={bild.vorschau} alt="Vorschau des ausgewählten Bildes" className="formular__vorschau" />
        )}
        {bild && (
          <label className="formular__check">
            <input type="checkbox" name="bild_rechte" value="ja" {...fehlerAttr("bild_rechte")} />
            <span>Ich darf dieses Bild verwenden und erlaube dies.das.düsseldorf, es zusammen mit dem Event zu veröffentlichen. *</span>
          </label>
        )}
        <Fehler felder={felder} name="bild_rechte" />
        <span className="formular__hinweis">Am besten im Querformat. Ohne Bild verwenden wir ein passendes Symbolbild.</span>
      </fieldset>

      <fieldset className="formular__gruppe">
        <legend className="d">Kontakt für Rückfragen</legend>
        <span className="formular__hinweis">Wird nicht veröffentlicht.</span>
        <div className="formular__reihe">
          <label className="formular__feld">
            <span className="formular__label">Name</span>
            <input name="kontakt_name" maxLength={100} autoComplete="name" />
          </label>
          <label className="formular__feld">
            <span className="formular__label">E-Mail *</span>
            <input type="email" name="kontakt_email" required maxLength={254} autoComplete="email" {...fehlerAttr("kontakt_email")} />
            <Fehler felder={felder} name="kontakt_email" />
          </label>
        </div>
        <div className="formular__optionen" role="radiogroup" aria-label="Ich bin">
          <label className="formular__check"><input type="radio" name="kontakt_rolle" value="veranstalter" defaultChecked /><span>Ich veranstalte das Event</span></label>
          <label className="formular__check"><input type="radio" name="kontakt_rolle" value="besucher" /><span>Ich habe einen Tipp</span></label>
        </div>
        <label className="formular__feld">
          <span className="formular__label">Anmerkung an die Redaktion</span>
          <textarea name="anmerkung" maxLength={1000} rows={3} placeholder="Optional" />
        </label>
      </fieldset>

      {/* Honeypot gegen Bots – für Menschen unsichtbar */}
      <input type="text" name="website" tabIndex={-1} autoComplete="off" aria-hidden className="honigtopf" />

      <label className="formular__check">
        <input type="checkbox" name="datenschutz" value="ja" required {...fehlerAttr("datenschutz")} />
        <span>
          Ich habe die <Link href="/datenschutz#event-melden" target="_blank">Datenschutzhinweise</Link> gelesen. Meine Angaben
          werden zur Prüfung und Veröffentlichung des Events gespeichert. *
        </span>
      </label>
      <Fehler felder={felder} name="datenschutz" />

      <div className="formular__aktionen">
        <button type="submit" className="btn btn--gold btn--gross" disabled={zustand === "sendet"}>
          {zustand === "sendet" ? "Wird gesendet…" : "Event zur Prüfung senden"}
        </button>
        <span className="formular__hinweis">* Pflichtfeld. Wir prüfen jede Meldung, bevor sie erscheint.</span>
      </div>
    </form>
  );
}
