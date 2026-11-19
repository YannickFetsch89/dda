-- Rennbahn-Weihnacht und Further Nikolausmarkt nur als Events, nicht als Weihnachtsmarkt-Seite (Auftraggeber 19.11.2026).
-- Beide wurden inaktiv angelegt und nie freigeschaltet – die Zeilen werden gelöscht. Vor der Freischalt-SQL ausführen.
DELETE FROM public.orte
WHERE typ = 'weihnachtsmarkt'
  AND aktiv = false
  AND extras->'weihnachtsmarkt'->>'schluessel' IN ('rennbahn-weihnacht', 'further-nikolausmarkt')
RETURNING slug, name;
