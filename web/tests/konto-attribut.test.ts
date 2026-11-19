// html[data-konto] folgt dem Hinweis-Cookie ohne Neuladen (Plan Mein Bereich 3.0). Node ohne Browser:
// document und window werden minimal nachgebaut.
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { KONTO_EVENT, kontoAttributAbgleichen, kontoZustand } from "@/lib/konto/merk-store";
import { KONTO_SCRIPT } from "@/lib/konto/kopf-skript";

const ereignisse: string[] = [];
let html: { dataset: Record<string, string> };
let body: { dataset: Record<string, string> };

beforeEach(() => {
  ereignisse.length = 0;
  html = { dataset: {} };
  body = { dataset: { konten: "1" } };
  (globalThis as Record<string, unknown>).document = { cookie: "", documentElement: html, body };
  (globalThis as Record<string, unknown>).window = { dispatchEvent: (e: Event) => ereignisse.push(e.type) };
});
afterEach(() => {
  delete (globalThis as Record<string, unknown>).document;
  delete (globalThis as Record<string, unknown>).window;
});
const cookie = (wert: string) => ((globalThis as unknown as { document: { cookie: string } }).document.cookie = wert);

describe("kontoAttributAbgleichen", () => {
  it("setzt 1, 0 und entfernt das Attribut je nach Cookie; Ereignis nur bei Änderung", () => {
    cookie("ddd_konto=1");
    expect(kontoZustand()).toBe("1");
    kontoAttributAbgleichen();
    expect(html.dataset.konto).toBe("1");
    kontoAttributAbgleichen();
    expect(ereignisse).toEqual([KONTO_EVENT]);

    cookie("ddd_konto=0");
    kontoAttributAbgleichen();
    expect(html.dataset.konto).toBe("0");

    cookie("andere=1");
    kontoAttributAbgleichen();
    expect(html.dataset.konto).toBeUndefined();
    expect(ereignisse.length).toBe(3);
  });
  it("Schalter aus (body ohne data-konten): kein Attribut, auch wenn ein Cookie liegenbleibt", () => {
    body.dataset = {};
    cookie("ddd_konto=1");
    kontoAttributAbgleichen();
    expect(html.dataset.konto).toBeUndefined();
    expect(ereignisse).toEqual([]);
  });
});

describe("KONTO_SCRIPT (Head, vor dem ersten Paint)", () => {
  const ausfuehren = () => new Function("document", KONTO_SCRIPT)((globalThis as Record<string, unknown>).document);
  it("setzt 1 bzw. 0 aus dem Cookie, ohne Cookie nichts; liest body nicht", () => {
    (globalThis as unknown as { document: Record<string, unknown> }).document = { cookie: "a=b; ddd_konto=1", documentElement: html };
    ausfuehren();
    expect(html.dataset.konto).toBe("1");
    html.dataset = {};
    cookie("ddd_konto=0");
    ausfuehren();
    expect(html.dataset.konto).toBe("0");
    html.dataset = {};
    cookie("ddd_konto=2; x_ddd_konto=1");
    ausfuehren();
    expect(html.dataset.konto).toBeUndefined();
  });
});
