// Tests Merkliste mit Konto – reine Logik (Plan 16.1: Store, Übernahme, Darstellung E9).
import { describe, expect, it } from "vitest";
import {
  geraetelisteNachUebernahme, herzAntwortEinordnen, herzImKonto, merklisteAufteilen, offeneLoeschungen, sichtbareListe,
  uebernahmeEntscheiden, warteschlangeAnwenden, type UebernahmeAntwort, type WarteEintrag,
} from "@/lib/konto/merk-logik";

const antwort = (teil: Partial<UebernahmeAntwort>): UebernahmeAntwort => ({
  konto: [], umgeschrieben: [], ungueltig: [], nicht_uebernommen: [], bleiben_auf_geraet: [], uebernommen: 0, vollstaendig: true, ...teil,
});
const e = (op: "merken" | "entfernen", id: string, zeit = 0): WarteEintrag => ({ op, id, zeit });

describe("Store-Quellen", () => {
  it("abgemeldet: Geräteliste ∪ nur-Gerät; angemeldet: Spiegel mit Warteschlange ∪ nur-Gerät", () => {
    expect(sichtbareListe({ kontomodus: false, geraet: ["a", "b"], spiegel: ["x"], schlange: [], nurGeraet: ["s"] })).toEqual(["a", "b", "s"]);
    expect(sichtbareListe({ kontomodus: true, geraet: ["a"], spiegel: ["x", "y"], schlange: [e("entfernen", "y"), e("merken", "z")], nurGeraet: ["s"] }))
      .toEqual(["x", "z", "s"]);
  });
  it("Abmelden: Spiegel leer → nur Geräteliste", () => {
    expect(sichtbareListe({ kontomodus: false, geraet: ["a"], spiegel: [], schlange: [], nurGeraet: [] })).toEqual(["a"]);
  });
});

describe("Übernahme entscheiden (5.4 Schritte 1–3)", () => {
  it("leeres Konto ohne merkliste_begonnen_am → automatisch", () => {
    expect(uebernahmeEntscheiden(["a", "b", "c"], [], null)).toEqual({ art: "automatisch", nurAufGeraet: ["a", "b", "c"] });
  });
  it("Konto hat Einträge, Gerät hat andere → Nachfrage", () => {
    expect(uebernahmeEntscheiden(["a", "b", "c", "d"], ["x"], "2026-11-01T00:00:00Z").art).toBe("nachfrage");
  });
  it("Konto leer, aber früher geleert → Nachfrage", () => {
    expect(uebernahmeEntscheiden(["a", "b", "c"], [], "2026-11-01T00:00:00Z")).toEqual({ art: "nachfrage", nurAufGeraet: ["a", "b", "c"] });
  });
  it("alles schon im Konto → nichts", () => {
    expect(uebernahmeEntscheiden(["a"], ["a", "b"], "x").art).toBe("nichts");
  });
});

describe("geraetelisteNachUebernahme (5.4 Schritt 8)", () => {
  it("automatisch, alle 3 übernommen → Geräteliste leer", () => {
    const r = geraetelisteNachUebernahme(["a", "b", "c"], [], antwort({ konto: ["a", "b", "c"], uebernommen: 3 }));
    expect(r.geraet).toEqual([]);
  });
  it("Konto 400, Gerät 600 (50 schon im Konto) → 100 übernommen, 450 bleiben", () => {
    const geraet = Array.from({ length: 600 }, (_, i) => `g${i}`);
    const schonImKonto = geraet.slice(0, 50);
    const konto = [...Array.from({ length: 350 }, (_, i) => `k${i}`), ...schonImKonto, ...geraet.slice(50, 150)];
    const r = geraetelisteNachUebernahme(geraet, [], antwort({ konto, uebernommen: 100, nicht_uebernommen: geraet.slice(150), vollstaendig: false }));
    expect(r.geraet).toHaveLength(450);
    expect(r.geraet).toEqual(geraet.slice(150));
  });
  it("ungueltig verschwindet vom Gerät, nie ins Konto", () => {
    const r = geraetelisteNachUebernahme(["beispiel-e1", "a"], [], antwort({ konto: ["a"], ungueltig: ["beispiel-e1"] }));
    expect(r.geraet).toEqual([]);
  });
  it("umgeschrieben: X verschwindet nur, wenn Y im Konto steht", () => {
    expect(geraetelisteNachUebernahme(["x"], [], antwort({ konto: ["y"], umgeschrieben: [{ von: "x", nach: "y" }] })).geraet).toEqual([]);
    expect(geraetelisteNachUebernahme(["x"], [], antwort({ konto: [], umgeschrieben: [{ von: "x", nach: "y" }], nicht_uebernommen: ["y"] })).geraet)
      .toEqual(["x"]);
  });
  it("bleiben_auf_geraet wandert nach ddd-merkliste-geraet", () => {
    const r = geraetelisteNachUebernahme(["a", "s"], [], antwort({ konto: ["a"], bleiben_auf_geraet: ["s"] }));
    expect(r.geraet).toEqual([]);
    expect(r.nurGeraet).toEqual(["s"]);
  });
});

describe("Warteschlange", () => {
  it("Klick-Reihenfolge bleibt erhalten", () => {
    expect(warteschlangeAnwenden(["a", "b", "c"], [e("entfernen", "b"), e("merken", "d")])).toEqual(["a", "c", "d"]);
  });
  it("[entfernen B, merken D] offen, dann 401 → Geräteliste ohne B, mit D", () => {
    expect(warteschlangeAnwenden(["a", "b"], [e("entfernen", "b"), e("merken", "d")])).toEqual(["a", "d"]);
  });
  it("offene Löschungen: nur IDs, deren letzter Eintrag „entfernen“ ist", () => {
    expect(offeneLoeschungen([e("entfernen", "a"), e("merken", "b"), e("entfernen", "c"), e("merken", "c")])).toEqual(["a"]);
    expect(offeneLoeschungen([])).toEqual([]);
  });
  it("Herz im Kontomodus schaltet je nach sichtbarem Zustand", () => {
    expect(herzImKonto(["a"], [], "a", 1).schlange.at(-1)?.op).toBe("entfernen");
    expect(herzImKonto(["a"], [e("entfernen", "a")], "a", 2).schlange.at(-1)?.op).toBe("merken");
    expect(herzImKonto([], [], "b", 3).schlange.at(-1)?.op).toBe("merken");
  });
});

describe("Herz-Antworten einordnen (5.5)", () => {
  it("bildet Statuscodes auf das Verhalten ab", () => {
    expect(herzAntwortEinordnen(200, undefined, "konto")).toEqual({ art: "ok", gespeichert: "konto" });
    expect(herzAntwortEinordnen(200, undefined, "geraet")).toEqual({ art: "ok", gespeichert: "geraet" });
    expect(herzAntwortEinordnen(401).art).toBe("abgemeldet");
    expect(herzAntwortEinordnen(403, "mindestalter_fehlt").art).toBe("mindestalter");
    expect(herzAntwortEinordnen(404).art).toBe("verwerfen");
    expect(herzAntwortEinordnen(409, "merkliste_voll").art).toBe("verwerfen");
    expect(herzAntwortEinordnen(500).art).toBe("spaeter");
    expect(herzAntwortEinordnen(null).art).toBe("spaeter");
  });
});

describe("Merkliste-Darstellung (E9)", () => {
  it("kommende nach Datum, vergangene getrennt; mehrtägig ab heute gilt als kommend", () => {
    const ev = [
      { id: "1", datum: "2026-11-20", datum_bis: null },
      { id: "2", datum: "2026-11-10", datum_bis: null },
      { id: "3", datum: "2026-11-01", datum_bis: "2026-11-30" },
      { id: "4", datum: "2026-11-12", datum_bis: null },
    ];
    const { kommend, vorbei } = merklisteAufteilen(ev, "2026-11-16");
    expect(kommend.map((x) => x.id)).toEqual(["3", "1"]);
    expect(vorbei.map((x) => x.id)).toEqual(["4", "2"]);
  });
});
