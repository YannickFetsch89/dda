// Zweites Bild (Essen & Getränke, extras.bild_zweit) auf der Detailseite von Restaurants und Cafés (27.11.2026):
// Bildadresse wie beim Titelbild – lokale Datei direkt, sonst immer über den eigenen Server (/ort-foto/…?bild=zweit).
import { describe, expect, it } from "vitest";
import { ortZweitBildUrl, ortZweitNachweis, zweitBildQuelle } from "@/lib/orte";
import type { DddOrt } from "@/lib/typen";

const NAME = "places/ChIJp5utnSG2uEcRiEASre9sJes/photos/AV-0GLces6_xqch0t";

function ort(extras: Record<string, unknown>, slug = "cafe-casa-nata-bakery-feinkost-derendorf"): DddOrt {
  return { id: "1", slug, name: "Café Casa.Nata", typ: "cafe", extras } as unknown as DddOrt;
}

describe("Essensbild (bild_zweit)", () => {
  it("eigenes Bild als lokale Datei: direkt, mit ?v= aus foto_version", () => {
    const o = ort({ foto_version: 3, bild_zweit: { art: "eigen", bild_url: "/ort-bilder/restaurants/cafe-casa-nata-bakery-feinkost-derendorf-essen.webp", nachweis: "casanata.de", link: "https://casanata.de/" } });
    expect(ortZweitBildUrl(o)).toBe("/ort-bilder/restaurants/cafe-casa-nata-bakery-feinkost-derendorf-essen.webp?v=3");
    expect(ortZweitNachweis(o)).toEqual({ text: "casanata.de", link: "https://casanata.de/" });
  });

  it("eigenes Bild auf fremdem Server: nur über den eigenen Server, nie direkt", () => {
    const o = ort({ bild_zweit: { art: "eigen", bild_url: "https://example.com/bild.jpg", nachweis: "example.com", link: "http://example.com/" } });
    expect(ortZweitBildUrl(o)).toBe("/ort-foto/cafe-casa-nata-bakery-feinkost-derendorf?bild=zweit");
    expect(zweitBildQuelle(o)).toEqual({ eigenes: "https://example.com/bild.jpg", google: null });
    // Link nur mit https
    expect(ortZweitNachweis(o)).toEqual({ text: "example.com", link: null });
  });

  it("Google-Foto: über den eigenen Server, Urheber-Link aus google_foto.autor_url", () => {
    const o = ort({ foto_version: 2, bild_zweit: { art: "google", google_foto: { name: NAME, autor: "Anna", autor_url: "https://maps.google.com/x" }, nachweis: "Anna" } });
    expect(ortZweitBildUrl(o)).toBe("/ort-foto/cafe-casa-nata-bakery-feinkost-derendorf?bild=zweit&v=2");
    expect(zweitBildQuelle(o)).toEqual({ eigenes: null, google: NAME });
    expect(ortZweitNachweis(o)).toEqual({ text: "Anna", link: "https://maps.google.com/x" });
  });

  it("fehlt oder ungültig: kein Bild, kein Nachweis", () => {
    expect(ortZweitBildUrl(ort({}))).toBeNull();
    expect(ortZweitNachweis(ort({}))).toBeNull();
    // ungültiger Google-Name und Adresse mit Key werden nie weitergereicht
    expect(ortZweitBildUrl(ort({ bild_zweit: { art: "google", google_foto: { name: "places/x/photos/../böse" } } }))).toBeNull();
    expect(ortZweitBildUrl(ort({ bild_zweit: { art: "eigen", bild_url: "https://maps.googleapis.com/x?key=abc" } }))).toBeNull();
  });
});
