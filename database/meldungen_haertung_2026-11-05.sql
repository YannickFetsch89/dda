-- meldungen_haertung_2026-11-05.sql – DiesDasDüsseldorf
-- Härtung nach Code-Review: Der anon-Key gilt als öffentlich. Bisher durfte er direkt in
-- newsletter_anmeldungen / event_meldungen schreiben und in den Bucket event-meldungen hochladen –
-- an Honeypot, Bremslimit und Bildprüfung der Website vorbei (und ein Unique-Fehler verriet, ob eine
-- Adresse schon angemeldet ist). Ab jetzt schreibt nur noch die Website serverseitig mit dem
-- Service-Key (umgeht RLS); anon hat auf beide Tabellen und den Upload KEINE Rechte mehr.
--
-- REIHENFOLGE: Erst die Website mit dem Service-Key deployen (web/lib/formulare.ts, deploy.yml),
-- DANN dieses Skript ausführen – sonst schlagen Anmeldungen/Meldungen bis zum Deploy fehl.
-- Wiederholbar.

-- Tabellen: alle Rechte weg (auch ein evtl. Supabase-Default „GRANT ALL“), Admins wieder lesen/ändern/löschen
REVOKE ALL ON public.newsletter_anmeldungen FROM anon, authenticated;
REVOKE ALL ON public.event_meldungen FROM anon, authenticated;
GRANT SELECT, UPDATE, DELETE ON public.newsletter_anmeldungen TO authenticated;
GRANT SELECT, UPDATE, DELETE ON public.event_meldungen TO authenticated;

-- Insert-Regeln für die Öffentlichkeit entfernen (Admin-Regeln bleiben bestehen)
DROP POLICY IF EXISTS "Newsletter anmelden" ON public.newsletter_anmeldungen;
DROP POLICY IF EXISTS "Event melden" ON public.event_meldungen;

-- Upload in den privaten Bucket nur noch über den Server (Service-Key)
DROP POLICY IF EXISTS "Meldungsbild hochladen" ON storage.objects;

-- Kontrolle: anon darf nichts mehr, es bleiben nur Admin-Regeln
SELECT tablename, policyname, cmd, roles
FROM pg_policies
WHERE (schemaname = 'public' AND tablename IN ('newsletter_anmeldungen', 'event_meldungen'))
   OR (schemaname = 'storage' AND policyname IN ('Meldungsbild hochladen', 'Admins lesen Meldungsbilder', 'Admins löschen Meldungsbilder'))
ORDER BY tablename, policyname;
