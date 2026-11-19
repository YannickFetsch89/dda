-- magazin_rubriken_autoren_2026-11-19.sql – DiesDasDüsseldorf
-- Magazin Schritt 4 (Plan docs/plan-redaktion-2026-11-19.md, E15 und Nachtrag 19.11.):
--   1 Drei neue Rubriken nachtleben, genuss, familie (Entscheidung Auftraggeber 19.11.2026) – in magazin_beitraege
--     und in magazin_autoren.rubriken. Die Rubrik ist zugleich das URL-Segment (/magazin/rubrik/<rubrik>).
--   2 Die fünf redaktionellen Pseudonyme (Namen vom Auftraggeber, Kurzbeschreibungen von ihm geprüft).
--     Profilbilder folgen (illustriert, KI-generiert); bis dahin bild = NULL.
--   3 Kontrollabfrage (letzte Anweisung): erwartet überall „ok“.
--
-- Wiederholbar (Autoren per ON CONFLICT aktualisiert). Ausführen im Supabase-SQL-Editor als postgres.
-- Unkritisch für Website und Pipeline: Solange MAGAZIN_VERLINKT aus ist, sind die Autorenseiten noindex und unverlinkt.

BEGIN;

-- ── 1 Rubriken ─────────────────────────────────────────────────────────────────────────────────────
ALTER TABLE public.magazin_beitraege DROP CONSTRAINT IF EXISTS magazin_rubrik_werte;
ALTER TABLE public.magazin_beitraege ADD CONSTRAINT magazin_rubrik_werte
    CHECK (rubrik IN ('wochenvorschau', 'monats-tipps', 'saison', 'nachtleben', 'genuss', 'familie', 'stadtleben'));

-- Die Prüfbedingung auf rubriken wurde beim Anlegen ohne Namen erzeugt; alle CHECKs auf diese Spalte ersetzen
DO $$
DECLARE c RECORD;
BEGIN
    FOR c IN
        SELECT con.conname FROM pg_constraint con
        WHERE con.conrelid = 'public.magazin_autoren'::regclass AND con.contype = 'c'
          AND pg_get_constraintdef(con.oid) LIKE '%rubriken%'
    LOOP
        EXECUTE format('ALTER TABLE public.magazin_autoren DROP CONSTRAINT %I', c.conname);
    END LOOP;
END $$;
ALTER TABLE public.magazin_autoren ADD CONSTRAINT magazin_autoren_rubriken
    CHECK (rubriken <@ ARRAY['wochenvorschau', 'monats-tipps', 'saison', 'nachtleben', 'genuss', 'familie', 'stadtleben']);

-- ── 2 Autoren (Pseudonyme) ─────────────────────────────────────────────────────────────────────────
-- rubriken = Standard-Autor je Rubrik (die Pipeline wählt darüber; je Rubrik genau ein Autor)
INSERT INTO public.magazin_autoren (slug, name, kurzbeschreibung, schwerpunkt, rubriken, bild, bild_ki, aktiv) VALUES
  ('lisa-hartwig', 'Lisa Hartwig',
   'Lisa Hartwig sortiert, was in Düsseldorf ansteht: jeden Sonntag die kommende Woche im Überblick, zum Monatsende die stärksten Termine des nächsten Monats. Kurz, verlässlich und mit Blick fürs Wesentliche.',
   'Events & Wochenplanung', ARRAY['wochenvorschau', 'monats-tipps'], NULL, TRUE, TRUE),
  ('dan-suttner', 'Dan Suttner',
   'Dan Suttner schreibt über Konzerte, Clubnächte und alles, was nach Sonnenuntergang in Düsseldorf passiert – von der kleinen Bühne bis zur großen Halle. Im Mittelpunkt: welcher Abend zu wem passt.',
   'Nachtleben & Musik', ARRAY['nachtleben'], NULL, TRUE, TRUE),
  ('nathalie-kirchner', 'Nathalie Kirchner',
   'Nathalie Kirchner erzählt vom Leben in Düsseldorf: Stadtteile, Saisonthemen wie Weihnachtsmärkte oder Karneval und alles, was in kein anderes Ressort passt. Neugierig, ruhig im Ton, nah an dem, was die Stadt gerade bewegt.',
   'Stadtleben', ARRAY['saison', 'stadtleben'], NULL, TRUE, TRUE),
  ('laurenz-weigelt', 'Laurenz Weigelt',
   'Laurenz Weigelt kümmert sich ums Essen und Trinken: Restaurants, Cafés, Foodmärkte, Tastings und Brauhauskultur in Düsseldorf. Im Mittelpunkt steht, was einen Ort ausmacht – ohne Sterne und ohne Werbesprache.',
   'Genuss', ARRAY['genuss'], NULL, TRUE, TRUE),
  ('amelie-glasner', 'Amelie Glasner',
   'Amelie Glasner sammelt, was Familien in Düsseldorf unternehmen können: Kinderprogramm, Spielplätze, Ausflüge und Ideen für Regentage. Praktisch gedacht – mit Blick auf Alter, Wetter und Wege.',
   'Familie', ARRAY['familie'], NULL, TRUE, TRUE)
ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name, kurzbeschreibung = EXCLUDED.kurzbeschreibung, schwerpunkt = EXCLUDED.schwerpunkt,
  rubriken = EXCLUDED.rubriken, bild_ki = EXCLUDED.bild_ki, aktiv = EXCLUDED.aktiv;

COMMIT;

-- ── 3 Kontrollabfrage – erwartet in jeder Zeile „ok“ ────────────────────────────────────────────────
WITH
rubriken (rubrik) AS (VALUES ('wochenvorschau'), ('monats-tipps'), ('saison'), ('nachtleben'), ('genuss'), ('familie'), ('stadtleben')),
k_autor_je_rubrik AS (
    SELECT 1 AS nr, 'Genau ein aktiver Autor je Rubrik'::text AS pruefung, r.rubrik AS objekt, '1'::text AS erwartet,
           (SELECT count(*) FROM public.magazin_autoren a WHERE a.aktiv AND r.rubrik = ANY (a.rubriken))::text AS ist
    FROM rubriken r
),
k_autoren AS (
    SELECT 2 AS nr, 'Autoren angelegt'::text AS pruefung, 'magazin_autoren (aktiv)'::text AS objekt, '5'::text AS erwartet,
           (SELECT count(*) FROM public.magazin_autoren WHERE aktiv)::text AS ist
),
k_check AS (
    SELECT 3 AS nr, 'Rubrik-CHECK kennt die neuen Werte'::text AS pruefung, 'magazin_rubrik_werte'::text AS objekt,
           'ja'::text AS erwartet,
           CASE WHEN pg_get_constraintdef((SELECT oid FROM pg_constraint WHERE conname = 'magazin_rubrik_werte'))
                     LIKE '%genuss%familie%' THEN 'ja' ELSE 'nein' END AS ist
),
k_laenge AS (
    SELECT 4 AS nr, 'Kurzbeschreibung ≤ 300 Zeichen'::text AS pruefung, slug AS objekt, 'ja'::text AS erwartet,
           CASE WHEN length(kurzbeschreibung) <= 300 THEN 'ja' ELSE 'nein' END AS ist
    FROM public.magazin_autoren
),
alles AS (
    SELECT nr, pruefung, objekt, erwartet, ist FROM k_autor_je_rubrik
    UNION ALL SELECT nr, pruefung, objekt, erwartet, ist FROM k_autoren
    UNION ALL SELECT nr, pruefung, objekt, erwartet, ist FROM k_check
    UNION ALL SELECT nr, pruefung, objekt, erwartet, ist FROM k_laenge
)
SELECT nr, pruefung, objekt, erwartet, ist, CASE WHEN erwartet = ist THEN 'ok' ELSE 'FEHLER' END AS ergebnis
FROM alles
ORDER BY CASE WHEN erwartet = ist THEN 1 ELSE 0 END, nr, objekt;
