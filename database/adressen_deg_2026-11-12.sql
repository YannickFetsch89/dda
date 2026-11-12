-- Nachtrag: DEG-Heimspiele mit falscher Adresse – DiesDasDüsseldorf, 12.11.2026
-- Der DEG-Scraper schrieb für den PSD Bank Dome die Kurzform der Adresse der Mitsubishi Electric Halle
-- („Siegburger Str. 15“). adressen_dlive_2026-11-12.sql hatte nur die ausgeschriebene Form erfasst.
-- scraper/tier3/deg.py ist korrigiert. Nur dieses kurze SQL ausführen (das große ist schon gelaufen).

UPDATE public.events SET adresse = 'Theodorstraße 281, 40472 Düsseldorf', stadtteil = 'Rath'
WHERE ort ILIKE '%psd bank dome%' AND adresse = 'Siegburger Str. 15, 40591 Düsseldorf';

-- Kontrolle: Dome-Termine mit Adresse
SELECT ort, adresse, stadtteil, COUNT(*) AS anzahl
FROM public.events WHERE ort ILIKE '%psd bank dome%'
GROUP BY ort, adresse, stadtteil ORDER BY anzahl DESC;
