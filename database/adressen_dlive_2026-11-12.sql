-- d.live: falsche Adressen und zwei Rest-Zuordnungen korrigieren – DiesDasDüsseldorf, 12.11.2026
-- Der d.live-Scraper hatte zwei falsche Adressen hinterlegt (scraper/tier2/dlive.py ist korrigiert):
--   PSD BANK DOME stand mit der Adresse der Mitsubishi Electric Halle (Siegburger Straße 15) in der DB,
--   richtig ist Theodorstraße 281, 40472 Düsseldorf (Rath).
--   CASTELLO stand mit „Auf'm Hennekamp 71, 40225“ (Bilk) in der DB,
--   richtig ist Karl-Hohmann-Straße 1, 40599 Düsseldorf (Reisholz).
-- Die Eventseiten zeigen die Adresse und die Karte – deshalb auch den Bestand korrigieren.
-- Außerdem: eine Zeile „Mitsubishi Electric  Halle“ (doppeltes Leerzeichen) stand unter Friedrichstadt.
-- Im Supabase-SQL-Editor als Ganzes ausführen.

BEGIN;

UPDATE public.events SET adresse = 'Theodorstraße 281, 40472 Düsseldorf', stadtteil = 'Rath'
WHERE ort ILIKE '%psd bank dome%' AND adresse = 'Siegburger Straße 15, 40591 Düsseldorf';

UPDATE public.events SET adresse = 'Karl-Hohmann-Straße 1, 40599 Düsseldorf', stadtteil = 'Reisholz'
WHERE ort ILIKE '%castello%' AND (adresse = 'Auf''m Hennekamp 71, 40225 Düsseldorf' OR stadtteil = 'Bilk');

UPDATE public.events SET stadtteil = 'Oberbilk'
WHERE regexp_replace(ort, '\s+', ' ', 'g') ILIKE '%mitsubishi electric halle%' AND stadtteil IS DISTINCT FROM 'Oberbilk';

COMMIT;

-- Kontrolle: Hallen mit Stadtteil und Adresse
SELECT stadtteil, ort, adresse, COUNT(*) AS anzahl
FROM public.events
WHERE ort ILIKE '%mitsubishi%' OR ort ILIKE '%psd bank dome%' OR ort ILIKE '%castello%'
GROUP BY stadtteil, ort, adresse
ORDER BY ort, anzahl DESC;
