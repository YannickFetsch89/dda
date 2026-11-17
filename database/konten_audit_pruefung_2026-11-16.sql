-- Prüfung des Supabase-Anmeldeprotokolls (auth.audit_log_entries) – DiesDasDüsseldorf, 16.11.2026
-- Plan docs/plan-nutzerkonten-2026-11-16.md, Abschnitt 4.6 und Schritt 1 in Abschnitt 15.
--
-- WARUM: Beim Löschen eines Kontos sollen auch seine Einträge im Anmeldeprotokoll verschwinden. Dafür muss
-- feststehen, (a) ob wir in auth.audit_log_entries löschen dürfen und (b) in welchen Feldern des Payloads
-- Nutzer-ID und Mailadresse stehen. Erst danach wird die Funktion konto_protokoll_loeschen geschrieben.
--
-- NUR LESEND. Ändert nichts. Gibt KEINE Mailadressen, IP-Adressen oder Nutzer-IDs aus, nur Feldnamen,
-- Anzahlen und Zeitpunkte. Wird im Supabase-SQL-Editor ausgeführt (als postgres).
-- Ergebnis bitte vollständig an Claude geben.
--
-- Kommt statt einer Tabelle die Meldung „permission denied for table audit_log_entries“, ist auch das ein
-- Ergebnis: Dann darf postgres die Tabelle nicht lesen (und vermutlich auch nicht löschen). Bitte die Meldung
-- schicken. Die Probe in konten_audit_probelauf_2026-11-16.sql ist dann überflüssig.

WITH
rechte AS (
    SELECT 1 AS reihenfolge, 'Rechte'::text AS bereich, 'ausgeführt als'::text AS schluessel, current_user::text AS wert
    UNION ALL SELECT 2, 'Rechte', 'postgres darf lesen',    has_table_privilege('postgres', 'auth.audit_log_entries', 'SELECT')::text
    UNION ALL SELECT 3, 'Rechte', 'postgres darf einfügen', has_table_privilege('postgres', 'auth.audit_log_entries', 'INSERT')::text
    UNION ALL SELECT 4, 'Rechte', 'postgres darf löschen',  has_table_privilege('postgres', 'auth.audit_log_entries', 'DELETE')::text
    UNION ALL SELECT 5, 'Tabelle', 'RLS an', c.relrowsecurity::text
              FROM pg_class c WHERE c.oid = 'auth.audit_log_entries'::regclass
    UNION ALL SELECT 6, 'Tabelle', 'Eigentümer', c.relowner::regrole::text
              FROM pg_class c WHERE c.oid = 'auth.audit_log_entries'::regclass
    UNION ALL SELECT 7, 'Tabelle', 'Spalten', string_agg(a.attname || ' ' || format_type(a.atttypid, a.atttypmod)
                                                         || CASE WHEN a.attnotnull THEN ' NOT NULL' ELSE '' END, ', ' ORDER BY a.attnum)
              FROM pg_attribute a WHERE a.attrelid = 'auth.audit_log_entries'::regclass AND a.attnum > 0 AND NOT a.attisdropped
    UNION ALL SELECT 8, 'Funktionen', 'Eigentümer von public.ist_admin() (Muster für neue Funktionen)', p.proowner::regrole::text
              FROM pg_proc p WHERE p.oid = 'public.ist_admin()'::regprocedure
),
inhalt AS (
    SELECT 10 AS reihenfolge, 'Inhalt'::text AS bereich, 'Zeilen gesamt'::text AS schluessel, count(*)::text AS wert
    FROM auth.audit_log_entries
    UNION ALL SELECT 11, 'Inhalt', 'älteste Zeile', min(created_at)::text FROM auth.audit_log_entries
    UNION ALL SELECT 12, 'Inhalt', 'neueste Zeile', max(created_at)::text FROM auth.audit_log_entries
),
payload_felder AS (
    SELECT 20 AS reihenfolge, 'Payload-Feld (Anzahl Zeilen)'::text AS bereich, k::text AS schluessel, count(*)::text AS wert
    FROM auth.audit_log_entries e,
         jsonb_object_keys(CASE WHEN jsonb_typeof(e.payload::jsonb) = 'object' THEN e.payload::jsonb ELSE '{}'::jsonb END) k
    GROUP BY k
),
traits_felder AS (
    SELECT 30 AS reihenfolge, 'traits-Feld (Anzahl Zeilen)'::text AS bereich, k::text AS schluessel, count(*)::text AS wert
    FROM auth.audit_log_entries e,
         jsonb_object_keys(CASE WHEN jsonb_typeof(e.payload::jsonb -> 'traits') = 'object'
                                THEN e.payload::jsonb -> 'traits' ELSE '{}'::jsonb END) k
    GROUP BY k
),
aktionen AS (
    SELECT 40 AS reihenfolge, 'Aktion (Anzahl Zeilen)'::text AS bereich,
           coalesce(e.payload::jsonb ->> 'action', '(ohne)') AS schluessel, count(*)::text AS wert
    FROM auth.audit_log_entries e
    GROUP BY 3
),
-- Ob actor_id bzw. traits.user_id wie eine Nutzer-ID aussehen und ob actor_username / traits.user_email
-- wie eine Mailadresse aussehen – nur als Anzahl, ohne Werte auszugeben
formate AS (
    SELECT 50 AS reihenfolge, 'Format (Anzahl Zeilen)'::text AS bereich, 'actor_id ist UUID'::text AS schluessel,
           count(*) FILTER (WHERE e.payload::jsonb ->> 'actor_id' ~* '^[0-9a-f-]{36}$')::text AS wert
    FROM auth.audit_log_entries e
    UNION ALL SELECT 51, 'Format (Anzahl Zeilen)', 'actor_username enthält @',
           count(*) FILTER (WHERE e.payload::jsonb ->> 'actor_username' LIKE '%@%')::text FROM auth.audit_log_entries e
    UNION ALL SELECT 52, 'Format (Anzahl Zeilen)', 'traits.user_id ist UUID',
           count(*) FILTER (WHERE e.payload::jsonb -> 'traits' ->> 'user_id' ~* '^[0-9a-f-]{36}$')::text FROM auth.audit_log_entries e
    UNION ALL SELECT 53, 'Format (Anzahl Zeilen)', 'traits.user_email enthält @',
           count(*) FILTER (WHERE e.payload::jsonb -> 'traits' ->> 'user_email' LIKE '%@%')::text FROM auth.audit_log_entries e
)

SELECT bereich, schluessel, wert
FROM (
    SELECT * FROM rechte
    UNION ALL SELECT * FROM inhalt
    UNION ALL SELECT * FROM payload_felder
    UNION ALL SELECT * FROM traits_felder
    UNION ALL SELECT * FROM aktionen
    UNION ALL SELECT * FROM formate
) ergebnis
ORDER BY reihenfolge, schluessel;
