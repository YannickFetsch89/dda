-- Redaktions-Schalter „nicht empfehlen“ (Auftraggeber 23.11.2026)
-- Ein Event mit nicht_empfehlen = true erscheint nie als Tipp des Tages, Pick, „Beliebt“, Wochenend-Tipp,
-- Highlight der Woche, Top-Event des Monats, „Für dich“ oder in der Magazin-Auswahl. Der Schalter schlägt alle Flaggen.
-- In Kalender, Suche, Kategorie-, Stadtteil- und Eventseiten bleibt das Event sichtbar (anders als abgelehnt).
-- Setzen im Dashboard über den Button „🙈 Nicht empfehlen“.
--
-- VOR dem Deploy ausführen: Das Dashboard liest die Spalte direkt. Die Website käme auch ohne sie aus.

BEGIN;

ALTER TABLE events ADD COLUMN IF NOT EXISTS nicht_empfehlen BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN events.nicht_empfehlen IS
  'Redaktion: nie empfehlen (Tipp, Picks, Beliebt, Wochenende, Highlight/Top, Für dich, Magazin). Bleibt im Kalender sichtbar.';

-- Erster Einsatz: „Magie der Travestie – Die Nacht der Ikonen“ (Capitol Theater, 28.11.2026) aus den Picks nehmen
UPDATE events
SET nicht_empfehlen = true
WHERE id = '8f3bcd69-694c-4a70-a045-092c8bd39ce4'
  AND slug = 'magie-der-travestie-die-nacht-der-ikonen-capitol-theater-duesseldo-2026-11-28';

-- Kontrolle: erwartet 1 Zeile mit nicht_empfehlen = true
SELECT id, titel, datum, nicht_empfehlen FROM events WHERE nicht_empfehlen;

COMMIT;
