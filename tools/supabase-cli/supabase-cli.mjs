#!/usr/bin/env node
// Supabase-CLI NUR für DDA (dies.das.düsseldorf) – mit eigenem Token, unabhängig vom globalen `supabase login`.
//
// Problem (2026-11-05): Der CLI-Login gilt für den ganzen Windows-Benutzer. Ein `supabase login` in einem
// anderen Projekt/Konto sperrte Ein.Blick aus (Deploy → 403); DDA liegt im selben Konto. Lösung wie Ein.Blick:
//   - Token aus secrets/supabase.env (SUPABASE_ACCESS_TOKEN, gitignored) → nur an den Kind-Prozess
//     (die Umgebungsvariable hat Vorrang vor dem globalen Login);
//   - vor jedem Befehl prüfen: Ordner ist mit DDA verlinkt (supabase/.temp/project-ref) UND das Token
//     sieht das DDA-Projekt – sonst klarer Abbruch statt 403.
//
// Aufruf (im Ordner tools/supabase-cli):
//   npm run sb -- <supabase-Argumente>      z. B. npm run sb -- projects list
//   npm run db:list | db:push | db:push:dry
//
// Die CLI ist hier als devDependency fest gepinnt (package.json) und wird direkt aus node_modules
// aufgerufen – nie ein nacktes `npx supabase` (lädt sonst ggf. still v3, die ohne --linked lokal arbeitet).
// Gearbeitet wird im Projekt-Hauptordner (supabase/ liegt dort). Das Token wird nie ausgegeben.
// Test-Haken: DDA_SUPABASE_ENV = anderer Pfad zur Token-Datei.

import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const TOOL_DIR = dirname(fileURLToPath(import.meta.url));
export const ROOT = join(TOOL_DIR, '..', '..');
export const PROJECT_REF = 'dqckcszxoyaxiwwcgxxk'; // DDA, Region eu-central-1

const IS_WIN = process.platform === 'win32';
const CLI = join(TOOL_DIR, 'node_modules', '.bin', IS_WIN ? 'supabase.cmd' : 'supabase');

/** KEY=VALUE-Datei lesen (Kommentare, Leerzeilen, Anführungszeichen, CRLF). */
export function parseEnvFile(text) {
  const out = {};
  for (const line of String(text).split(/\r?\n/)) {
    const m = /^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/.exec(line);
    if (!m || line.trim().startsWith('#')) continue;
    out[m[1]] = m[2].replace(/^(['"])(.*)\1$/, '$2');
  }
  return out;
}

export function envFilePath() {
  return process.env.DDA_SUPABASE_ENV || join(ROOT, 'secrets', 'supabase.env');
}

/** Token aus secrets/supabase.env; null, wenn Datei oder Wert fehlt. */
export function loadToken(path = envFilePath()) {
  if (!existsSync(path)) return null;
  const t = parseEnvFile(readFileSync(path, 'utf8')).SUPABASE_ACCESS_TOKEN ?? '';
  return t.trim() ? t.trim() : null;
}

/** JSON-Ausgabe von `projects list -o json` enthält das Projekt? */
export function projectVisible(jsonText, ref = PROJECT_REF) {
  try {
    const d = JSON.parse(jsonText);
    const list = Array.isArray(d) ? d : Array.isArray(d?.projects) ? d.projects : [];
    return list.some((p) => p && (p.ref === ref || p.id === ref));
  } catch {
    return false;
  }
}

/** Mit welchem Projekt ist der Ordner verlinkt? ('' = gar nicht) */
export function linkedRef(root = ROOT) {
  const refFile = join(root, 'supabase', '.temp', 'project-ref');
  return existsSync(refFile) ? readFileSync(refFile, 'utf8').trim() : '';
}

function fail(lines) {
  for (const l of lines) console.error(`supabase-cli: ${l}`);
  return 1;
}

// Windows: .cmd nur über die Shell startbar; Pfad in Anführungszeichen (Leerzeichen im Benutzerpfad)
const cli = (args, env, stdio) =>
  spawnSync(IS_WIN ? `"${CLI}"` : CLI, args, { cwd: ROOT, env, stdio, shell: IS_WIN, encoding: 'utf8' });

/** Führt `supabase <args>` mit dem DDA-Token aus. Rückgabe: Exit-Code. */
export function runSupabase(args) {
  const token = loadToken();
  if (!token) {
    return fail([
      `kein DDA-Token in ${envFilePath()}.`,
      'Supabase-Dashboard (Konto mit DDA) → Account → Access Tokens → neues Token „dda-cli“ erzeugen,',
      'dann secrets/supabase.env nach Vorlage secrets/supabase.env.example anlegen und den Wert selbst eintragen.',
    ]);
  }
  if (!existsSync(CLI)) {
    return fail([
      'Supabase-CLI nicht installiert.',
      'Bitte einmalig im Ordner tools/supabase-cli: npm ci',
    ]);
  }
  // Nur das Token zusätzlich setzen; ein evtl. global gesetztes SUPABASE_ACCESS_TOKEN wird überschrieben
  const env = { ...process.env, SUPABASE_ACCESS_TOKEN: token };

  // Verlinktes Projekt muss DDA sein (db push/migration list arbeiten mit --linked);
  // ausgenommen sind die Befehle, mit denen der Ordner erst eingerichtet wird
  if (!['link', 'init'].includes(args[0])) {
    const linked = linkedRef();
    if (linked !== PROJECT_REF) {
      return fail([
        `Ordner ist mit „${linked || 'nichts'}“ verlinkt, erwartet ${PROJECT_REF}.`,
        `Bitte: npm run sb -- link --project-ref ${PROJECT_REF}`,
      ]);
    }
  }

  // Sieht das Token das DDA-Projekt? (sonst gehört es zu einem anderen Konto oder ist abgelaufen)
  const check = cli(['projects', 'list', '-o', 'json'], env, 'pipe');
  if (check.status !== 0 || !projectVisible(check.stdout)) {
    return fail([
      `Token gehört zu einem anderen Konto oder ist abgelaufen (das Token in ${envFilePath()} sieht das Projekt ${PROJECT_REF} nicht).`,
      'Bitte im Supabase-Konto mit DDA ein neues Token „dda-cli“ erzeugen und in secrets/supabase.env eintragen.',
    ]);
  }

  const res = cli(args, env, 'inherit');
  return res.status ?? 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.error('Aufruf: npm run sb -- <supabase-Argumente>   (im Ordner tools/supabase-cli)');
    process.exit(2);
  }
  process.exit(runSupabase(args));
}
