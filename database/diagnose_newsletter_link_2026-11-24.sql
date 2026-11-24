-- diagnose_newsletter_link_2026-11-24.sql – nur lesen
-- Livetest 24.11.2026: Bestätigungslink „ungültig oder abgelaufen“. Gibt es die Anmeldung aus dem Link noch?
-- Zeigt keine Mailadressen.

SELECT id,
       id = '8a37790f-1658-4a37-aeb2-57232ddfca83' AS aus_dem_link,
       erstellt_am, bestaetigung_gesendet_am, bestaetigung_zugestellt_am, bestaetigt_am, mails_gesendet, abgemeldet_am
FROM public.newsletter_anmeldungen
ORDER BY erstellt_am DESC
LIMIT 10;
