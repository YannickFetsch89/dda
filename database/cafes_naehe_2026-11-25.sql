-- Cafés in der Nähe von Spielplätzen (Auftraggeber 25.11.2026)
-- Auf den Spielplatz-Seiten erscheinen neben den Guide-Cafés (Score ≥ 7, mit Pill „Empfehlung“) auch Cafés mit
-- Score 5 und 6, die im Café-Guide bewusst nicht stehen (aktiv = false). Die Website liest sie über diese Ansicht,
-- weil die Zeilen-Regeln (RLS) inaktive Orte für Besucher sonst verbergen.
--
-- Nur wenige, ohnehin öffentliche Felder (Name, Lage, Google-Bewertung, Google-Maps-Link). Geschlossene Orte
-- (Eintrag in ort_weiterleitungen, Admin „Schließen“) bleiben draußen.
-- Die Website kommt auch ohne diese Ansicht aus (dann wie bisher nur Guide-Cafés). Wiederholbar.

BEGIN;

CREATE OR REPLACE VIEW public.cafes_naehe AS
SELECT o.id,
       o.name,
       o.slug,
       o.stadtteil,
       o.latitude,
       o.longitude,
       o.qualitaets_score,
       o.aktiv,
       o.google_rating,
       o.google_bewertungen_anzahl,
       o.extras ->> 'google_maps_url' AS google_maps_url
FROM public.orte o
WHERE o.typ = 'cafe'
  AND o.qualitaets_score >= 5
  AND o.latitude IS NOT NULL
  AND o.longitude IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM public.ort_weiterleitungen w WHERE w.alter_slug = o.slug);

COMMENT ON VIEW public.cafes_naehe IS
  'Cafés ab Score 5 für „Cafés in der Nähe“ auf Spielplatz-Seiten; ohne geschlossene Orte. Nur Lesen.';

REVOKE ALL ON public.cafes_naehe FROM PUBLIC;
GRANT SELECT ON public.cafes_naehe TO anon, authenticated;

-- Kontrolle: erwartet rund 279 Zeilen, davon rund 136 aktiv (Guide)
SELECT count(*) AS cafes, count(*) FILTER (WHERE aktiv) AS davon_im_guide FROM public.cafes_naehe;

COMMIT;
