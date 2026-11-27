-- Restaurants (Auftraggeber, 27.11.2026, Durchsicht der Restaurants)
-- 1) La Latina Eismanufaktur ausblenden (Eisdiele → eigener Eis-Guide später), Zeile bleibt im Bestand
-- 2) Kochi Bismarck (nachgeladen mit scraper/orte/ort_nachladen.py, bisher unsichtbar) freischalten:
--    Google-Score nur 6 (erst 65 Bewertungen) → redaktioneller Score 7 (extras.score_manuell, bleibt bei Neuberechnung)
-- 3) 3 Texte (Josef Dauser, La Noodle, Kochi Bismarck), alter Text in Sicherungstabelle

begin;

update orte
set aktiv = false,
    extras = coalesce(extras, '{}'::jsonb) || jsonb_build_object('ausgeblendet', jsonb_build_object('grund', 'Eisdiele – eigener Eis-Guide später', 'datum', '2026-11-27'))
where id = '28799f21-e312-4dbb-8163-0088e9830c9b';  -- La Latina Eismanufaktur (Gerresheim)

update orte
set aktiv = true,
    qualitaets_score = greatest(coalesce(qualitaets_score, 0), 7),
    extras = coalesce(extras, '{}'::jsonb) || jsonb_build_object('score_manuell', 'Zweite Filiale von Kochi, vom Auftraggeber gewünscht (27.11.2026)')
where id = 'a4aaad30-dfd4-43af-bb9a-854d3a40a29d';  -- Kochi Bismarck (Stadtmitte)

create table if not exists public.orte_texte_sicherung_rest_d_2026_11_27 as
select id, name, beschreibung, now() as gesichert_am from orte where false;
alter table public.orte_texte_sicherung_rest_d_2026_11_27 enable row level security;
insert into public.orte_texte_sicherung_rest_d_2026_11_27 (id, name, beschreibung, gesichert_am)
select id, name, beschreibung, now() from orte where id in (
  'f096d8e6-32ba-4c8d-8ed6-289bdc6e1a58',
  '8bf37d2c-2577-4d46-8901-f0152d697321',
  'a4aaad30-dfd4-43af-bb9a-854d3a40a29d'
);

-- Josef Dauser (Derendorf) – angepasst
update orte set beschreibung = replace($t$Wer **rustikale deutsche Küche** sucht, ist bei Josef Dauser in Derendorf richtig. Auf der Karte stehen fast ausschließlich **Suppen und Eintöpfe**: Linsensuppe, Kartoffelsuppe, Gulaschsuppe und Graupensuppe kommen herzhaft und gut gewürzt auf den Tisch, dazu gibt es **Maultaschen**, die begeistern. Eine große Speisekarte darf man also nicht erwarten, wer aber einen ehrlichen Teller Eintopf wie bei Oma sucht, wird hier glücklich.

Das Lokal wirkt wie eine Kreuzung aus chic und rustikal, und besonders fallen die **bunten Glasfenster** im hinteren Teil auf, im Stil deutscher Küche bemalt. Es gibt viele Sitzplätze mit angenehm viel Abstand zwischen den Tischen, und es ist meist schön ruhig. Der Laden ist sauber und das Personal freundlich.

Praktisch: Essen und Getränke bestellt man gesondert, und man bekommt es schnell, egal ob zum **Mitnehmen** oder zum Hiersitzen. Das Ganze hat Tradition, die **Gulaschkanone** steht seit Jahrzehnten auf dem Carlsplatz.$t$, chr(13), '') where id = 'f096d8e6-32ba-4c8d-8ed6-289bdc6e1a58';

-- La Noodle (Pempelfort) – angepasst
update orte set beschreibung = replace($t$Das La Noodle in Pempelfort ist eine Mischung aus Restaurant und **Imbiss**: eher einfach im **asiatischen Street-Style** eingerichtet, dafür mit einer phänomenalen Küche. Die **Nudeln werden von Hand gemacht**, direkt vor den Augen der Gäste, was schon beim Zusehen Spaß macht. Man bestellt am Tresen, bekommt einen Pieper und wartet nicht lange, Getränke nimmt man sich aus dem Kühlfach.

Die Nudelgerichte schmecken **authentisch**, so wie man sie auch in China essen kann: frischer Teig, ideal gegartes Siedfleisch, dazu Varianten mit Rippchen, Hackfleisch oder Tomaten. Salate und **knusprige Teigtaschen** runden das Angebot ab. Die **Portionen sind riesig**, und für den Rest stehen kostenlose Behälter zum Mitnehmen bereit.

Das Personal ist freundlich und aufmerksam. Ideal für ein **schnelles, richtig gutes Essen**, etwa vor einem Konzert, oder einen unkomplizierten Abend zu zweit.$t$, chr(13), '') where id = '8bf37d2c-2577-4d46-8901-f0152d697321';

-- Kochi Bismarck (Stadtmitte) – neu
update orte set beschreibung = replace($t$Neben dem Kochi in Flingern gibt es das Spießrestaurant auch an der **Bismarckstraße**, ganz in der Nähe des japanischen Viertels. Auch hier dreht sich alles um **Fleischspieße** mit einer großen Auswahl an **hochwertigem Fleisch**, das Gäste immer wieder begeistert. Dazu lassen sich weitere Gerichte bestellen, etwa ein kleiner **Bulgogi-Hotpot** oder gebratener Reis.

Der Laden ist etwas kleiner, für größere Gruppen gibt es einen eigenen Raum mit rundem Tisch. Das Team ist **freundlich, aufmerksam und herzlich**, sodass man sich vom ersten Moment an willkommen fühlt. Etwas Geduld sollte man mitbringen, denn gute Spieße brauchen ihre Zeit. Parkhäuser gibt es in der Nähe, und vom Hauptbahnhof ist es nicht weit.$t$, chr(13), '') where id = 'a4aaad30-dfd4-43af-bb9a-854d3a40a29d';

commit;

-- Prüfung
select name, aktiv, qualitaets_score, extras->'ausgeblendet'->>'grund' as ausgeblendet from orte
where id in ('28799f21-e312-4dbb-8163-0088e9830c9b', 'a4aaad30-dfd4-43af-bb9a-854d3a40a29d');
select count(*) filter (where beschreibung like '%**%') as texte_mit_fett from orte
where id in (select id from public.orte_texte_sicherung_rest_d_2026_11_27);
