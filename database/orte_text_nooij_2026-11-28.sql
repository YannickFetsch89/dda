-- NOOIJ / DUTCH DELI (Flingern): Hinweis Tanzhaus NRW gleich am Anfang (Auftraggeber, 28.11.2026)
begin;
create table if not exists public.orte_texte_sicherung_rest_b_2026_11_28 as
select id, name, beschreibung, now() as gesichert_am from orte where false;
alter table public.orte_texte_sicherung_rest_b_2026_11_28 enable row level security;
insert into public.orte_texte_sicherung_rest_b_2026_11_28 (id, name, beschreibung, gesichert_am)
select id, name, beschreibung, now() from orte where id = '5e59cb84-f7ba-4e1d-a346-4e80a3de709d';
update orte set beschreibung = replace($t$Das Nooij / Dutch Deli befindet sich im **Tanzhaus NRW** in Flingern und ist ein helles, modernes Lokal mit **holländischen Cafégerichten**. Besonders angenehm ist die Atmosphäre: Man fühlt sich schnell wohl und bleibt gern länger sitzen. Wer draußen sitzen möchte, findet auch **Plätze im Freien**.

Das **Frühstück** überzeugt mit einer vielseitigen Karte, in der für jeden Geschmack etwas dabei ist, und alles wird frisch zubereitet. Der Service ist nett und aufmerksam, und die Wartezeiten fallen angenehm kurz aus.

Auch für ein **entspanntes Mittagessen** passt der Ort gut, etwa mit Freunden oder vor einer Vorstellung im Tanzhaus, denn das Essen fällt reichlich aus. Die Einrichtung wirkt sauber und geräumig.$t$, chr(13), '') where id = '5e59cb84-f7ba-4e1d-a346-4e80a3de709d';
commit;

-- Prüfung: Text beginnt mit dem Tanzhaus-Hinweis
select name, left(beschreibung, 80) as anfang from orte where id = '5e59cb84-f7ba-4e1d-a346-4e80a3de709d';
