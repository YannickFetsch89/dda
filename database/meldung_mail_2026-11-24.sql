-- meldung_mail_2026-11-24.sql – DiesDasDüsseldorf
-- Bestätigungsmail an Melder, sobald ihre Meldung als Event veröffentlicht ist (Wunsch des Auftraggebers 24.11.2026).
--
-- Ablauf: Die Freigabe im Dashboard (web/app/api/admin/meldungen/route.ts) setzt mail_status = 'offen' und startet
-- den Workflow .github/workflows/meldung-mail.yml (stündlich als Sicherheitsnetz). Der Job
-- pipeline/meldung_mail.py beansprucht offene Meldungen über meldung_mail_beanspruchen, schickt die Mail und meldet
-- das Ergebnis mit meldung_mail_versandt bzw. meldung_mail_freigeben zurück. Höchstens 3 Versuche je Meldung.
-- Ältere Freigaben (vor diesem Skript) haben mail_status NULL und bekommen keine Mail (Entscheidung 24.11.2026).
-- Endstatus: 'gesendet'; 'fehler' (3 Versuche ohne Zustellung); 'entfallen' (Event inzwischen ausgeblendet oder vorbei).
-- Zweite Fassung nach Cursor-Prüfung (24.11.2026): Endstatus 'entfallen' und das Abschließen hängender Versuche.
--
-- REIHENFOLGE: Dieses Skript VOR dem Deploy ausführen (die Freigabe schreibt sonst in eine fehlende Spalte).
-- Wiederholbar.

BEGIN;

ALTER TABLE public.event_meldungen ADD COLUMN IF NOT EXISTS mail_status TEXT;
ALTER TABLE public.event_meldungen ADD COLUMN IF NOT EXISTS mail_versuche SMALLINT NOT NULL DEFAULT 0;
ALTER TABLE public.event_meldungen ADD COLUMN IF NOT EXISTS mail_beansprucht_am TIMESTAMPTZ;
ALTER TABLE public.event_meldungen ADD COLUMN IF NOT EXISTS mail_gesendet_am TIMESTAMPTZ;

ALTER TABLE public.event_meldungen DROP CONSTRAINT IF EXISTS event_meldungen_mail_status_check;
ALTER TABLE public.event_meldungen ADD CONSTRAINT event_meldungen_mail_status_check
    CHECK (mail_status IS NULL OR mail_status IN ('offen', 'gesendet', 'fehler', 'entfallen'));

CREATE INDEX IF NOT EXISTS idx_event_meldungen_mail_offen
    ON public.event_meldungen (bearbeitet_am) WHERE mail_status = 'offen';

-- Offene Mails beanspruchen (gegen Doppelversand bei parallelen Läufen). Ein Anspruch ohne Rückmeldung, älter als
-- 30 Minuten, wird wieder aufgenommen. Nur Events, die noch sichtbar sind und nicht vorbei.
-- Liefert die Angaben des Events (nicht der Meldung): die Redaktion kann Titel, Ort usw. bei der Freigabe ändern.
-- Vorher werden offene Zeilen abgeschlossen, die nie mehr dran kämen (Cursor-Prüfung 24.11.2026):
--   'entfallen' – Event ausgeblendet, gelöscht oder vorbei; 'fehler' – dritter Versuch beansprucht, aber nie verbucht.
CREATE OR REPLACE FUNCTION public.meldung_mail_beanspruchen(p_anzahl INTEGER)
RETURNS TABLE (
    id UUID, kontakt_email TEXT, kontakt_name TEXT, kontakt_rolle TEXT,
    titel TEXT, datum DATE, datum_bis DATE, uhrzeit TIME, ort TEXT, kategorie TEXT, slug TEXT, event_id UUID
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
    UPDATE public.event_meldungen m
    SET mail_status = 'entfallen', mail_beansprucht_am = NULL
    WHERE m.mail_status = 'offen'
      AND (m.mail_beansprucht_am IS NULL OR m.mail_beansprucht_am < now() - interval '30 minutes')
      AND NOT EXISTS (
          SELECT 1 FROM public.events e
          WHERE e.id = m.event_id AND e.abgelehnt = false
            AND coalesce(e.datum_bis, e.datum) >= (now() AT TIME ZONE 'Europe/Berlin')::date
      );

    UPDATE public.event_meldungen m
    SET mail_status = 'fehler', mail_beansprucht_am = NULL
    WHERE m.mail_status = 'offen' AND m.mail_versuche >= 3
      AND m.mail_beansprucht_am < now() - interval '30 minutes';

    WITH gewaehlt AS (
        SELECT o.id
        FROM public.event_meldungen o
        JOIN public.events oe ON oe.id = o.event_id
        WHERE o.status = 'freigegeben' AND o.mail_status = 'offen' AND o.mail_versuche < 3
          AND (o.mail_beansprucht_am IS NULL OR o.mail_beansprucht_am < now() - interval '30 minutes')
          AND oe.abgelehnt = false
          AND coalesce(oe.datum_bis, oe.datum) >= (now() AT TIME ZONE 'Europe/Berlin')::date
        ORDER BY o.bearbeitet_am
        LIMIT greatest(1, least(p_anzahl, 100))
        FOR UPDATE OF o SKIP LOCKED
    ), beansprucht AS (
        UPDATE public.event_meldungen m
        SET mail_beansprucht_am = now(), mail_versuche = m.mail_versuche + 1
        FROM gewaehlt g
        WHERE m.id = g.id
        RETURNING m.id, m.kontakt_email, m.kontakt_name, m.kontakt_rolle, m.event_id
    )
    SELECT b.id, b.kontakt_email, b.kontakt_name, b.kontakt_rolle,
           e.titel, e.datum, e.datum_bis, e.uhrzeit, e.ort, e.kategorie, e.slug, e.id
    FROM beansprucht b
    JOIN public.events e ON e.id = b.event_id;
$$;

-- Mailserver hat die Mail angenommen
CREATE OR REPLACE FUNCTION public.meldung_mail_versandt(p_id UUID)
RETURNS VOID
LANGUAGE sql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
    UPDATE public.event_meldungen
    SET mail_status = 'gesendet', mail_gesendet_am = now(), mail_beansprucht_am = NULL
    WHERE id = p_id AND mail_status = 'offen';
$$;

-- Versand gescheitert → wieder offen; nach dem dritten Versuch 'fehler' (wird im Dashboard angezeigt)
CREATE OR REPLACE FUNCTION public.meldung_mail_freigeben(p_id UUID)
RETURNS VOID
LANGUAGE sql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
    UPDATE public.event_meldungen
    SET mail_beansprucht_am = NULL,
        mail_status = CASE WHEN mail_versuche >= 3 THEN 'fehler' ELSE 'offen' END
    WHERE id = p_id AND mail_status = 'offen';
$$;

-- Nur der Job (Service-Key) darf die Funktionen aufrufen
DO $$
DECLARE f TEXT;
BEGIN
    FOREACH f IN ARRAY ARRAY[
        'meldung_mail_beanspruchen(integer)',
        'meldung_mail_versandt(uuid)',
        'meldung_mail_freigeben(uuid)'
    ] LOOP
        EXECUTE format('ALTER FUNCTION public.%s OWNER TO postgres', f);
        EXECUTE format('REVOKE EXECUTE ON FUNCTION public.%s FROM PUBLIC, anon, authenticated', f);
        EXECUTE format('GRANT EXECUTE ON FUNCTION public.%s TO service_role', f);
    END LOOP;
END $$;

COMMIT;


-- ── Kontrolle ────────────────────────────────────────────────────────────────
-- Erwartet: 4 Spalten; 3 meldung_mail_*-Funktionen mit anon_darf = false und authenticated_darf = false;
-- mail_offen = Zahl der seit dem Deploy freigegebenen Meldungen (vor dem Deploy 0); pruefregel enthält 'entfallen'.
SELECT 'spalte' AS art, column_name AS name, NULL::boolean AS anon_darf, NULL::boolean AS authenticated_darf
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'event_meldungen'
  AND column_name IN ('mail_status', 'mail_versuche', 'mail_beansprucht_am', 'mail_gesendet_am')
UNION ALL
SELECT 'funktion', p.proname, has_function_privilege('anon', p.oid, 'EXECUTE'), has_function_privilege('authenticated', p.oid, 'EXECUTE')
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public' AND p.proname IN ('meldung_mail_beanspruchen', 'meldung_mail_versandt', 'meldung_mail_freigeben')
UNION ALL
SELECT 'mail_offen', count(*)::text, NULL, NULL FROM public.event_meldungen WHERE mail_status = 'offen'
UNION ALL
SELECT 'pruefregel', pg_get_constraintdef(c.oid), NULL, NULL FROM pg_constraint c
WHERE c.conname = 'event_meldungen_mail_status_check'
ORDER BY 1, 2;
