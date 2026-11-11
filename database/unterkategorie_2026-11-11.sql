-- Unterkategorien (Feinfilter je Kategorie) – DiesDasDüsseldorf, 11.11.2026
-- Die Pipeline (pipeline/unterkategorien.py) ordnet jedes kommende Event per KI einer Unterkategorie zu,
-- z.B. Musik → „klassik“, „jazz“, „elektronisch“. Liste: web/lib/unterkategorien.json.
-- Wert „keine“ = geprüft, nichts passt. Leer (NULL) = noch nicht geprüft.
-- Die Website kommt auch ohne die Spalte aus (lädt dann ohne Feinfilter).

ALTER TABLE public.events ADD COLUMN IF NOT EXISTS unterkategorie TEXT;

-- Filter auf der Website und die Nachpflege („noch nicht geprüft“) laufen über Kategorie + Unterkategorie
CREATE INDEX IF NOT EXISTS events_unterkategorie_idx ON public.events (kategorie, unterkategorie);

-- Kontrolle: Spalte vorhanden
SELECT column_name, data_type FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'events' AND column_name = 'unterkategorie';
