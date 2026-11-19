-- Probelauf des Schutz-Triggers orte_schutz (Plan docs/plan-locations-2026-11-18.md, 3.3 Punkt 8, Pflicht-Tests)
-- Stand: 2026-11-19 · Im Supabase SQL-Editor ausführen, NACH database/orte_spielstaetten_2026-11-19.sql.
--
-- Ändert nichts dauerhaft: Alle Testzeilen entstehen in dieser Transaktion. Der Block endet absichtlich mit einer
-- Fehlermeldung, die das Ergebnis enthält – dadurch wird alles zurückgerollt (dazu das ROLLBACK am Ende).
--
-- ERWARTET: Fehlermeldung „PROBELAUF ERGEBNIS: alle 14 ok“. Steht dort „FEHLER“, nicht weitermachen.

BEGIN;

DO $$
DECLARE
  ok      INT := 0;
  fehler  TEXT := '';
  haus    UUID;
  saal    UUID;
  club    UUID;
  clubsaal UUID;
  ziel    UUID;
  frei    UUID;
BEGIN
  -- Testzeilen: Spielstätte mit aktivem Saal, Guide-Haus (club) mit aktivem Saal, eine Zielzeile, eine freie Guide-Zeile
  INSERT INTO public.orte (name, slug, typ, aktiv) VALUES ('Probe Haus', 'probe-haus-x1', 'spielstaette', true)
    RETURNING id INTO haus;
  INSERT INTO public.orte (name, slug, typ, aktiv, parent_id)
    VALUES ('Probe Saal', 'probe-haus-x1-saal', 'spielstaette', true, haus) RETURNING id INTO saal;
  INSERT INTO public.orte (name, slug, typ, aktiv) VALUES ('Probe Club', 'probe-club-x1', 'club', true)
    RETURNING id INTO club;
  INSERT INTO public.orte (name, slug, typ, aktiv, parent_id)
    VALUES ('Probe Clubsaal', 'probe-club-x1-saal', 'spielstaette', true, club) RETURNING id INTO clubsaal;
  INSERT INTO public.orte (name, slug, typ, aktiv) VALUES ('Probe Ziel', 'probe-ziel-x1', 'kneipe', true)
    RETURNING id INTO ziel;
  INSERT INTO public.orte (name, slug, typ, aktiv) VALUES ('Probe Frei', 'probe-frei-x1', 'cafe', true)
    RETURNING id INTO frei;

  -- 1–4: Spielstätte ohne Weiterleitung: Löschen, Abschalten, Slug-Wechsel, Typwechsel brechen ab
  BEGIN DELETE FROM public.orte WHERE id = saal;
    fehler := fehler || ' 1(Löschen ohne Weiterleitung lief durch)';
  EXCEPTION WHEN raise_exception THEN ok := ok + 1; END;
  BEGIN UPDATE public.orte SET aktiv = false WHERE id = saal;
    fehler := fehler || ' 2(Abschalten ohne Weiterleitung lief durch)';
  EXCEPTION WHEN raise_exception THEN ok := ok + 1; END;
  BEGIN UPDATE public.orte SET slug = 'probe-haus-x1-saal-neu' WHERE id = saal;
    fehler := fehler || ' 3(Slug-Wechsel ohne Weiterleitung lief durch)';
  EXCEPTION WHEN raise_exception THEN ok := ok + 1; END;
  BEGIN UPDATE public.orte SET typ = 'kneipe' WHERE id = saal;
    fehler := fehler || ' 4(Typwechsel ohne Weiterleitung lief durch)';
  EXCEPTION WHEN raise_exception THEN ok := ok + 1; END;

  -- 5: Haus (Spielstätte) mit aktivem Saal löschen bricht ab, auch mit eigener Weiterleitung
  INSERT INTO public.ort_weiterleitungen (alter_slug, ziel_ort_id, grund) VALUES ('probe-haus-x1', NULL, 'Probe');
  BEGIN DELETE FROM public.orte WHERE id = haus;
    fehler := fehler || ' 5(Haus mit aktivem Saal gelöscht)';
  EXCEPTION WHEN raise_exception THEN ok := ok + 1; END;

  -- 6–7: Guide-Haus (club) mit aktivem Saal: Löschen und Abschalten brechen ab
  BEGIN DELETE FROM public.orte WHERE id = club;
    fehler := fehler || ' 6(Guide-Haus mit aktivem Saal gelöscht)';
  EXCEPTION WHEN raise_exception THEN ok := ok + 1; END;
  BEGIN UPDATE public.orte SET aktiv = false WHERE id = club;
    fehler := fehler || ' 7(Guide-Haus mit aktivem Saal abgeschaltet)';
  EXCEPTION WHEN raise_exception THEN ok := ok + 1; END;

  -- 8: Guide-Zeile ohne Kinder lässt sich wie bisher abschalten und löschen
  BEGIN UPDATE public.orte SET aktiv = false WHERE id = frei; DELETE FROM public.orte WHERE id = frei; ok := ok + 1;
  EXCEPTION WHEN raise_exception THEN fehler := fehler || ' 8(Guide-Zeile ohne Kinder blockiert: ' || SQLERRM || ')'; END;

  -- 9: Zeile, auf die eine Weiterleitung zeigt, lässt sich nicht löschen …
  INSERT INTO public.ort_weiterleitungen (alter_slug, ziel_ort_id, grund) VALUES ('probe-alt-x1', ziel, 'Probe');
  BEGIN DELETE FROM public.orte WHERE id = ziel;
    fehler := fehler || ' 9(Ziel einer Weiterleitung gelöscht)';
  EXCEPTION WHEN raise_exception THEN ok := ok + 1; END;
  -- 10: … nach dem Umhängen schon
  BEGIN
    UPDATE public.ort_weiterleitungen SET ziel_ort_id = club WHERE ziel_ort_id = ziel;
    DELETE FROM public.orte WHERE id = ziel; ok := ok + 1;
  EXCEPTION WHEN raise_exception THEN fehler := fehler || ' 10(nach Umhängen blockiert: ' || SQLERRM || ')'; END;

  -- 11–14: mit Weiterleitung klappen Slug-Wechsel, Typwechsel, Abschalten und Löschen eines Saals
  INSERT INTO public.ort_weiterleitungen (alter_slug, ziel_ort_id, grund) VALUES ('probe-club-x1-saal', club, 'Probe');
  BEGIN UPDATE public.orte SET slug = 'probe-club-x1-saal-b' WHERE id = clubsaal; ok := ok + 1;
  EXCEPTION WHEN raise_exception THEN fehler := fehler || ' 11(Slug-Wechsel mit Weiterleitung blockiert)'; END;
  INSERT INTO public.ort_weiterleitungen (alter_slug, ziel_ort_id, grund) VALUES ('probe-club-x1-saal-b', club, 'Probe');
  BEGIN UPDATE public.orte SET typ = 'kneipe' WHERE id = clubsaal; UPDATE public.orte SET typ = 'spielstaette' WHERE id = clubsaal;
    ok := ok + 1;
  EXCEPTION WHEN raise_exception THEN fehler := fehler || ' 12(Typwechsel mit Weiterleitung blockiert)'; END;
  BEGIN UPDATE public.orte SET aktiv = false WHERE id = clubsaal; ok := ok + 1;
  EXCEPTION WHEN raise_exception THEN fehler := fehler || ' 13(Abschalten mit Weiterleitung blockiert)'; END;
  BEGIN DELETE FROM public.orte WHERE id = clubsaal; ok := ok + 1;
  EXCEPTION WHEN raise_exception THEN fehler := fehler || ' 14(Löschen mit Weiterleitung blockiert)'; END;

  IF fehler = '' THEN
    RAISE EXCEPTION 'PROBELAUF ERGEBNIS: alle % ok (alles wird zurückgerollt)', ok;
  ELSE
    RAISE EXCEPTION 'PROBELAUF ERGEBNIS: % ok, FEHLER:%', ok, fehler;
  END IF;
END $$;

ROLLBACK;
