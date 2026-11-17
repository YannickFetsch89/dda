-- konten_rueckbau_2026-11-16.sql – DiesDasDüsseldorf
-- Rückbau zu database/konten_2026-11-16.sql (Plan Schritt 3 in Abschnitt 15, Risiken Abschnitt 17).
--
-- TEIL 1 (sofort wirksam, harmlos): entfernt NUR den Sensibel-Trigger auf events.
--   Für den Fall, dass er die Pipeline stört (z. B. Fehler beim Speichern von Events).
--   Alles andere bleibt. Neue Events werden danach nicht mehr gekennzeichnet; das muss vor dem Einschalten
--   der Konten wieder in Ordnung sein (Trigger neu anlegen = Abschnitt 3 der Migration erneut ausführen).
--
-- TEIL 2 (nur nach ausdrücklicher Entscheidung): entfernt ALLE Objekte der Migration, auch Merklisten,
--   Einwilligungsnachweise und die neuen Profilspalten mit ihren Daten. Läuft nur, wenn unten
--   „teil2_ausfuehren := true“ von Hand eingetragen wird. Vorher Rücksprache mit Claude.
--
-- Wird im Supabase-SQL-Editor als postgres ausgeführt. Wiederholbar.

-- ── TEIL 1 ───────────────────────────────────────────────────────────────────
DROP TRIGGER IF EXISTS events_sensibel_pruefen ON public.events;


-- ── TEIL 2 ───────────────────────────────────────────────────────────────────
DO $$
DECLARE
    teil2_ausfuehren BOOLEAN := false;   -- nur nach ausdrücklicher Entscheidung auf true setzen
BEGIN
    IF NOT teil2_ausfuehren THEN
        RAISE NOTICE 'Teil 2 übersprungen (teil2_ausfuehren = false). Nur Teil 1 wurde ausgeführt.';
        RETURN;
    END IF;

    -- Tabellen zuerst (Reihenfolge wegen Fremdschlüsseln). Ihre Trigger verschwinden mit ihnen.
    DROP TABLE IF EXISTS public.merkliste;
    DROP TABLE IF EXISTS public.einwilligungen;
    DROP TABLE IF EXISTS public.einwilligungstexte;
    DROP TABLE IF EXISTS public.event_sensibel;
    DROP TABLE IF EXISTS public.event_sensibel_ausnahmen;
    DROP TABLE IF EXISTS public.sensibel_regeln;

    -- Danach die Funktionen (der Trigger auf events ist seit Teil 1 weg)
    DROP FUNCTION IF EXISTS public.merk_statistik(DATE, DATE);
    DROP FUNCTION IF EXISTS public.konto_protokoll_loeschen(UUID);
    DROP FUNCTION IF EXISTS public.geburtstag_setzen(UUID, DATE, TEXT, TEXT);
    DROP FUNCTION IF EXISTS public.stammdaten_setzen(UUID, TEXT, TEXT, DATE);   -- konten_stammdaten_2026-11-17.sql
    DROP FUNCTION IF EXISTS public.einwilligung_setzen(UUID, TEXT, BOOLEAN, TEXT, TEXT);
    DROP FUNCTION IF EXISTS public.event_sensibel_merkliste_raeumen();
    DROP FUNCTION IF EXISTS public.merkliste_vor_insert();
    DROP FUNCTION IF EXISTS public.events_sensibel_pruefen();
    DROP FUNCTION IF EXISTS public.sensibel_grund(TEXT, TEXT, TEXT);
    DROP FUNCTION IF EXISTS public.einwilligungstexte_schuetzen();

    -- profiles: Prüfbedingungen und neue Spalten
    ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS praeferenzen_form;
    ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS praeferenzen_nur_mit_einwilligung;
    ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS geburtsdatum_nur_mit_einwilligung;
    ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS geburtsdatum_plausibel;
    ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS name_plausibel;
    ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS geburtstagsmail_nur_mit_datum;
    ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS onboarding_nur_mit_stammdaten;
    ALTER TABLE public.profiles
        DROP COLUMN IF EXISTS onboarding_fertig_am,
        DROP COLUMN IF EXISTS mindestalter_bestaetigt_am,
        DROP COLUMN IF EXISTS personalisierung,
        DROP COLUMN IF EXISTS sensible_events_erlaubt,
        DROP COLUMN IF EXISTS analyse_erlaubt,
        DROP COLUMN IF EXISTS nutzungsbedingungen_version,
        DROP COLUMN IF EXISTS geburtstagsmail,
        DROP COLUMN IF EXISTS geburtsdatum,
        DROP COLUMN IF EXISTS geburtstagsmail_zuletzt,
        DROP COLUMN IF EXISTS unter16_gesperrt_am,
        DROP COLUMN IF EXISTS letzte_aktivitaet_am,
        DROP COLUMN IF EXISTS merkliste_begonnen_am,
        DROP COLUMN IF EXISTS vorname,
        DROP COLUMN IF EXISTS nachname;

    -- profiles: Rechte wie vor der Migration für authenticated (UPDATE auf das eigene Profil per Policy).
    -- anon bleibt ohne Rechte; vorher hatte anon nur Supabase-Standardrechte ohne Policy, also ohne Wirkung.
    GRANT UPDATE ON public.profiles TO authenticated;

    RAISE NOTICE 'Teil 2 ausgeführt: alle Objekte der Konten-Migration entfernt.';
END $$;

-- Kontrolle: Trigger auf events vorhanden? (nach Teil 1 erwartet: keine Zeile)
SELECT tgname AS trigger_auf_events
FROM pg_trigger
WHERE tgrelid = 'public.events'::regclass
  AND tgname = 'events_sensibel_pruefen';
