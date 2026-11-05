-- SEO-Entscheidungen: Weiterleitungsziel strenger prüfen – DiesDasDüsseldorf, 05.11.2026
-- Browser und URL-Parser entfernen Tab/Zeilenumbruch und lesen „\“ wie „/“; Punkt-Segmente lösen sich
-- auf. Aus „/<Tab>/evil.com“ oder „/.//evil.com“ würde so „//evil.com“ (fremde Domain). Deshalb:
--   - keine Steuerzeichen, kein Leerraum, kein Backslash im ganzen Ziel
--   - im Pfad (vor „?“) kein „//“, keine Punkt-Segmente („/.“), keine kodierten . / \ (%2e %2f %5c)
-- Gleiche Regel wie zielErlaubt() in web/lib/seo-entscheidungen.ts.

ALTER TABLE public.event_seo_entscheidungen DROP CONSTRAINT IF EXISTS event_seo_entscheidungen_ziel_check;
ALTER TABLE public.event_seo_entscheidungen DROP CONSTRAINT IF EXISTS event_seo_ziel_intern;
ALTER TABLE public.event_seo_entscheidungen ADD CONSTRAINT event_seo_ziel_intern CHECK (
    ziel IS NULL OR (
        ziel ~ '^/[^/]'
        AND ziel !~ '[[:cntrl:][:space:]\\]'
        AND split_part(ziel, '?', 1) !~* '(//|/\.|%2e|%2f|%5c)'
        AND length(ziel) <= 500
    )
);

-- Kontrolle: muss genau eine Zeile „event_seo_ziel_intern“ liefern, die alte Regel ist weg
SELECT conname, pg_get_constraintdef(oid) AS regel
FROM pg_constraint
WHERE conrelid = 'public.event_seo_entscheidungen'::regclass AND contype = 'c' AND conname LIKE '%ziel%';
