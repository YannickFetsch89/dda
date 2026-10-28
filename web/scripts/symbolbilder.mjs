// Erzeugt die Symbolbilder für Events ohne eigenes Foto.
// Quelle: symbolbilder-quellen/<motiv>/*.jpg|png|webp (Originale aus Gemini, nicht in Git)
// Ziel:   public/fallback/<motiv>-<nr>.webp (1200 px breit) + lib/symbolbilder.json (Motiv → Anzahl)
// Aufruf: npm run symbolbilder
import fs from "node:fs";
import path from "node:path";
import sharp from "sharp";

const QUELLE = "symbolbilder-quellen";
const ZIEL = "public/fallback";
const MANIFEST = "lib/symbolbilder.json";
const BREITE = 1200;

// Natürliche Sortierung, damit "(10)" nach "(9)" kommt
const natuerlich = (a, b) => a.localeCompare(b, "de", { numeric: true });

fs.mkdirSync(ZIEL, { recursive: true });
for (const alt of fs.readdirSync(ZIEL)) if (alt.endsWith(".webp")) fs.rmSync(path.join(ZIEL, alt));

const manifest = {};
for (const motiv of fs.readdirSync(QUELLE).sort()) {
  const ordner = path.join(QUELLE, motiv);
  if (!fs.statSync(ordner).isDirectory()) continue;
  if (!/^[a-z0-9-]+$/.test(motiv)) {
    console.warn(`Übersprungen: Ordnername "${motiv}" bitte nur aus a-z, 0-9 und Bindestrich`);
    continue;
  }
  const dateien = fs.readdirSync(ordner).filter((d) => /\.(jpe?g|png|webp)$/i.test(d)).sort(natuerlich);
  let nr = 0;
  for (const datei of dateien) {
    nr += 1;
    await sharp(path.join(ordner, datei))
      .rotate()
      .resize({ width: BREITE, withoutEnlargement: true })
      .webp({ quality: 74 })
      .toFile(path.join(ZIEL, `${motiv}-${nr}.webp`));
  }
  if (nr) manifest[motiv] = nr;
  console.log(`${motiv}: ${nr} Bilder`);
}

fs.writeFileSync(MANIFEST, JSON.stringify(manifest, null, 2) + "\n");
const groesse = fs.readdirSync(ZIEL).reduce((s, d) => s + fs.statSync(path.join(ZIEL, d)).size, 0);
console.log(`Fertig: ${Object.values(manifest).reduce((a, b) => a + b, 0)} Bilder, ${(groesse / 1e6).toFixed(1)} MB → ${ZIEL}`);
