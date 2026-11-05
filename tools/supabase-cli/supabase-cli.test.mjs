// Tests für den DDA-Supabase-Wrapper:  npm test  (im Ordner tools/supabase-cli)
// Echte Token werden nie verwendet; die Token-Datei kommt über DDA_SUPABASE_ENV aus einem Temp-Ordner.
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { PROJECT_REF, linkedRef, parseEnvFile, projectVisible } from './supabase-cli.mjs';

const SKRIPT = fileURLToPath(new URL('./supabase-cli.mjs', import.meta.url));
const FALSCHES_TOKEN = `sbp_${'0'.repeat(40)}`;

/** Wrapper als eigenen Prozess starten (wie `npm run sb -- …`). */
function wrapper(args, envDatei) {
  return spawnSync(process.execPath, [SKRIPT, ...args], {
    env: { ...process.env, DDA_SUPABASE_ENV: envDatei, SUPABASE_ACCESS_TOKEN: '' },
    encoding: 'utf8',
    timeout: 120_000,
  });
}

function tokenDatei(inhalt) {
  const ordner = mkdtempSync(join(tmpdir(), 'dda-sb-test-'));
  const datei = join(ordner, 'supabase.env');
  writeFileSync(datei, inhalt);
  return { datei, aufraeumen: () => rmSync(ordner, { recursive: true, force: true }) };
}

test('ohne Token: Abbruch mit Anleitung', () => {
  const r = wrapper(['projects', 'list'], join(tmpdir(), 'gibt-es-nicht', 'supabase.env'));
  assert.equal(r.status, 1);
  assert.match(r.stderr, /kein DDA-Token/);
  assert.match(r.stderr, /Access Tokens/);
});

test('leerer Token-Wert (Vorlage unverändert): Abbruch mit Anleitung', () => {
  const t = tokenDatei('# Kommentar\r\nSUPABASE_ACCESS_TOKEN=\r\n');
  try {
    const r = wrapper(['projects', 'list'], t.datei);
    assert.equal(r.status, 1);
    assert.match(r.stderr, /kein DDA-Token/);
  } finally {
    t.aufraeumen();
  }
});

test('Ordner nicht mit DDA verlinkt: Abbruch vor jedem Netzabruf', { skip: linkedRef() === PROJECT_REF }, () => {
  const t = tokenDatei(`SUPABASE_ACCESS_TOKEN=${FALSCHES_TOKEN}\n`);
  try {
    const r = wrapper(['migration', 'list', '--linked'], t.datei);
    assert.equal(r.status, 1);
    assert.match(r.stderr, /verlinkt, erwartet dqckcszxoyaxiwwcgxxk/);
  } finally {
    t.aufraeumen();
  }
});

test('falsches Token: Abbruch „anderes Konto oder abgelaufen“, Token wird nicht ausgegeben', () => {
  const t = tokenDatei(`SUPABASE_ACCESS_TOKEN="${FALSCHES_TOKEN}"\n`);
  try {
    // „link“ überspringt die Verlinkungs-Prüfung → die Token-Prüfung (projects list) greift
    const r = wrapper(['link', '--project-ref', PROJECT_REF], t.datei);
    assert.equal(r.status, 1);
    assert.match(r.stderr, /Token gehört zu einem anderen Konto oder ist abgelaufen/);
    assert.ok(!r.stderr.includes(FALSCHES_TOKEN) && !r.stdout.includes(FALSCHES_TOKEN), 'Token darf nicht erscheinen');
  } finally {
    t.aufraeumen();
  }
});

test('Projekt-Erkennung in der JSON-Liste von `projects list -o json`', () => {
  const liste = JSON.stringify([
    { id: 'abc', ref: 'aaaaaaaaaaaaaaaaaaaa', name: 'Ein.Blick', region: 'eu-central-1' },
    { id: PROJECT_REF, ref: PROJECT_REF, name: 'DDA', region: 'eu-central-1' },
  ]);
  assert.equal(projectVisible(liste), true);
  assert.equal(projectVisible(JSON.stringify({ projects: [{ ref: PROJECT_REF }] })), true);
  assert.equal(projectVisible(JSON.stringify([{ ref: 'aaaaaaaaaaaaaaaaaaaa' }])), false);
  assert.equal(projectVisible('[]'), false);
  assert.equal(projectVisible('Unauthorized'), false);
  assert.equal(projectVisible(''), false);
});

test('Token-Datei: Kommentare, Anführungszeichen, CRLF', () => {
  const env = parseEnvFile('# Kommentar\r\nSUPABASE_ACCESS_TOKEN="sbp_abc"\r\n\r\nANDERES=1\n# X=2\n');
  assert.equal(env.SUPABASE_ACCESS_TOKEN, 'sbp_abc');
  assert.equal(env.ANDERES, '1');
  assert.equal(env.X, undefined);
});
