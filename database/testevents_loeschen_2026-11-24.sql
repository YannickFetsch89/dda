-- testevents_loeschen_2026-11-24.sql – DiesDasDüsseldorf
-- Zwei Test-Events aus dem Livetest der Meldungs-Mail (24.11.2026) endgültig löschen, samt ihrer Test-Meldungen.
-- Abhängige Zeilen (SEO-Entscheidungen, Merklisten, Empfehlungen) hängen per ON DELETE CASCADE bzw. SET NULL daran.
-- Das veröffentlichte Bild bleibt im Bucket event-bilder (meldungen/…) liegen; es ist ohne Event nirgends verlinkt.
-- Die Seiten verschwinden nach dem nächsten Deploy bzw. spätestens mit dem Ablauf des Website-Caches.
--
-- Schritt 1 zeigt, was gelöscht wird. Nur wenn genau die zwei Test-Events erscheinen, Schritt 2 ausführen.

-- ── Schritt 1: Vorschau ──────────────────────────────────────────────────────
SELECT e.id, e.slug, e.titel, e.datum, e.quelle_name,
       (SELECT count(*) FROM public.event_meldungen m WHERE m.event_id = e.id) AS meldungen
FROM public.events e
WHERE e.slug IN ('flohmarkt-in-dd-flingern-test-privat-2026-11-27',
                 'flohmarkt-in-dd-flingern-test-flohmarkthausen-2026-11-27');

-- ── Schritt 2: Löschen (erst nach Prüfung der Vorschau) ──────────────────────
BEGIN;

DELETE FROM public.event_meldungen
WHERE event_id IN (SELECT id FROM public.events
                   WHERE slug IN ('flohmarkt-in-dd-flingern-test-privat-2026-11-27',
                                  'flohmarkt-in-dd-flingern-test-flohmarkthausen-2026-11-27')
                     AND quelle_name = 'Event-Meldung')
RETURNING 'meldung' AS art, id, titel;

DELETE FROM public.events
WHERE slug IN ('flohmarkt-in-dd-flingern-test-privat-2026-11-27',
               'flohmarkt-in-dd-flingern-test-flohmarkthausen-2026-11-27')
  AND quelle_name = 'Event-Meldung'
RETURNING 'event' AS art, id, titel;

COMMIT;
