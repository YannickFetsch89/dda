-- Quellen-Ausbau, Schritt P1 (Plan docs/plan-quellen-ausbau-2026-11-23.md, 5.5.2).
-- VOR dem Deploy von P1 im Supabase-SQL-Editor als Ganzes ausführen. Wiederholbar.
--
-- events.ticket_url (text): Link zum Ticketverkauf, den das Haus selbst nennt (Eventim, Reservix, ADticket,
-- Ticketmaster, ticket.io … oder der eigene Ticketshop). quelle_url bleibt die Seite des Termins und ist kein Ersatz.
-- Die Spalte erbt die Policy „Events lesen“ (auth_rollen.sql) wie alle anderen Spalten von events.
-- Beim Quellenwechsel bleibt ein vorhandener ticket_url stehen, wenn die neue Quelle keinen hat (database/client.py).

ALTER TABLE public.events
    ADD COLUMN IF NOT EXISTS ticket_url TEXT;

-- PostgREST den neuen Aufbau sofort mitteilen (sonst scheitert im ersten Lauf danach jeder Insert mit ticket_url)
NOTIFY pgrst, 'reload schema';

-- Kontrolle: neue Spalte
SELECT table_name, column_name, data_type FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'events' AND column_name = 'ticket_url';
