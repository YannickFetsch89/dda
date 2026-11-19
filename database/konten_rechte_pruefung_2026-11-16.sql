-- Rechte-Prüfung vor den Nutzerkonten – DiesDasDüsseldorf, 16.11.2026
-- Plan docs/plan-nutzerkonten-2026-11-16.md, Abschnitt 4.0 und Schritt 1 in Abschnitt 15.
--
-- WARUM: Sobald sich jeder ein Konto anlegen kann, ist jede angemeldete Person in der Rolle „authenticated“.
-- Viele Admin-Regeln hängen heute an „authenticated“ plus ist_admin(). Eine Tabelle ohne RLS oder mit zu weiter
-- Policy wäre dann für alle Kontoinhaber offen. Diese Abfrage listet alles auf, was dafür in Frage kommt.
--
-- NUR LESEND. Ändert nichts. Wird im Supabase-SQL-Editor ausgeführt (als postgres).
-- Der SQL-Editor zeigt nur das Ergebnis der letzten Anweisung, deshalb ist alles EINE Abfrage mit einer Tabelle:
--   nr | pruefung | objekt | detail | bewertung
-- Ergebnis bitte vollständig an Claude geben (Export als CSV oder alle Zeilen kopieren).
--
-- Bewertung:
--   „LÜCKE …“         muss vor dem Einschalten der Registrierung geschlossen werden (Härtungs-SQL folgt)
--   „prüfen …“         Claude sieht es sich an; oft gewollt (z. B. öffentlicher Bucket für Event-Bilder)
--   „ok …“             nichts zu tun
--
-- Prüfungen:
--   1 Tabellen in public/storage ohne Row Level Security
--   2 Policies, die für public, anon oder authenticated gelten, mit Bindung an Admin/Person/service_role
--   3 Schreibrechte (INSERT, UPDATE, DELETE, TRUNCATE) für anon und authenticated
--   4 Views, die anon oder authenticated lesen dürfen (Views umgehen RLS, wenn security_invoker fehlt)
--   5 SECURITY-DEFINER-Funktionen in public, die anon oder authenticated aufrufen dürfen
--   6 Storage-Buckets und ob sie öffentlich sind
--   0 Übersicht (Zahl der geprüften Objekte)
--
-- Gewollt öffentlich lesbar (Whitelist aus Plan 4.0, nur SELECT): events, event_seo_entscheidungen, reihen, orte,
-- ab Schritt 3 zusätzlich einwilligungstexte; ab 19.11.2026 magazin_beitraege und magazin_autoren (Plan Redaktion 3.1).

WITH
tabellen AS (
    SELECT c.oid,
           n.nspname::text AS schema_name,
           c.relname::text AS tabelle,
           c.relkind,
           c.relrowsecurity AS rls,
           c.reloptions
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname IN ('public', 'storage')
      AND c.relkind IN ('r', 'p', 'v', 'm', 'f')
),
whitelist (schema_name, tabelle) AS (
    VALUES ('public', 'events'),
           ('public', 'event_seo_entscheidungen'),
           ('public', 'reihen'),
           ('public', 'orte'),
           ('public', 'einwilligungstexte'),  -- ab Schritt 3: Wortlaute der Einwilligungen sind öffentlich (Plan 4.4)
           ('public', 'magazin_beitraege'),   -- Magazin (Plan Redaktion 3.1): nur veröffentlichte, nur öffentliche Spalten
           ('public', 'magazin_autoren')      -- Magazin: aktive Pseudonyme, nur öffentliche Spalten
),
rollen (rolle) AS (
    VALUES ('anon'::name), ('authenticated'::name)
),
rechte AS (
    SELECT t.oid, t.schema_name, t.tabelle, t.relkind, t.rls, t.reloptions, r.rolle,
           has_any_column_privilege(r.rolle, t.oid, 'SELECT') AS darf_lesen,
           has_any_column_privilege(r.rolle, t.oid, 'INSERT') AS darf_einfuegen,
           has_any_column_privilege(r.rolle, t.oid, 'UPDATE') AS darf_aendern,
           has_table_privilege(r.rolle, t.oid, 'DELETE')      AS darf_loeschen,
           has_table_privilege(r.rolle, t.oid, 'TRUNCATE')    AS darf_leeren
    FROM tabellen t
    CROSS JOIN rollen r
),

-- 1 Tabellen ohne RLS
p1 AS (
    SELECT 1 AS nr,
           'Tabelle ohne Row Level Security'::text AS pruefung,
           schema_name || '.' || tabelle AS objekt,
           'anon/authenticated dürfen: ' || coalesce(nullif(concat_ws(', ',
               CASE WHEN bool_or(darf_lesen)     THEN 'lesen'    END,
               CASE WHEN bool_or(darf_einfuegen) THEN 'einfügen' END,
               CASE WHEN bool_or(darf_aendern)   THEN 'ändern'   END,
               CASE WHEN bool_or(darf_loeschen)  THEN 'löschen'  END,
               CASE WHEN bool_or(darf_leeren)    THEN 'leeren'   END), ''), 'nichts') AS detail,
           CASE WHEN bool_or(darf_lesen OR darf_einfuegen OR darf_aendern OR darf_loeschen OR darf_leeren)
                THEN 'LÜCKE: Rechte für anon/authenticated, aber keine RLS'
                ELSE 'ok (keine Rechte für anon/authenticated)' END AS bewertung
    FROM rechte
    WHERE relkind IN ('r', 'p') AND NOT rls
    GROUP BY schema_name, tabelle
),

-- 2 Policies für public/anon/authenticated
-- Bewertung (zweite Fassung nach Cursor-Prüfung 16.11.2026): Ein Ausdruck gilt nur dann als gebunden, wenn er
-- nach dem Ersetzen der bekannten Bindungen vollständig aufgeht. Bekannte Bindungen (#b): ist_admin(),
-- auth.role() = 'service_role', <spalte> = auth.uid(). Bucket-Filter (#f): bucket_id = '…', nur mit AND.
-- Erlaubte Formen: #b, #b OR #b …, #f AND #b, #b AND #f. Alles andere (z. B. „auth.uid() IS NOT NULL“,
-- „ist_admin() OR true“, „bucket_id = 'x' OR ist_admin()“, fehlendes WITH CHECK bei INSERT) ergibt „prüfen“.
-- Geprüft werden je Befehl die Ausdrücke, die Postgres wirklich anwendet: SELECT/DELETE nur USING, INSERT nur
-- WITH CHECK, UPDATE/ALL beide (fehlt WITH CHECK, gilt USING auch als Prüfung).
pol_ausdruck AS (
    SELECT pol.schemaname, pol.tablename, pol.policyname, a.art,
           btrim(regexp_replace(regexp_replace(regexp_replace(regexp_replace(regexp_replace(regexp_replace(
               lower(coalesce(a.ausdruck, '')),
               '\(\s*select\s+(auth\.[a-z_]+\(\))\s+as\s+[a-z_]+\s*\)', '\1', 'g'),
               '(public\.)?ist_admin\(\)|auth\.role\(\)\s*=\s*''service_role''(::text)?', '#b', 'g'),
               '[a-z_]+\s*=\s*auth\.uid\(\)|auth\.uid\(\)\s*=\s*[a-z_]+', '#b', 'g'),
               'bucket_id\s*=\s*''[^'']*''(::text)?', '#f', 'g'),
               '[()]', ' ', 'g'),
               '\s+', ' ', 'g')) AS rest
    FROM pg_policies pol
    CROSS JOIN LATERAL (
        SELECT 'USING'::text AS art, pol.qual AS ausdruck
        WHERE pol.cmd IN ('SELECT', 'DELETE', 'UPDATE', 'ALL')
        UNION ALL
        SELECT 'WITH CHECK', CASE WHEN pol.cmd = 'INSERT' THEN pol.with_check
                                  ELSE coalesce(pol.with_check, pol.qual) END
        WHERE pol.cmd IN ('INSERT', 'UPDATE', 'ALL')
    ) a
    WHERE pol.schemaname IN ('public', 'storage')
      AND pol.roles && ARRAY['public', 'anon', 'authenticated']::name[]
),
pol_bindung AS (
    SELECT schemaname, tablename, policyname,
           bool_and(rest ~ '^(#f and )?#b(( and| or) #b)*( and #f)?$') AS gebunden,
           string_agg(CASE WHEN rest !~ '^(#f and )?#b(( and| or) #b)*( and #f)?$'
                           THEN art || ' Rest: ' || coalesce(nullif(rest, ''), '(leer = alles erlaubt)') END, '; ') AS rest
    FROM pol_ausdruck
    GROUP BY schemaname, tablename, policyname
),
p2 AS (
    SELECT 2 AS nr,
           'Policy für public/anon/authenticated'::text AS pruefung,
           pol.schemaname::text || '.' || pol.tablename::text || ' – ' || pol.policyname::text AS objekt,
           'Befehl: ' || pol.cmd || '; ' || pol.permissive || '; Rollen: ' || array_to_string(pol.roles, ', ')
               || '; USING: ' || coalesce(pol.qual, '–')
               || '; WITH CHECK: ' || coalesce(pol.with_check, '–')
               || coalesce('; nicht aufgegangen: ' || b.rest, '') AS detail,
           CASE
               WHEN b.gebunden
                   THEN 'ok (an Admin, Person oder service_role gebunden)'
               WHEN pol.cmd = 'SELECT'
                    AND (pol.schemaname::text, pol.tablename::text) IN (SELECT w.schema_name, w.tabelle FROM whitelist w)
                   THEN 'ok (gewollter öffentlicher Leseweg, Whitelist 4.0)'
               ELSE 'LÜCKE prüfen: Bedingung nicht eindeutig an Admin, Person oder service_role gebunden'
           END AS bewertung
    FROM pg_policies pol
    LEFT JOIN pol_bindung b
           ON b.schemaname = pol.schemaname AND b.tablename = pol.tablename AND b.policyname = pol.policyname
    WHERE pol.schemaname IN ('public', 'storage')
      AND pol.roles && ARRAY['public', 'anon', 'authenticated']::name[]
),

-- 3 Schreibrechte je Rolle
p3 AS (
    SELECT 3 AS nr,
           ('Schreibrecht für ' || rolle)::text AS pruefung,
           schema_name || '.' || tabelle AS objekt,
           concat_ws(', ',
               CASE WHEN darf_einfuegen THEN 'INSERT'   END,
               CASE WHEN darf_aendern   THEN 'UPDATE'   END,
               CASE WHEN darf_loeschen  THEN 'DELETE'   END,
               CASE WHEN darf_leeren    THEN 'TRUNCATE' END) AS detail,
           CASE
               WHEN relkind IN ('v', 'm') THEN 'LÜCKE prüfen: Schreibrecht auf einer View'
               WHEN darf_leeren          THEN 'LÜCKE: TRUNCATE umgeht RLS'
               WHEN rls                  THEN 'prüfen: RLS an, die Policies aus Prüfung 2 entscheiden'
               ELSE 'LÜCKE: Schreibrecht ohne RLS'
           END AS bewertung
    FROM rechte
    WHERE darf_einfuegen OR darf_aendern OR darf_loeschen OR darf_leeren
),

-- 4 Views, die anon/authenticated lesen dürfen
p4 AS (
    SELECT 4 AS nr,
           'View lesbar für anon/authenticated'::text AS pruefung,
           schema_name || '.' || tabelle AS objekt,
           'lesbar für: ' || string_agg(rolle::text, ', ' ORDER BY rolle)
               || '; security_invoker: '
               || coalesce((SELECT o.option_value FROM pg_options_to_table(reloptions) o
                            WHERE o.option_name = 'security_invoker'), 'aus') AS detail,
           CASE WHEN coalesce((SELECT o.option_value FROM pg_options_to_table(reloptions) o
                               WHERE o.option_name = 'security_invoker'), 'false') IN ('true', 'on', '1')
                THEN 'ok (läuft mit den Rechten der aufrufenden Person)'
                ELSE 'LÜCKE prüfen: View läuft mit den Rechten des Eigentümers und umgeht RLS'
           END AS bewertung
    FROM rechte
    WHERE relkind IN ('v', 'm') AND darf_lesen
    GROUP BY schema_name, tabelle, reloptions
),

-- 5 SECURITY-DEFINER-Funktionen, die anon/authenticated aufrufen dürfen
p5 AS (
    SELECT 5 AS nr,
           'SECURITY-DEFINER-Funktion aufrufbar'::text AS pruefung,
           n.nspname::text || '.' || p.proname::text || '(' || pg_get_function_identity_arguments(p.oid) || ')' AS objekt,
           'anon: ' || has_function_privilege('anon', p.oid, 'EXECUTE')::text
               || ', authenticated: ' || has_function_privilege('authenticated', p.oid, 'EXECUTE')::text
               || ', Eigentümer: ' || p.proowner::regrole::text
               || ', search_path fest: ' || (coalesce(array_to_string(p.proconfig, ','), '') LIKE '%search_path=%')::text AS detail,
           CASE
               WHEN p.prorettype = 'trigger'::regtype THEN 'ok (Trigger-Funktion, nicht direkt aufrufbar)'
               WHEN p.proname = 'ist_admin'          THEN 'ok (gewollt, auth_rollen.sql)'
               WHEN p.proname = 'merk_statistik'
                    AND NOT has_function_privilege('anon', p.oid, 'EXECUTE')
                                                     THEN 'ok (nur authenticated, Admin-Prüfung innen, Plan 4.5)'
               ELSE 'prüfen: läuft mit Eigentümerrechten'
           END AS bewertung
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
      AND p.prosecdef
      AND (has_function_privilege('anon', p.oid, 'EXECUTE')
           OR has_function_privilege('authenticated', p.oid, 'EXECUTE'))
),

-- 6 Storage-Buckets
p6 AS (
    SELECT 6 AS nr,
           'Storage-Bucket'::text AS pruefung,
           b.id::text AS objekt,
           'öffentlich: ' || b.public::text AS detail,
           CASE WHEN b.public
                THEN 'prüfen: Dateien ohne Anmeldung abrufbar (bei Event-Bildern gewollt?)'
                ELSE 'ok (privat)' END AS bewertung
    FROM storage.buckets b
),

-- 0 Übersicht
p0 AS (
    SELECT 0 AS nr,
           'Übersicht'::text AS pruefung,
           'geprüfte Tabellen und Views in public und storage' AS objekt,
           count(*)::text AS detail,
           'Info' AS bewertung
    FROM tabellen
)

SELECT nr, pruefung, objekt, detail, bewertung
FROM (
    SELECT * FROM p0
    UNION ALL SELECT * FROM p1
    UNION ALL SELECT * FROM p2
    UNION ALL SELECT * FROM p3
    UNION ALL SELECT * FROM p4
    UNION ALL SELECT * FROM p5
    UNION ALL SELECT * FROM p6
) ergebnis
ORDER BY CASE WHEN bewertung LIKE 'LÜCKE%'  THEN 0
              WHEN bewertung LIKE 'prüfen%' THEN 1
              ELSE 2 END,
         nr, objekt;
