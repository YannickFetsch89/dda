"use client";
// Magazin-Beitrag: Entwurf bearbeiten (jedes Speichern prüft (a)–(i) neu), Vorschau, Veröffentlichen, Zurückziehen;
// veröffentlichte Beiträge nur per Korrektur mit sichtbarem Hinweis.
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { RUBRIK_NAME } from "@/lib/magazin";

interface Beitrag {
  id: string;
  slug: string;
  rubrik: string;
  status: "entwurf" | "in_pruefung" | "veroeffentlicht" | "zurueckgezogen";
  titel: string;
  seo_titel: string | null;
  teaser: string | null;
  inhalt_md: string;
  kurzfassung: string[] | null;
  faq: { frage: string; antwort: string }[] | null;
  hero_bild: string | null;
  hero_alt: string | null;
  hero_nachweis: string | null;
  gueltig_von: string | null;
  gueltig_bis: string | null;
  naechste_pruefung: string | null;
  korrektur_hinweis: string | null;
  veroeffentlicht_am: string | null;
  pruefung: { ergebnis?: string; punkte?: string[]; lauf?: string; zeitpunkt?: string } | null;
  ki_entwurf: { modell?: string; kosten_usd?: number } | null;
  event_ids: string[];
}

const KOPF = { "Content-Type": "application/json" };
const STATUS = { entwurf: "Entwurf (Prüfbefund offen)", in_pruefung: "Entwurf geprüft – kann veröffentlicht werden", veroeffentlicht: "veröffentlicht", zurueckgezogen: "zurückgezogen" } as const;

/** FAQ als Text: je Block erste Zeile Frage, Rest Antwort; Blöcke durch Leerzeile getrennt */
function faqText(faq: Beitrag["faq"]): string {
  return (faq ?? []).map((f) => `${f.frage}\n${f.antwort}`).join("\n\n");
}
function faqAus(text: string): { frage: string; antwort: string }[] {
  return text
    .split(/\n\s*\n/)
    .map((block) => block.trim().split("\n"))
    .filter((z) => z.length >= 2)
    .map(([frage, ...rest]) => ({ frage: frage.trim(), antwort: rest.join(" ").trim() }));
}

export function MagazinBearbeiten() {
  const { id } = useParams<{ id: string }>();
  const [b, setB] = useState<Beitrag | null>(null);
  const [meldung, setMeldung] = useState<{ art: "ok" | "fehler"; text: string } | null>(null);
  const [laeuft, setLaeuft] = useState(false);
  const [teaserLaenge, setTeaserLaenge] = useState(0);

  const laden = useCallback(async () => {
    const r = await fetch(`/api/admin/magazin/${id}`, { cache: "no-store" });
    if (r.status === 401) return window.location.assign("/admin/anmelden");
    const d = (await r.json().catch(() => ({}))) as { beitrag?: Beitrag; fehler?: string };
    if (!r.ok || !d.beitrag) return setMeldung({ art: "fehler", text: d.fehler ?? "Beitrag nicht gefunden." });
    setB(d.beitrag);
    setTeaserLaenge((d.beitrag.teaser ?? "").length);
  }, [id]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- einmaliges Laden beim Öffnen
    laden();
  }, [laden]);

  async function aktion(body: Record<string, unknown>, erfolg: string) {
    setLaeuft(true);
    setMeldung(null);
    const r = await fetch(`/api/admin/magazin/${id}`, { method: "POST", headers: KOPF, body: JSON.stringify(body) });
    const d = (await r.json().catch(() => ({}))) as { fehler?: string; pruefung?: { ergebnis: string } };
    setLaeuft(false);
    if (!r.ok) return setMeldung({ art: "fehler", text: d.fehler ?? "Hat nicht geklappt." });
    const zusatz = d.pruefung ? (d.pruefung.ergebnis === "gruen" ? " Prüfung grün – kann veröffentlicht werden." : " Prüfung rot – siehe Befunde oben.") : "";
    setMeldung({ art: "ok", text: erfolg + zusatz });
    laden();
  }

  function speichern(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const text = (n: string) => String(f.get(n) ?? "");
    aktion(
      {
        aktion: "speichern",
        felder: {
          titel: text("titel"),
          seo_titel: text("seo_titel"),
          teaser: text("teaser"),
          inhalt_md: text("inhalt_md"),
          kurzfassung: text("kurzfassung").split("\n").map((z) => z.trim()).filter(Boolean),
          faq: faqAus(text("faq")),
          hero_bild: text("hero_bild"),
          hero_alt: text("hero_alt"),
          hero_nachweis: text("hero_nachweis"),
          gueltig_von: text("gueltig_von"),
          gueltig_bis: text("gueltig_bis"),
          naechste_pruefung: text("naechste_pruefung"),
        },
      },
      "Gespeichert und geprüft.",
    );
  }

  function korrektur(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const inhalt = String(f.get("inhalt_md") ?? "");
    aktion({ aktion: "korrektur", hinweis: String(f.get("hinweis") ?? ""), inhalt_md: inhalt === b?.inhalt_md ? null : inhalt }, "Korrektur veröffentlicht.");
  }

  if (!b) return meldung ? <p className="admin-fehler">{meldung.text}</p> : <p className="admin-unterzeile">Wird geladen …</p>;
  const entwurf = b.status === "entwurf" || b.status === "in_pruefung";
  const gruen = b.pruefung?.ergebnis === "gruen";

  return (
    <>
      <p className="admin-unterzeile">
        <Link href="/admin/magazin">← Magazin</Link>
        {" · "}
        <a href={`/admin/magazin/${b.id}/vorschau`} target="_blank" rel="noreferrer">
          Vorschau
        </a>
        {b.status === "veroeffentlicht" && (
          <>
            {" · "}
            <a href={`https://diesdas.events/magazin/${b.slug}`} target="_blank" rel="noreferrer noopener">
              Live-Seite
            </a>
          </>
        )}
      </p>
      <h1>{b.titel}</h1>
      <p className="admin-unterzeile">
        {RUBRIK_NAME[b.rubrik as keyof typeof RUBRIK_NAME] ?? b.rubrik} · {STATUS[b.status]}
        {b.ki_entwurf?.modell ? ` · KI-Entwurf ${b.ki_entwurf.modell}${b.ki_entwurf.kosten_usd ? `, ${Number(b.ki_entwurf.kosten_usd).toFixed(2)} $` : ""}` : ""}
      </p>
      {meldung && <p className={meldung.art === "ok" ? "admin-karte" : "admin-fehler"} role="status">{meldung.text}</p>}

      <section className={`admin-karte admin-pruefung admin-pruefung--${gruen ? "gruen" : "rot"}`}>
        <h2>Prüfung: {b.pruefung?.ergebnis === "gruen" ? "grün" : b.pruefung?.ergebnis === "rot" ? "rot" : "noch nicht geprüft"}</h2>
        {!!b.pruefung?.punkte?.length && (
          <ul>
            {b.pruefung.punkte.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        )}
        <div className="admin-aktionen">
          {entwurf && (
            <button type="button" className="admin-knopf admin-knopf--leise" disabled={laeuft} onClick={() => aktion({ aktion: "pruefen" }, "Neu geprüft.")}>
              Neu prüfen
            </button>
          )}
          {b.status === "in_pruefung" && gruen && (
            <button
              type="button"
              className="admin-knopf"
              disabled={laeuft}
              onClick={() => window.confirm(`„${b.titel}“ jetzt veröffentlichen?`) && aktion({ aktion: "veroeffentlichen" }, "Veröffentlicht.")}
            >
              Veröffentlichen
            </button>
          )}
          {b.status !== "zurueckgezogen" && (
            <button
              type="button"
              className="admin-knopf admin-knopf--leise"
              disabled={laeuft}
              onClick={() => window.confirm(b.status === "veroeffentlicht" ? "Beitrag von der Website nehmen?" : "Entwurf verwerfen?") && aktion({ aktion: "zurueckziehen" }, "Zurückgezogen.")}
            >
              {b.status === "veroeffentlicht" ? "Zurückziehen" : "Verwerfen"}
            </button>
          )}
        </div>
      </section>

      {entwurf && (
        <form className="admin-karte admin-formular" onSubmit={speichern} key={JSON.stringify(b)}>
          <label className="admin-feld admin-feld--breit">
            Titel (höchstens 90 Zeichen)
            <input name="titel" defaultValue={b.titel} maxLength={90} required />
          </label>
          <label className="admin-feld">
            SEO-Titel (optional, höchstens 60)
            <input name="seo_titel" defaultValue={b.seo_titel ?? ""} maxLength={60} />
          </label>
          <label className="admin-feld">
            Zeitraum von / bis
            <span className="admin-filterleiste">
              <input name="gueltig_von" type="date" defaultValue={b.gueltig_von ?? ""} />
              <input name="gueltig_bis" type="date" defaultValue={b.gueltig_bis ?? ""} />
            </span>
          </label>
          <label className="admin-feld admin-feld--breit">
            Teaser ({teaserLaenge} Zeichen, 80–160)
            <textarea name="teaser" defaultValue={b.teaser ?? ""} rows={2} onChange={(x) => setTeaserLaenge(x.target.value.trim().length)} />
          </label>
          <label className="admin-feld admin-feld--breit">
            Auf einen Blick (3–5 Punkte, je Zeile einer)
            <textarea name="kurzfassung" defaultValue={(b.kurzfassung ?? []).join("\n")} rows={5} />
          </label>
          <label className="admin-feld">
            Aufmacherbild (Pfad)
            <input name="hero_bild" defaultValue={b.hero_bild ?? ""} placeholder="/magazin-bilder/… oder /fallback/…" />
          </label>
          <label className="admin-feld">
            Alt-Text
            <input name="hero_alt" defaultValue={b.hero_alt ?? ""} />
          </label>
          <label className="admin-feld">
            Bildnachweis
            <input name="hero_nachweis" defaultValue={b.hero_nachweis ?? ""} />
          </label>
          <label className="admin-feld">
            Nächste Überarbeitung (optional)
            <input name="naechste_pruefung" type="date" defaultValue={b.naechste_pruefung ?? ""} />
          </label>
          <label className="admin-feld admin-feld--breit">
            Text (Markdown). Events tauschen: Zeile {"{{event:<id>}}"} ändern, die Event-Liste folgt automatisch.
            <textarea name="inhalt_md" defaultValue={b.inhalt_md} rows={24} className="admin-code" />
          </label>
          <label className="admin-feld admin-feld--breit">
            FAQ (optional; je Frage ein Block: erste Zeile Frage, darunter Antwort, Blöcke durch Leerzeile getrennt)
            <textarea name="faq" defaultValue={faqText(b.faq)} rows={6} />
          </label>
          <div className="admin-feld--breit">
            <button className="admin-knopf" type="submit" disabled={laeuft}>
              {laeuft ? "Speichert …" : "Speichern und prüfen"}
            </button>
          </div>
        </form>
      )}

      {b.status === "veroeffentlicht" && (
        <form className="admin-karte admin-formular" onSubmit={korrektur}>
          <h2 className="admin-feld--breit">Korrektur</h2>
          <p className="admin-feld--breit">Veröffentlichte Beiträge ändern nur mit sichtbarem Korrekturhinweis. Er erscheint unter dem Beitrag.</p>
          {b.korrektur_hinweis && <p className="admin-feld--breit"><small>Bisheriger Hinweis: {b.korrektur_hinweis}</small></p>}
          <label className="admin-feld admin-feld--breit">
            Korrekturhinweis (5–500 Zeichen)
            <input name="hinweis" required minLength={5} maxLength={500} placeholder="z. B. „Die Lesung am Mittwoch wurde abgesagt; wir haben den Hinweis entfernt.“" />
          </label>
          <label className="admin-feld admin-feld--breit">
            Text (Markdown)
            <textarea name="inhalt_md" defaultValue={b.inhalt_md} rows={20} className="admin-code" />
          </label>
          <div className="admin-feld--breit">
            <button className="admin-knopf" type="submit" disabled={laeuft}>
              Korrektur veröffentlichen
            </button>
          </div>
        </form>
      )}
    </>
  );
}
