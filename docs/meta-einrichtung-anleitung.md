# Anleitung: Meta-Einrichtung für Instagram und Facebook (Social-Plan Schritt 0)

**Für:** den Auftraggeber · **Stand:** 26.11.2026 · **Plan:** `docs/plan-social-2026-11-25.md`, Abschnitt 9
**Konten:** Instagram @dies.das.duesseldorf, Facebook-Seite facebook.com/dies.das.duesseldorf

Meta ändert seine Menüs häufig. Heißt ein Punkt bei dir etwas anders, nimm den nächstliegenden. Bei Zweifeln schick mir einen Screenshot, aber **nie den Token**.

Ergebnis dieser Anleitung:
- ein Token ohne Ablauf, der nur auf unsere Seite und unser Instagram-Konto zugreifen darf
- die beiden IDs von Seite und Instagram-Konto
- eine bestandene Prüfung mit `tools/meta_pruefen.py`

**Veröffentlicht wird dabei nichts**, außer du startest ausdrücklich die Test-Story (Teil 7).

---

## Teil 1 – Business-Portfolio prüfen (5 Minuten)

1. Öffne **business.facebook.com/settings** und melde dich mit deinem Facebook-Konto an.
2. Prüfe oben links, ob das richtige **Business-Portfolio** gewählt ist, also das, dem die Seite gehört.
3. **Konten → Seiten:** Dort muss **dies.das.duesseldorf** stehen. Falls nicht: „Hinzufügen“ → „Seite hinzufügen“.
4. **Konten → Instagram-Konten:** Dort muss **dies.das.duesseldorf** stehen. Falls nicht: „Hinzufügen“ und mit Instagram anmelden.
5. **Sicherheitscenter:** Die zweistufige Authentifizierung sollte für alle Admins an sein.

✓ Geschafft, wenn Seite und Instagram-Konto im selben Portfolio stehen.

## Teil 2 – Entwicklerkonto und App (10 Minuten)

1. Öffne **developers.facebook.com**, melde dich mit demselben Facebook-Konto an und schließe beim ersten Mal „Erste Schritte“ ab (Telefon/E-Mail bestätigen).
2. **Meine Apps → App erstellen.**
   - App-Name: `diesdas-social`
   - Kontakt-E-Mail: `hallo@diesdas.events`
   - Anwendungsfälle: **„Inhalte auf Instagram verwalten“** (Instagram-API mit Facebook-Login) **und** **„Alles auf deiner Seite verwalten“**. Wenn Meta nach dem App-Typ fragt: **Business**.
   - Business-Portfolio: dasselbe wie in Teil 1.
3. In der App unter **App-Einstellungen → Allgemeines:**
   - Datenschutzrichtlinie: `https://diesdas.events/datenschutz`
   - Nutzungsbedingungen: `https://diesdas.events/nutzungsbedingungen`
   - Datenlöschung (Anleitungs-URL): `https://diesdas.events/datenschutz`
   - App-Symbol: 1024×1024 PNG. Ich kann dir das aus `web/public/logo/app-icon.svg` erzeugen, sag Bescheid.
   - Kategorie: „Business und Seiten“ oder ähnlich.
   - **Speichern.**
4. **Den App-Modus lässt du auf „Entwicklung“.** Ob „Live“ nötig ist, zeigt erst Teil 7.

## Teil 3 – Berechtigungen (5 Minuten)

In der App unter **Anwendungsfälle → (jeweils) Anpassen → Berechtigungen** diese Rechte hinzufügen. Der **Standardzugriff genügt**, ein App-Review ist nicht nötig, weil wir nur eigene Konten bespielen:

| Recht | wofür |
|---|---|
| `instagram_basic` | Instagram-Konto lesen |
| `instagram_content_publish` | auf Instagram veröffentlichen |
| `pages_show_list` | Seite finden |
| `pages_read_engagement` | Seite lesen, Seiten-Token holen |
| `pages_manage_posts` | auf der Facebook-Seite veröffentlichen |
| `business_management` | Systembenutzer im Portfolio |
| `ads_read` | verlangt Meta zusätzlich, wenn die Seitenrolle über das Business-Portfolio vergeben ist (Teil 4). Wir schalten keine Anzeigen. |

## Teil 4 – Systembenutzer und Token (10 Minuten)

1. **business.facebook.com/settings → Nutzer → Systembenutzer → Hinzufügen.**
   - Name: `diesdas-social`
   - Rolle: **Mitarbeiter**, nicht Admin
2. Beim neuen Systembenutzer: **Assets zuweisen.**
   - **Apps:** `diesdas-social` → App verwalten bzw. Vollzugriff
   - **Seiten:** `dies.das.duesseldorf` → **Inhalte** (Beiträge erstellen und verwalten). Mehr nicht.
   - **Instagram-Konten:** `dies.das.duesseldorf` → **Inhalte**
3. **Token generieren:**
   - App `diesdas-social` wählen
   - Ablauf: **„Nie“**
   - die sieben Rechte aus Teil 3 ankreuzen
   - „Token generieren“
4. **Den Token sofort sicher ablegen, er wird nur einmal angezeigt:**
   - Lege die Datei **`C:\Claude_DDD\DD\secrets\meta.env`** an, nach der Vorlage `secrets/meta.env.example`.
   - Trag dort `META_TOKEN=…` ein. Der Ordner `secrets/` ist von Git ausgenommen.
   - **Nicht** in den Chat, nicht in eine Mail, nicht in ein Dokument.

**Falls Meta beim Token den Systembenutzer ablehnt** (Hinweis auf fehlenden Marketing-API-Zugang oder Freischaltung), nehmen wir den Ersatzweg aus dem Plan (E13): ein Seiten-Token ohne Ablauf über deinen eigenen Zugang. Schick mir dann die Fehlermeldung, ohne Token. Ich führe dich durch den Ersatzweg.

## Teil 5 – Prüfung (2 Minuten)

Sag mir im Chat: **„meta.env liegt“**. Ich starte dann die Grundprüfung:

```
python tools/meta_pruefen.py --env C:\Claude_DDD\DD\secrets\meta.env
```

Sie veröffentlicht nichts und prüft:
- Token gültig und ohne Ablauf
- alle sieben Rechte vorhanden
- Seite lesbar und Seiten-Token abrufbar
- Instagram-Konto verknüpft und @dies.das.duesseldorf
- Veröffentlichungs-Limit

Am Ende zeigt sie `META_PAGE_ID` und `META_IG_ID`. Die beiden IDs sind nicht geheim.

Selbst starten geht auch: einmalig `py -m pip install httpx python-dotenv`, dann den Befehl oben mit `py` statt `python`.

## Teil 6 – Test-Container für ein Bild (2 Minuten, veröffentlicht nichts)

Ich lege bei Meta einen Bild-Container mit einem eigenen JPEG von diesdas.events an und veröffentliche ihn **nicht**. So sehen wir, ob Meta Bilder von außen abholt. Nicht veröffentlichte Container verfallen nach 24 Stunden.

Der **Test für das Reel-Video** folgt später: Lokal ist kein ffmpeg installiert, und der Speicherbereich `social` entsteht erst mit dem SQL in Schritt 3. Das Video baut dann der Social-Job in GitHub mit genau den Reel-Einstellungen. Den Container ohne Veröffentlichen prüfen wir vor dem Einschalten (Schritt 8).

## Teil 7 – Test-Story (optional, öffentlich für 24 Stunden)

Nur wenn du willst: eine Story mit einem Testbild, die nach 24 Stunden verschwindet. Sie zeigt, ob Posts im App-Modus „Entwicklung“ öffentlich erscheinen. Das Skript verlangt dafür ausdrücklich `--wirklich-veroeffentlichen`. Ich starte sie nur, wenn du im Chat zustimmst.

## Teil 8 – Supabase prüfen (2 Minuten)

Im **Supabase-SQL-Editor** (Projekt `dqckcszxoyaxiwwcgxxk`) ausführen und mir das Ergebnis schicken:

```sql
-- Sind pg_cron, pg_net und der Vault verfügbar bzw. eingeschaltet?
SELECT name, default_version, installed_version
FROM pg_available_extensions
WHERE name IN ('pg_cron', 'pg_net', 'supabase_vault')
ORDER BY name;
```

Daraus ergibt sich, ob der Takt alle 5 Minuten aus Supabase kommt oder über einen `crontab`-Eintrag auf dem Server (Plan E9). Einschalten musst du noch nichts, das kommt mit dem SQL in Schritt 3.

## Teil 9 – GitHub (erst nach Teil 5)

Im Repository unter **Settings → Secrets and variables → Actions:**
- **Secret** `META_TOKEN`: derselbe Token wie in `meta.env`. Ihn liest nur der Deploy und schreibt ihn auf den Server, kein anderer Job.
- **Variables** `META_PAGE_ID` und `META_IG_ID`: die IDs aus Teil 5.

Die Schlüssel `SOCIAL_JOB_SCHLUESSEL` und `SOCIAL_TAKT_SCHLUESSEL` kommen erst in Schritt 8. Ich sage dir dann, wie du sie erzeugst.

## Teil 10 – Profile

- **Facebook-Seite → Seite bearbeiten → Info:**
  - Feld **Impressum** mit `https://diesdas.events/impressum`
  - Website `https://diesdas.events`
  - Das kannst du jetzt schon machen.
- **Instagram-Bio:** der Link `diesdas.events/links` erst, wenn die Seite `/links` live ist (Schritt 9). Bis dahin `diesdas.events`.

---

**Danach:** Ich trage die Ergebnisse (Token-Weg, IDs, App-Modus, Supabase-Erweiterungen) im Plan ein, und wir gehen an Schritt 2, die Folien-Entwürfe.
