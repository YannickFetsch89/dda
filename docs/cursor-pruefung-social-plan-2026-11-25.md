# Cursor-Prüfung 1 – Plan Social-Posting (erste Fassung), 25.11.2026

Ergebnis vom Auftraggeber übermittelt. Gesamturteil: **nicht freigabefähig** (2 kritisch, 5 mittel, 5 gering). Alle Befunde sind in die zweite Fassung eingearbeitet (`docs/plan-social-2026-11-25.md`, Anhang E).

## Kritisch
1. **Eindeutigkeits-Index** `UNIQUE (slot, (geplant_fuer AT TIME ZONE 'Europe/Berlin')::date)` lässt sich nicht anlegen. `AT TIME ZONE` ist `STABLE`, nicht `IMMUTABLE`. Vorschlag: Spalte `tag date`, `UNIQUE (slot, tag)`.
2. **Zustandsautomat:** Das Reel wird `bereit` ohne Freigabe. `teilweise` steht nicht in der Beanspruchung. Die 15-Minuten-Regel bricht wartende Reel-Container ab. „Fällig“ ist nur über die Uhrzeit definiert, die Auswahl kann `wird_gepostet` erneut beanspruchen.

## Mittel
3. Die Auswahlfunktionen rechnen mit `pool.heute`, `eventPoolLaden` ist gecacht → `magazinPoolLaden` mit Stichtag.
4. Die Bildherkunft geht nur aus `bild_url` hervor (Dubletten-Zusammenführung). Die Ortsbild-Lizenz steht in `data/spielstaetten/bilder.csv`. Google-Fotos ausschließen. Sperrliste über den Host wie `_VERBOTEN` (`scraper/orte/ortsbilder.py:52`).
5. Meta: Instagram braucht den Seiten-Token, dazu `ads_read`/`ads_management` bei einer Rolle über den Business Manager. Der Facebook-Reel-Upload läuft über `rupload.facebook.com`. Das Karussell-Format richtet sich nach der ersten Folie, das Reel-Cover wird im Feed quadratisch beschnitten. Fehlercodes 613/80001.
6. Reel und Karussell passen zeitlich nicht zusammen (Zwei-Tage-Regel).
7. Schritt 1 bricht `tests/test_vorschau.py:94–99` und `test_pipeline.py:26/83`; `config.py:19–20`.

## Gering
8. Der Kategorisierer filtert auf `beschreibung IS NULL`, der Caption-Generator setzt `fehler`, `dashboard/` gibt es nicht mehr.
9. `seo.ts:44` ist ein Kommentar, kein auskommentierter Block.
10. `schluesselOk()` ohne zweites Argument prüft den Magazin-Schlüssel. `META_TOKEN` darf nur in `deploy.yml` stehen.
11. Die Startseite liefert Tipp + bis zu 4 Picks. Story-Folien sind einzelne Veröffentlichungen.
12. `INSTAGRAM_TAGE` und Admin-Plan 4.8: kein Widerspruch in der Wirkung.

## Bestätigt
Der Bestand (Abschnitt 1) stimmt. Next 16.4.6, sharp 0.35.5 (JPEG ohne neue Abhängigkeit). Schriften liegen nicht als Dateien vor. Die Host-Trennung für `/api/admin` funktioniert. `sensibelMenge()` (`web/lib/konto/mein-bereich.ts:22`). `magazin_beitraege.event_ids` aus den Einbettungen (`web/lib/admin/magazin-pruefung.ts:44`).
