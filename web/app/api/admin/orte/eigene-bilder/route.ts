// Admin-Bereich – eigene Bilddateien unter web/public/ort-bilder (Plan Admin-Dashboard 4.7, Stufe 3b).
// GET ?ordner=orte|weihnachtsmaerkte|… → Pfade (/ort-bilder/…), neueste zuerst. Eigene Bilder bleiben Dateien im Repo
// (Q5: Upload offen) – neue kommen weiter per Deploy (z. B. scraper/orte/ortsbilder.py), hier wird nur ausgewählt.
import { readdir, stat } from "node:fs/promises";
import path from "node:path";
import { eigenesBildErlaubt } from "@/lib/admin/guides";
import { adminAntwort, adminRoute } from "@/lib/admin/route";

const WURZEL = () => path.join(/* turbopackIgnore: true */ process.cwd(), "public", "ort-bilder");

async function dateien(ordner: string): Promise<{ pfad: string; zeit: number }[]> {
  const aus: { pfad: string; zeit: number }[] = [];
  const basis = WURZEL();
  async function lesen(rel: string, tiefe: number) {
    if (tiefe > 3) return;
    const eintraege = await readdir(path.join(basis, rel), { withFileTypes: true }).catch(() => []);
    for (const e of eintraege) {
      const r = rel ? `${rel}/${e.name}` : e.name;
      if (e.isDirectory()) await lesen(r, tiefe + 1);
      else if (eigenesBildErlaubt(`/ort-bilder/${r}`)) {
        const s = await stat(path.join(basis, r)).catch(() => null);
        aus.push({ pfad: `/ort-bilder/${r}`, zeit: s?.mtimeMs ?? 0 });
      }
    }
  }
  await lesen(ordner, 0);
  return aus.sort((a, b) => b.zeit - a.zeit);
}

export async function GET(request: Request) {
  return adminRoute(request, {}, async ({ setCookies }) => {
    const ordner = new URL(request.url).searchParams.get("ordner") ?? "";
    if (ordner && !/^[a-z0-9-]+$/.test(ordner)) return adminAntwort(400, { fehler: "Ungültiger Ordner." }, setCookies);
    const liste = await dateien(ordner);
    return adminAntwort(200, { bilder: liste.slice(0, 400).map((d) => d.pfad) }, setCookies);
  });
}
