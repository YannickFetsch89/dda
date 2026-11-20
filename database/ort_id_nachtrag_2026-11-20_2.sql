-- Nachtrag events.ort_id für den Bestand (Plan docs/plan-locations-2026-11-18.md, 3.4, Deploy-Punkt 3)
-- Erzeugt am 2026-11-20 von `python -m pipeline.ort_zuordnung --sql` (nur lesend).
-- Wiederholbar: setzt nur Treffer, die vom gespeicherten Wert abweichen; schreibt nie NULL.
-- Ein zweiter Lauf des Skripts nach dem Ausführen erzeugt keine Änderung mehr.

-- Hamtorkrug (hamtorkrug, spielstaette): 2 Events
UPDATE public.events SET ort_id = '67d4e943-80c9-48d3-864e-c79274c7b40e' WHERE id IN ('0af66e15-52c6-48df-af20-e9ddccff12b7', 'f5a6d986-2723-430c-8dbe-a99624964f13');
-- Vino Tinto (vino-tinto, spielstaette): 2 Events
UPDATE public.events SET ort_id = 'ac5a3c19-938b-4e12-ae03-5393573f080e' WHERE id IN ('c9628c98-f24a-47a5-b1cd-14cb3d7f1409', '94309f11-6bd7-4784-9857-150083c74d76');
-- Raketenstation Hombroich (raketenstation-hombroich, spielstaette): 2 Events
UPDATE public.events SET ort_id = 'e383ff0f-2638-4613-8c8e-b7a68965d61d' WHERE id IN ('34f3abff-d7e0-430c-93a0-44b55cf63661', '144928bd-d317-425f-81db-65b795f0c7bd');
-- Jugendkirche (jugendkirche, spielstaette): 2 Events
UPDATE public.events SET ort_id = 'abb00f41-0d22-463a-9970-e78e956a9283' WHERE id IN ('fd286718-469d-42ff-9761-195acba56c1b', 'd6e23712-ea53-4382-9177-191169ac1e17');
-- SCHVARZ KAFFEE HQ (schvarz-kaffee-hq, spielstaette): 2 Events
UPDATE public.events SET ort_id = 'e290d691-ecee-465a-bbd5-c332f7bd65c2' WHERE id IN ('a53ce3f2-1b86-4a3c-bffa-450c8356baf3', 'b61c44b3-8859-460a-b5ad-548e844f4d08');
-- Theaterfabrik (theaterfabrik, spielstaette): 2 Events
UPDATE public.events SET ort_id = '1acccde9-89c4-4867-a4ac-84f2c5443979' WHERE id IN ('2cae6c91-3839-458e-9b6c-b893cf12d730', '324eb7c0-68c6-4701-ae61-d8b452ae4e14');
-- Cuvée (cuvee, spielstaette): 2 Events
UPDATE public.events SET ort_id = '203fb081-9cc3-42d4-a458-bdf43b29a99f' WHERE id IN ('95d331eb-399e-4d20-9796-ef8a374c0890', '253f3153-0fe5-4535-9108-869b7558d3cc');

-- Kontrolle: Events mit ort_id je Typ des Orts
SELECT o.typ, count(*) FROM public.events e JOIN public.orte o ON o.id = e.ort_id GROUP BY o.typ ORDER BY 2 DESC;
