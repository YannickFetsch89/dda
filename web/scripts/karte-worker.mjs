// Kopiert den MapLibre-Worker aus node_modules nach public/karte/, damit die Karte ihn vom eigenen
// Server laden kann (MapLibre 6 sucht ihn sonst neben der gebündelten Datei, wo er nach dem Build fehlt).
// Läuft automatisch vor "npm run dev" und "npm run build" (predev/prebuild in package.json).
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const web = join(dirname(fileURLToPath(import.meta.url)), "..");
const quelle = join(web, "node_modules", "maplibre-gl", "dist", "maplibre-gl-worker.mjs");
const ziel = join(web, "public", "karte", "maplibre-gl-worker.mjs");

mkdirSync(dirname(ziel), { recursive: true });
copyFileSync(quelle, ziel);
console.log("MapLibre-Worker nach public/karte/ kopiert");
