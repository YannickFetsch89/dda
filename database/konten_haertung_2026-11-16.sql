-- Härtung vor den Nutzerkonten – DiesDasDüsseldorf, 16.11.2026
-- Plan docs/plan-nutzerkonten-2026-11-16.md, Abschnitt 4.0 und Schritt 1 in Abschnitt 15.
--
-- WARUM: Die Rechte-Prüfung (konten_rechte_pruefung_2026-11-16.sql) hat gezeigt, dass anon und authenticated
-- auf den Tabellen in public noch die Supabase-Standardrechte TRUNCATE, REFERENCES und TRIGGER haben.
-- TRUNCATE leert eine Tabelle ohne Rücksicht auf Row Level Security. Über die Supabase-API (PostgREST) ist
-- TRUNCATE nicht erreichbar, und anon/authenticated können sich nicht direkt an der Datenbank anmelden.
-- Die Lücke ist also heute nur theoretisch. Sobald sich jeder ein Konto anlegen kann, soll aber kein Recht
-- mehr übrig sein, das RLS umgeht. Kein Code im Repo nutzt TRUNCATE, REFERENCES oder TRIGGER über diese Rollen.
--
-- WAS PASSIERT:
--   1 Entzieht anon und authenticated TRUNCATE, REFERENCES und TRIGGER auf allen Tabellen in public.
--   2 Sorgt dafür, dass neue Tabellen in public diese Rechte gar nicht erst bekommen (Standardrechte für
--     Tabellen, die postgres anlegt – so legt der SQL-Editor sie an).
--   3 Zeigt zur Kontrolle, ob noch eines dieser Rechte übrig ist. Erwartet: genau eine Zeile „ok“.
--
-- SELECT, INSERT, UPDATE und DELETE bleiben unverändert; die regelt weiterhin RLS.
-- Kann gefahrlos mehrfach ausgeführt werden. Wird im Supabase-SQL-Editor ausgeführt (als postgres).
-- Danach bitte konten_rechte_pruefung_2026-11-16.sql noch einmal laufen lassen: Prüfung 3 darf dann kein
-- „LÜCKE: TRUNCATE umgeht RLS“ mehr zeigen.
--
-- RÜCKBAU (nur falls nötig, nicht empfohlen):
--   GRANT TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA public TO anon, authenticated;
--   ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
--       GRANT TRUNCATE, REFERENCES, TRIGGER ON TABLES TO anon, authenticated;

BEGIN;

-- 1 Bestehende Tabellen
REVOKE TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA public FROM anon, authenticated;

-- 2 Künftige Tabellen (von postgres angelegt)
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    REVOKE TRUNCATE, REFERENCES, TRIGGER ON TABLES FROM anon, authenticated;

COMMIT;

-- 3 Kontrolle: übrig gebliebene Rechte dieser Art (bestehende Tabellen und Standardrechte)
WITH
rest_tabellen AS (
    SELECT 'Tabelle'::text AS art,
           n.nspname::text || '.' || c.relname::text AS objekt,
           r.rolle::text AS rolle,
           concat_ws(', ',
               CASE WHEN has_table_privilege(r.rolle, c.oid, 'TRUNCATE')   THEN 'TRUNCATE'   END,
               CASE WHEN has_table_privilege(r.rolle, c.oid, 'REFERENCES') THEN 'REFERENCES' END,
               CASE WHEN has_table_privilege(r.rolle, c.oid, 'TRIGGER')    THEN 'TRIGGER'    END) AS rechte
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    CROSS JOIN (VALUES ('anon'::name), ('authenticated'::name)) r(rolle)
    WHERE n.nspname = 'public'
      AND c.relkind IN ('r', 'p', 'v', 'm', 'f')
),
rest_standard AS (
    SELECT 'Standardrecht neuer Tabellen'::text AS art,
           'Eigentümer ' || d.defaclrole::regrole::text AS objekt,
           a.grantee::regrole::text AS rolle,
           a.privilege_type::text AS rechte
    FROM pg_default_acl d
    JOIN pg_namespace n ON n.oid = d.defaclnamespace
    CROSS JOIN LATERAL aclexplode(d.defaclacl) a
    WHERE n.nspname = 'public'
      AND d.defaclobjtype = 'r'
      AND a.grantee IN ('anon'::regrole::oid, 'authenticated'::regrole::oid)
      AND a.privilege_type IN ('TRUNCATE', 'REFERENCES', 'TRIGGER')
),
rest AS (
    SELECT * FROM rest_tabellen WHERE rechte <> ''
    UNION ALL
    SELECT * FROM rest_standard
)
SELECT art, objekt, rolle, rechte,
       CASE WHEN art = 'Tabelle' THEN 'NOCH OFFEN: bitte an Claude geben'
            ELSE 'prüfen: Standardrecht eines anderen Eigentümers (z. B. supabase_admin), an Claude geben' END AS bewertung
FROM rest
UNION ALL
SELECT 'Kontrolle', 'public', 'anon, authenticated', '–',
       'ok (kein TRUNCATE, REFERENCES oder TRIGGER mehr auf bestehenden Tabellen)'
WHERE NOT EXISTS (SELECT 1 FROM rest WHERE art = 'Tabelle')
ORDER BY 1, 2, 3;
