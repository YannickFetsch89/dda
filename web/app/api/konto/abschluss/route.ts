// Abschluss des Profils (Plan 5.3, E16): { praeferenzen?, vorname, nachname, geburtsdatum, interessen_ok, sensibel_ok,
// widerspruch, geburtstagsmail_ok }. Jede Einwilligung bekommt eine Nachweiszeile (auch „nein“), handlung = 'abschlussseite'.
// Reihenfolge: Stammdaten zuerst (Pflicht, Altersprüfung) – liegt das Datum unter 16, bricht die Route ab, bevor
// etwas anderes gespeichert ist (Test 16.1). Dann (d), (a), (b), (c), danach praeferenzen (nur mit (a)) und
// onboarding_fertig_am (die Datenbank verlangt dafür alle Stammdaten).
// Wiederholung nach Fehler: Stammdaten nur, wenn sie sich ändern; einwilligung_setzen nur, wo sich etwas ändert oder
// noch keine Abschluss-Zeile existiert; praeferenzen werden immer erneut geschrieben, wenn (a) gilt.
import { hinweisCookie } from "@/lib/konto/cookies";
import { kontoDienstClient } from "@/lib/konto/clients";
import { MELDUNG, type EinwilligungArt } from "@/lib/konto/konfig";
import { einwilligungSetzen, stammdatenSetzen } from "@/lib/konto/einwilligungen";
import { weiterPruefen } from "@/lib/konto/pruefungen";
import { kontoAntwort, kontoRoute, ZEIT } from "@/lib/konto/route";
import { stammdatenAusBody } from "@/lib/konto/stammdaten";
import { vorliebenPruefen } from "@/lib/konto/vorlieben";

const TEILWEISE = "Konnte nicht vollständig gespeichert werden. Bitte nochmal versuchen.";

export const POST = kontoRoute(
  { anmeldung: true, json: true, aendernd: true, limit: { name: "abschluss", max: 30, fensterMs: ZEIT.STUNDE } },
  async (ctx) => {
    const p = ctx.profil!;
    const db = ctx.db!;
    const nutzerId = ctx.sitzung!.nutzerId;
    const dienst = kontoDienstClient();
    if (!dienst) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });

    const b = ctx.body;
    const stamm = stammdatenAusBody(b);
    if (stamm.fehler) return stamm.fehler;
    const s = stamm.daten;
    const interessenOk = b.interessen_ok === true;
    const sensibelOk = b.sensibel_ok === true;
    const widerspruch = b.widerspruch === true;
    const geburtstagsmailOk = b.geburtstagsmail_ok === true;
    const vorlieben = interessenOk && b.praeferenzen !== undefined ? vorliebenPruefen(b.praeferenzen) : null;
    if (interessenOk && b.praeferenzen !== undefined && !vorlieben) return kontoAntwort(400, { fehler: MELDUNG.ungueltig });

    // Welche Angaben haben schon eine Zeile von der Abschlussseite? (eigene Zeilen, RLS)
    const { data: zeilen, error: lesefehler } = await db.from("einwilligungen").select("art").eq("handlung", "abschlussseite");
    if (lesefehler) return kontoAntwort(503, { fehler: MELDUNG.nichtVerfuegbar });
    const schonDa = new Set((zeilen ?? []).map((z) => z.art as string));
    const gespeichert: string[] = [];
    const teilweise = () => kontoAntwort(500, { ok: false, gespeichert, fehler: TEILWEISE });

    // Stammdaten (Pflicht, Altersprüfung in der Datenbank)
    if (!(p.vorname === s.vorname && p.nachname === s.nachname && p.geburtsdatum === s.geburtsdatum)) {
      const r = await stammdatenSetzen(dienst, nutzerId, s);
      if (!r.ok) return teilweise();
      if (r.ergebnis === "unter_16") {
        ctx.ohneHinweis = true;
        ctx.setCookies.push(hinweisCookie("0", ctx.lokal));
        return kontoAntwort(200, { ok: false, gesperrt: true, meldung: MELDUNG.unter16 });
      }
      gespeichert.push("stammdaten");
    }

    // (d), (a), (b), (c) – (c) als analyse_erlaubt: ohne Widerspruch true (erst ab hier wird das Konto mitgezählt)
    const angaben: [EinwilligungArt, boolean, boolean][] = [
      ["geburtstagsmail", geburtstagsmailOk, p.geburtstagsmail],
      ["personalisierung", interessenOk, p.personalisierung],
      ["sensible_events", sensibelOk, p.sensible_events_erlaubt],
      ["analyse", !widerspruch, p.analyse_erlaubt],
    ];
    for (const [art, soll, ist] of angaben) {
      if (soll === ist && schonDa.has(art)) continue;
      const r = await einwilligungSetzen(dienst, nutzerId, art, soll, "abschlussseite");
      if (!r.ok) return teilweise();
      gespeichert.push(art);
    }

    // Interessen nur mit (a); (a) ist oben schon gesetzt, die Prüfbedingung in der Datenbank ist also erfüllt
    if (interessenOk && vorlieben) {
      const { error } = await db.from("profiles").update({ praeferenzen: vorlieben }).eq("id", nutzerId);
      if (error) return teilweise();
      gespeichert.push("praeferenzen");
    }

    if (!p.onboarding_fertig_am) {
      const { error } = await db.from("profiles").update({ onboarding_fertig_am: new Date().toISOString() }).eq("id", nutzerId);
      if (error) return teilweise();
    }
    return kontoAntwort(200, { ok: true, gespeichert, ziel: weiterPruefen(b.weiter) });
  },
);
