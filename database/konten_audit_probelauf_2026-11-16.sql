-- Probelauf: Darf postgres in auth.audit_log_entries löschen? – DiesDasDüsseldorf, 16.11.2026
-- Plan docs/plan-nutzerkonten-2026-11-16.md, Abschnitt 4.6 und Schritt 1 in Abschnitt 15.
--
-- WAS PASSIERT: Der Block fügt EINE gekennzeichnete Testzeile ein ({"ddd_test": true}), löscht genau diese
-- wieder und bricht dann ABSICHTLICH mit einer Fehlermeldung ab. Durch den Abbruch wird alles zurückgerollt:
-- Am Ende ist die Tabelle genau wie vorher. Eine echte Zeile wird nie berührt (gelöscht wird nur per ID der
-- Testzeile).
--
-- ERWARTET: Der SQL-Editor zeigt eine rote Fehlermeldung, die mit „PROBELAUF“ beginnt. Das ist gewollt.
-- Bitte diese Meldung vollständig an Claude geben. Sie enthält:
--   Ergebnis       ok = Einfügen und Löschen erlaubt; sonst die Postgres-Fehlermeldung (z. B. permission denied)
--   gelöscht       1 = Testzeile wurde gefunden und gelöscht; 0 = gelöscht werden durfte, aber RLS o. Ä. hat sie
--                  versteckt; -1 = es kam gar nicht bis zum Löschen
--   ausgeführt als die Rolle, mit der später auch die Lösch-Funktion als Eigentümer läuft
--
-- Bitte erst ausführen, wenn konten_audit_pruefung_2026-11-16.sql gelaufen ist und „postgres darf löschen“ true
-- zeigt. Bei false ist dieser Probelauf überflüssig.

DO $$
DECLARE
    test_id   uuid := gen_random_uuid();
    geloescht integer := -1;
    meldung   text := 'ok';
BEGIN
    BEGIN
        INSERT INTO auth.audit_log_entries (id, payload, created_at)
        VALUES (test_id, '{"ddd_test": true}'::json, now());

        DELETE FROM auth.audit_log_entries WHERE id = test_id;
        GET DIAGNOSTICS geloescht = ROW_COUNT;
    EXCEPTION WHEN others THEN
        meldung := SQLSTATE || ' ' || SQLERRM;
    END;

    -- Absichtlicher Abbruch: rollt alles zurück und zeigt das Ergebnis als Meldung
    RAISE EXCEPTION 'PROBELAUF (alles zurückgerollt) – Ergebnis: % | gelöscht: % | ausgeführt als: %',
        meldung, geloescht, current_user;
END
$$;
