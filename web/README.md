# DiesDasDüsseldorf – Website (diesdas.events)

Next.js 16 (App Router, Cache Components) + TypeScript. Design laut Brand-Identity-Handoff (Startseite V2, Entdecken, Event-Detail, Tagesplaner, Wochenende) plus Stadtteil-Übersicht.

## Lokal starten

```bash
cp .env.local.example .env.local   # SUPABASE_URL + SUPABASE_KEY eintragen
npm install
npm run dev
```

Ohne `.env.local` läuft die Seite mit den 32 Beispiel-Events aus dem Handoff (gelber Hinweis oben).

## Aufbau

| Pfad | Inhalt |
|---|---|
| `lib/daten.ts` | Lädt alle Events ab heute (+60 Tage, ohne `abgelehnt`) aus Supabase, Cache 10 min |
| `lib/ableitungen.ts` | Filter, Sortierung, Kennzahlen, Picks, Wochenend-Programm, Themen, Bezirks-Clustering |
| `lib/stadtteile.ts` | Stadtteil → Stadtbezirk (10 Bezirke), Positionen der schematischen Karte |
| `lib/kategorien.ts` | Kategoriefarben/-icons; DB-Wert `family` → `familie` |
| `app/` | Routen: `/`, `/entdecken`, `/event/[id]`, `/heute`, `/tag/[datum]`, `/wochenende`, `/stadtteile`, `/merkliste`, `/api/events` |
| `app/globals.css` | Design Tokens + alle Komponenten-Styles |

## Abgeleitete Felder (noch nicht in der DB)

- **Beliebtheit**: Heuristik aus Redaktions-Flags, Bild, Beschreibung, Uhrzeit (`beliebtheit()`)
- **Kostenlos**: aus `preis` ("kostenlos", "Eintritt frei", "gratis" …)
- **Themen**: Stichwortsuche in Titel/Beschreibung (`THEMEN`)
- **Picks / Wochenend-Slots**: die beliebtesten Events mit möglichst verschiedenen Kategorien
- **Tipp des Tages / Highlight der Woche / Top-Event des Monats**: aus den Dashboard-Flags, sonst Heuristik
- Events, die länger als 7 Tage laufen (Ausstellungen), erscheinen in Tagesansichten nur am Starttag, in Entdecken durchgehend.
