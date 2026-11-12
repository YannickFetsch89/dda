-- Club-Guide A/B/C (12.11.2026) – im Supabase SQL-Editor ausführen, VOR dem Deploy.
--
-- 1) Konvex gehört zu den Bars, nicht zu den Clubs (Auftraggeber 12.11.2026: DJ-Nächte und Konzerte, aber kein Club).
--    - aus dem Club-Hub: auch_club entfernen, kein_club setzen (der Club-Import markiert den Ort nie wieder)
--    - im Bar-Hub sichtbar: qualitaets_score 7 (Schwelle der Website), redaktionell festgelegt (score_manuell –
--      die automatische Neubewertung lässt den Wert dann stehen)
--    Die alte Club-URL /guides/clubs/konvex-flingern leitet danach dauerhaft (301) auf /guides/kneipen-bars/konvex-flingern.
UPDATE public.orte
SET qualitaets_score = 7,
    extras = (extras - 'auch_club')
             || jsonb_build_object(
                  'kein_club', 'Auftraggeber 12.11.2026: Bar mit DJ-Nächten und Konzerten, kein Club',
                  'score_manuell', 'Auftraggeber 12.11.2026: Konvex im Bar-Hub'
                )
WHERE slug = 'konvex-flingern' AND typ = 'kneipe';

-- 2) Alle Clubs mit passendem Profil sichtbar schalten (bisher nur freigegebene mit Club-Score ≥ 7).
--    Die Website stuft sie selbst ein: A = Top-Empfehlung (Freigabe + Score ≥ 7), B = Score ≥ 5, C = übrige.
--    Erwartet: 25 Zeilen.
UPDATE public.orte
SET aktiv = true
WHERE typ = 'club'
  AND aktiv = false
  AND extras->'club'->>'passt' = 'true'
  AND NOT (extras ? 'kein_club');

-- Kontrolle 1: Konvex – erwartet: kneipe, aktiv, Score 7, auch_club leer, kein_club gesetzt
SELECT name, typ, aktiv, qualitaets_score, extras->'auch_club' AS auch_club, extras->>'kein_club' AS kein_club
FROM public.orte WHERE slug = 'konvex-flingern';

-- Kontrolle 2: Club-Zeilen nach Sichtbarkeit – erwartet: aktiv=true/passt=true 31, aktiv=false nur passt=false (6)
SELECT aktiv, extras->'club'->>'passt' AS passt, COUNT(*) AS anzahl
FROM public.orte WHERE typ = 'club'
GROUP BY aktiv, passt ORDER BY aktiv DESC, passt;
