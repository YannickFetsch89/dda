# Kartendaten und -Assets (selbst gehostet)

- `region.pmtiles` – Kartenausschnitt Düsseldorf/Neuss/Ratingen (bbox 6.55,51.08,6.99,51.39, Zoom 0–15),
  erzeugt mit `pmtiles extract` aus dem Protomaps-Build `20261104.pmtiles`.
  Daten © OpenStreetMap-Mitwirkende, Open Database License (ODbL) – Quellenangabe auf der Karte ist Pflicht.
  Nicht im Git-Repo (≈ 50 MB); liegt auf dem Server unter `~/dda/web/public/karte/region.pmtiles`.
- `fonts/` – Noto Sans (Regular, Medium, Italic) als Glyph-PBF aus protomaps/basemaps-assets,
  SIL Open Font License 1.1 (siehe `fonts/OFL.txt`). Nur die Zeichenbereiche 0-255, 256-511, 8192-8447.
- `sprites/` – Kartensymbole (hell/dunkel) aus protomaps/basemaps-assets, abgeleitet von tangrams/icons (MIT).

Aktualisieren des Kartenausschnitts (z.B. jährlich):
`pmtiles extract https://build.protomaps.com/<JJJJMMTT>.pmtiles region.pmtiles --bbox=6.55,51.08,6.99,51.39 --maxzoom=15`
