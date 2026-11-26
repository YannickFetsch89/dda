-- uhrzeit_hinweis_2026-11-26.sql – DiesDasDüsseldorf
-- Zeitfenster statt fester Uhrzeit (z. B. selbstgeführte Touren „zwischen 09:00–23:00 Uhr“). Die Event-Seite zeigt den
-- Hinweis statt „Uhrzeit siehe Veranstalter“, wenn keine Uhrzeit gesetzt ist; Listen zeigen das Event weiter ganztägig.
-- Im Dashboard unter Events → Bearbeiten → „Uhrzeit-Hinweis“ pflegbar. Wiederholbar.

ALTER TABLE public.events ADD COLUMN IF NOT EXISTS uhrzeit_hinweis TEXT;
ALTER TABLE public.events DROP CONSTRAINT IF EXISTS events_uhrzeit_hinweis_laenge;
ALTER TABLE public.events ADD CONSTRAINT events_uhrzeit_hinweis_laenge
    CHECK (uhrzeit_hinweis IS NULL OR char_length(uhrzeit_hinweis) <= 60);

-- Schatzsuche „Düsseldorf im Winterzauber“ (Event-Meldung von City Adventure, 26.11.2026): Zeitfenster und Bild
UPDATE public.events
SET uhrzeit = NULL,
    uhrzeit_hinweis = 'zwischen 09:00–23:00 Uhr',
    bild_url = '/ort-bilder/events/duesseldorf-im-winterzauber.webp'
WHERE slug = 'duesseldorf-im-winterzauber-deine-weihnachtsschatzsuche-altstadt-duesseldorf-star-2026-11-26'
RETURNING id, titel, uhrzeit, uhrzeit_hinweis, bild_url;
