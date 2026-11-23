// Admin-Bereich – Technik und Kosten (Plan Admin-Dashboard 4.10, Stufe 5a).
// GET → Speicherplatz des Servers (fs.statfs), Größe von logs/ und web/.next, KI-Kosten Magazin (dieses Jahr), Schalter
// (GitHub-Variablen, nur lesen – gesetzt werden sie auf GitHub, E4). Gesamtkosten Anthropic/Google gibt es nicht:
// Dafür fehlt eine Quelle (Q8).
import { opendir, stat, statfs } from "node:fs/promises";
import path from "node:path";
import { schalterLesen } from "@/lib/admin/github";
import { adminAntwort, adminRoute } from "@/lib/admin/route";

const MAX_DATEIEN = 200_000;
const MAX_MS = 4000;

/**
 * Größe eines Ordners in Bytes (rekursiv, ohne Symlinks); bricht bei MAX_DATEIEN oder MAX_MS ab (dann „mindestens“).
 * Cursor-Prüfung 5a, Befund 3: Die Grenze gilt je Eintrag, und Ordner werden mit opendir gestreamt statt ganz
 * eingelesen – auch ein großer flacher Ordner hält den Next-Prozess so höchstens MAX_MS fest.
 */
async function ordnerGroesse(wurzel: string): Promise<{ bytes: number; dateien: number; vollstaendig: boolean } | null> {
  const start = Date.now();
  let bytes = 0;
  let dateien = 0;
  const offen = [wurzel];
  try {
    await stat(wurzel);
  } catch {
    return null;
  }
  const ueberGrenze = () => dateien >= MAX_DATEIEN || Date.now() - start > MAX_MS;
  while (offen.length) {
    const ordner = offen.pop()!;
    const dir = await opendir(ordner, { bufferSize: 64 }).catch(() => null);
    if (!dir) continue;
    try {
      for await (const e of dir) {
        if (ueberGrenze()) return { bytes, dateien, vollstaendig: false };
        const p = path.join(ordner, e.name);
        if (e.isDirectory()) offen.push(p);
        else if (e.isFile()) {
          const s = await stat(p).catch(() => null);
          if (s) {
            bytes += s.size;
            dateien += 1;
          }
        }
      }
    } catch {
      // Ordner während des Lesens verschwunden o. Ä. → weiter mit dem nächsten
    }
  }
  return { bytes, dateien, vollstaendig: true };
}

export async function GET(request: Request) {
  return adminRoute(request, {}, async ({ admin, setCookies }) => {
    const web = /* turbopackIgnore: true */ process.cwd();
    const jahr = `${new Date().getUTCFullYear()}-01-01`;
    const [platte, logs, next, kosten, schalter] = await Promise.all([
      statfs(web).then((s) => ({ gesamt: s.blocks * s.bsize, frei: s.bavail * s.bsize })).catch(() => null),
      ordnerGroesse(path.join(web, "..", "logs")),
      ordnerGroesse(path.join(web, ".next")),
      admin!.db.rpc("admin_magazin_kosten", { p_von: jahr }),
      schalterLesen(),
    ]);
    return adminAntwort(
      200,
      {
        platte,
        ordner: { logs, next },
        magazin_kosten: kosten.error ? null : kosten.data,
        schalter,
        hinweis_kosten: "Gesamtkosten für Anthropic und Google zeigt das Dashboard nicht: Dafür gibt es keine Quelle (Q8). Bitte in den Konsolen der Anbieter nachsehen.",
      },
      setCookies,
    );
  });
}
