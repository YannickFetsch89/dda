-- Pitcher gehört zu den Bars, nicht zu den Clubs (Auftraggeber 12.11.2026: eher Bar, wie Konvex; sonst doppelt geführt).
-- Im Supabase SQL-Editor ausführen. Die Kneipen-Seite /guides/kneipen-bars/pitcher-flingern bleibt (Score 8, sichtbar);
-- die Club-URL /guides/clubs/pitcher-flingern leitet danach dauerhaft (308, über den Proxy) dorthin.
UPDATE public.orte
SET extras = (extras - 'auch_club')
             || jsonb_build_object('kein_club', 'Auftraggeber 12.11.2026: eher Bar, wie Konvex; keine doppelte Führung')
WHERE slug = 'pitcher-flingern' AND typ = 'kneipe';

-- Kontrolle: erwartet kneipe, aktiv, Score 8, auch_club leer, kein_club gesetzt
SELECT name, typ, aktiv, qualitaets_score, extras->'auch_club' AS auch_club, extras->>'kein_club' AS kein_club
FROM public.orte WHERE slug = 'pitcher-flingern';
