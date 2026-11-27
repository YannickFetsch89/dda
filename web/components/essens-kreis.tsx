"use client";
// Zweites Bild (Essen & Getränke) als Kreis mit goldener Linie halb über dem großen Foto der Detailseite, mit Parallax
// (Entwurf docs/mockups/cafe-essensbild-final.html, 27.11.2026): Beim Runterscrollen wandert der Kreis schneller nach
// oben als die Seite (Faktor 0,4), das große Foto in seiner Hülle etwas langsamer (Faktor 0,15). Nur transform,
// gerechnet in requestAnimationFrame. Bei „Bewegung reduzieren“ steht alles still. Das Server-HTML zeigt beides
// ohne Verschiebung – kein Layoutsprung beim Laden.
import { useEffect, useRef, useState } from "react";

const KREIS = 0.4;
const FOTO = 0.15;
const VORLAUF = 80; // Bewegung beginnt, wenn die Hero-Oberkante 80 px unter dem Fensterrand steht
const NACHLAUF = 200; // Weg höchstens Hero-Höhe + 200 px

export function EssensKreis({ src, alt }: { src: string; alt: string }) {
  const kreis = useRef<HTMLSpanElement>(null);
  const bild = useRef<HTMLImageElement>(null);
  const [fehler, setFehler] = useState(false);

  // Schlägt das Bild schon vor der Hydrierung fehl, kommt onError nie an (wie bei BildImg) → einmal nachsehen
  useEffect(() => {
    const img = bild.current;
    if (img && img.complete && img.naturalWidth === 0) setFehler(true);
  }, []);

  useEffect(() => {
    const k = kreis.current;
    const hero = k?.closest<HTMLElement>("[data-parallax-hero]");
    if (!k || !hero) return;
    const ruhig = window.matchMedia("(prefers-reduced-motion: reduce)");
    let start = 0;
    let geplant = false;
    const messen = () => {
      start = hero.getBoundingClientRect().top + window.scrollY;
    };
    const rechnen = () => {
      geplant = false;
      // Das Foto steckt in BildImg und kann nach einem Ladefehler wechseln → jedes Mal neu suchen
      const foto = hero.querySelector<HTMLElement>(".gd-detail__foto img");
      const weg = ruhig.matches ? 0 : Math.max(0, Math.min(window.scrollY - (start - VORLAUF), hero.offsetHeight + NACHLAUF));
      k.style.transform = weg ? `translate3d(0, ${(-weg * KREIS).toFixed(1)}px, 0)` : "";
      if (foto) foto.style.transform = weg ? `translate3d(0, ${(weg * FOTO).toFixed(1)}px, 0)` : "";
    };
    const anstossen = () => {
      if (!geplant) {
        geplant = true;
        requestAnimationFrame(rechnen);
      }
    };
    const neuMessen = () => {
      messen();
      anstossen();
    };
    messen();
    rechnen();
    window.addEventListener("scroll", anstossen, { passive: true });
    window.addEventListener("resize", neuMessen);
    ruhig.addEventListener("change", anstossen);
    return () => {
      window.removeEventListener("scroll", anstossen);
      window.removeEventListener("resize", neuMessen);
      ruhig.removeEventListener("change", anstossen);
    };
  }, []);

  // Lädt das Bild nicht, verschwindet der Kreis (statt eines leeren goldenen Rings)
  if (fehler) return null;
  return (
    <span ref={kreis} className="gd-detail__essen">
      {/* eslint-disable-next-line @next/next/no-img-element -- Bild kommt vom eigenen Server (lokal oder /ort-foto) */}
      <img ref={bild} src={src} alt={alt} decoding="async" referrerPolicy="no-referrer" onError={() => setFehler(true)} />
    </span>
  );
}
