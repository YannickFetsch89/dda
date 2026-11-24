-- Quellen-Ausbau, Schritt R2 (Plan docs/plan-quellen-ausbau-2026-11-23.md, 4.3 und 4.5).
-- VOR dem Deploy von R2 im Supabase-SQL-Editor als Ganzes ausführen. Wiederholbar.
--
-- 1. events.quellen (jsonb): alle Quellen, die ein Event geliefert haben – Liste von
--    {"name": quelle_name, "url": quelle_url, "rang": 1–5, "zuletzt": Zeitpunkt}, höchstens ein Eintrag je Name.
--    Die Hauptquelle bleibt quelle_name/quelle_url. Vorbelegung für alle Zeilen ohne Liste aus der heutigen Quelle;
--    den Rang rechnet derselbe CASE wie pipeline/quellen_rang.py (RANG_GESPEICHERT, unbekannt = 3,
--    Rausgegangen per Name oder URL = 5). Die Spalte erbt die Policy „Events lesen“ (auth_rollen.sql).
-- 2. scraper_laeufe: drei Kennzahlen des Laufs
--      kuenftige_events  – sichtbare Events ab heute nach dem Speichern
--      nur_rausgegangen  – davon Events, die nur Rausgegangen kennt
--      luecken           – {Ort: Anzahl} Rausgegangen-Events an Orten mit eigener Quelle ohne Treffer (Warnregel W7)
--    Fehlen diese Spalten, verwirft der Lauf-Report ALLE Kennzahlen des Laufs (pipeline/lauf_report.py, abschliessen).

ALTER TABLE public.events
    ADD COLUMN IF NOT EXISTS quellen JSONB;

UPDATE public.events
SET quellen = jsonb_build_array(jsonb_build_object(
        'name', quelle_name,
        'url', quelle_url,
        'rang', CASE
            WHEN lower(coalesce(quelle_name, '')) LIKE '%rausgegangen%'
              OR lower(coalesce(quelle_url, '')) LIKE '%rausgegangen.de%' THEN 5
            ELSE CASE btrim(coalesce(quelle_name, ''))
            WHEN 'Ticketmaster' THEN 2
            WHEN 'Kulturportal Düsseldorf' THEN 3
            WHEN 'VisitDüsseldorf' THEN 3
            WHEN 'VisitDüsseldorf Führungen' THEN 3
            WHEN 'Meetup.com' THEN 3
            WHEN 'Resident Advisor' THEN 3
            WHEN 'PRINZ.de Düsseldorf' THEN 4
            WHEN 'Songkick' THEN 4
            WHEN 'AllEvents.in Düsseldorf' THEN 4
            WHEN 'Rausgegangen' THEN 5
            WHEN 'Tonhalle Düsseldorf' THEN 1
            WHEN 'zakk' THEN 1
            WHEN 'Deutsche Oper am Rhein' THEN 1
            WHEN 'Düsseldorfer Schauspielhaus' THEN 1
            WHEN 'd-live' THEN 1
            WHEN 'Kunstpalast Düsseldorf' THEN 1
            WHEN 'Kunstsammlung NRW (K20/K21)' THEN 1
            WHEN 'NRW-Forum Düsseldorf' THEN 1
            WHEN 'FFT Düsseldorf' THEN 1
            WHEN 'Stahlwerk Düsseldorf' THEN 1
            WHEN 'Rudas Studios Düsseldorf' THEN 1
            WHEN 'Mitsubishi Electric HALLE' THEN 1
            WHEN 'Kulturschlachthof R25' THEN 1
            WHEN 'Salon des Amateurs' THEN 1
            WHEN 'Pitcher Rock HQ' THEN 1
            WHEN 'Kunsthalle Düsseldorf' THEN 1
            WHEN 'Filmmuseum Düsseldorf' THEN 1
            WHEN 'Stadtbüchereien Düsseldorf' THEN 1
            WHEN 'Tanzhaus NRW' THEN 1
            WHEN 'Jazz-Schmiede Düsseldorf' THEN 1
            WHEN 'Capitol Theater Düsseldorf' THEN 1
            WHEN 'Kom(m)ödchen Düsseldorf' THEN 1
            WHEN 'STARTPLATZ Düsseldorf' THEN 1
            WHEN 'Parkrun Volksgarten Düsseldorf' THEN 1
            WHEN 'Sport im Park Düsseldorf' THEN 1
            WHEN 'Fortuna Düsseldorf' THEN 1
            WHEN 'DEG Eishockey Düsseldorf' THEN 1
            WHEN 'Messe Düsseldorf' THEN 1
            WHEN 'EKŌ-Haus der Japanischen Kultur' THEN 1
            WHEN 'Classic Remise Düsseldorf' THEN 1
            WHEN 'Stadtstrand Düsseldorf' THEN 1
            WHEN 'IHK Düsseldorf' THEN 1
            WHEN 'StartupDorf Meetup' THEN 1
            WHEN 'Street Food Thursday' THEN 1
            WHEN 'Kasematten Düsseldorf' THEN 1
            WHEN 'Auf ins Viertel' THEN 1
            WHEN 'Kleine Weihnachtsmärkte' THEN 1
            WHEN 'Classic Remise' THEN 1
            WHEN 'Street Food Thursday Düsseldorf' THEN 1
            WHEN 'Kleine Weihnachtsmärkte (Redaktion)' THEN 1
            WHEN 'Event-Meldung' THEN 1
            WHEN 'Eventbrite' THEN 4
            WHEN 'eventfinder.de' THEN 4
            WHEN 'meinestadt.de' THEN 4
            WHEN 'Bandsintown' THEN 4
            WHEN 'Spontacts Düsseldorf' THEN 4
            ELSE 3
            END
        END,
        'zuletzt', coalesce(erstellt_am, now())
    ))
WHERE quellen IS NULL
  AND quelle_name IS NOT NULL;

ALTER TABLE public.scraper_laeufe
    ADD COLUMN IF NOT EXISTS kuenftige_events INTEGER,
    ADD COLUMN IF NOT EXISTS nur_rausgegangen INTEGER,
    ADD COLUMN IF NOT EXISTS luecken          JSONB;

-- PostgREST den neuen Aufbau sofort mitteilen (sonst kennt der Schema-Cache die Spalten im ersten Lauf noch nicht)
NOTIFY pgrst, 'reload schema';

-- Kontrolle 1: neue Spalten
SELECT table_name, column_name, data_type FROM information_schema.columns
WHERE table_schema = 'public'
  AND ((table_name = 'events' AND column_name = 'quellen')
    OR (table_name = 'scraper_laeufe' AND column_name IN ('kuenftige_events', 'nur_rausgegangen', 'luecken')))
ORDER BY table_name, column_name;

-- Kontrolle 2: Vorbelegung je Rang (künftige Events)
SELECT (quellen -> 0 ->> 'rang')::int AS rang, count(*) AS events
FROM public.events
WHERE datum >= current_date
GROUP BY 1 ORDER BY 1;
