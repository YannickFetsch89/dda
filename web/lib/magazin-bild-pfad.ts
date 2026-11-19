// Zweite Sicherung der Zuschnitt-Route (Plan 5.11): Nach path.resolve muss die Datei in einem erlaubten Ordner liegen.
import "server-only";
import path from "node:path";
import { ZUSCHNITT_ORDNER } from "./magazin-bilder";

/** Absoluter Pfad der Datei in public/, wenn sie in einem erlaubten Ordner liegt – sonst null. */
export function imErlaubtenOrdner(relativ: string, publicOrdner = path.resolve(process.cwd(), "public")): string | null {
  const voll = path.resolve(publicOrdner, relativ);
  return ZUSCHNITT_ORDNER.some((o) => voll.startsWith(path.resolve(publicOrdner, o) + path.sep)) ? voll : null;
}
