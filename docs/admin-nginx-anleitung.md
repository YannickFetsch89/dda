# Anleitung: nginx für den neuen Admin-Bereich (Plan Admin-Dashboard, Schritte 1a-0 und 1a)

Stand 23.11.2026. Plan: `docs/plan-admin-dashboard-2026-11-23.md`, Abschnitt 3.2.

**Warum:** Die Website sieht hinter nginx nur die Adresse `localhost:3847`, egal ob jemand diesdas.events oder admin.diesdas.events aufruft. Deshalb sagt nginx ihr mit einem eigenen Kopf, woher die Anfrage kommt: `X-DDD-Bereich: web` oder `X-DDD-Bereich: admin`. `proxy_set_header` ersetzt dabei einen Wert, den jemand selbst mitschickt.

**Wo:** ISPConfig → **Sites** → **Website** → Domain anklicken → Reiter **Options** (deutsch „Optionen“) → Feld **nginx Directives** („nginx-Direktiven“).

> Geprüft am 23.11.2026: Das Feld ist bearbeitbar. Bei admin.diesdas.events wurde es schon für die Weiterleitung an Streamlit genutzt. Abschnitt C entfällt damit.

---

## A. Schritt 1a-0: diesdas.events (vor dem ersten Admin-Deploy)

1. In ISPConfig die Website **diesdas.events** öffnen → **Options** → **nginx Directives**.
2. Dort steht bereits eine Weiterleitung an die Website, etwa so:
   ```
   location / {
       proxy_pass http://127.0.0.1:3847;
       ...
   }
   ```
3. **Innerhalb** dieses `location`-Blocks eine Zeile ergänzen:
   ```
   proxy_set_header X-DDD-Bereich web;
   ```
   Gibt es mehrere `location`-Blöcke mit `proxy_pass http://127.0.0.1:3847`, kommt die Zeile in **jeden** davon.
4. Speichern. ISPConfig lädt nginx nach etwa einer Minute neu.
5. Kurz Bescheid geben. Claude prüft danach, dass die Website unverändert läuft.

Für die Website ändert diese Zeile nichts, solange der neue Code sie nicht liest.

## B. Schritt 1a: admin.diesdas.events (direkt nach dem Deploy von Stufe 1a)

Mit dem Deploy zieht das alte Streamlit-Dashboard auf `/alt/` um. Bis zu dieser Umstellung ist admin.diesdas.events kurz nicht erreichbar.

1. In ISPConfig die Website **admin.diesdas.events** öffnen → **Options** → **nginx Directives**.
2. Den bisherigen Inhalt **durch Folgendes ersetzen**. Vorher den alten Inhalt kopieren und aufheben, damit man zurück kann. Die ersten beiden Teile, also `X-Robots-Tag` und `robots.txt`, stehen heute schon so drin (Screenshot vom 23.11.2026) und bleiben unverändert.
   ```
   add_header X-Robots-Tag "noindex, nofollow, noarchive" always;
   location = /robots.txt {
       default_type text/plain;
       return 200 "User-agent: *\nDisallow: /\n";
   }

   # Startseite → /admin
   location = / {
       return 308 /admin;
   }

   # Neuer Admin-Bereich und alles, was seine Seiten laden (Next.js auf 3847)
   location ~ ^/(admin|api/admin|_next|bild|fallback|magazin-bild|magazin-autoren|ort-foto|ort-bilder)(/|$) {
       proxy_pass http://127.0.0.1:3847;
       proxy_set_header Host $host;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-DDD-Bereich admin;
   }
   location = /icon.svg {
       proxy_pass http://127.0.0.1:3847;
       proxy_set_header Host $host;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-DDD-Bereich admin;
   }

   # Altes Dashboard (Streamlit) übergangsweise unter /alt/
   location /alt/ {
       proxy_pass http://127.0.0.1:8502;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
       proxy_set_header Host $host;
       proxy_read_timeout 86400;
   }

   # Alles andere gibt es hier nicht
   location / {
       return 404;
   }
   ```
   Der Block ist so fertig zum Einfügen. `Host $host` und `X-Real-IP` entsprechen dem bisherigen Block für Streamlit.
3. Speichern. Nach etwa einer Minute ist der neue Bereich unter https://admin.diesdas.events erreichbar, das alte Dashboard unter https://admin.diesdas.events/alt/.
4. Kurz Bescheid geben. Claude prüft dann mit `curl`:
   - `https://admin.diesdas.events/` → 308 auf `/admin`
   - `https://admin.diesdas.events/admin` → Anmeldung
   - `https://admin.diesdas.events/entdecken` → 404
   - **`https://diesdas.events/admin` mit selbst gesetztem Kopf `X-DDD-Bereich: admin` → 404.** Kommt hier etwas anderes, fehlt die Zeile aus Teil A.

## C. Falls „nginx Directives“ nicht bearbeitbar ist

Dann setzt ein kleiner Weiterleiter auf dem Server den Kopf. Das ist ein Node-Skript ohne neue Bibliothek, auf einem eigenen Port mit eigenem Geheimschlüssel. admin.diesdas.events zeigt dann auf diesen Port statt auf 8502. Der Kopf auf diesdas.events ist dann nicht nötig, weil die Website den Geheimschlüssel prüft statt des Kopfs. Das wäre eine Abweichung vom freigegebenen Plan und kommt nur nach Rücksprache.

## Zurück

Den aufgehobenen alten Inhalt wieder in **nginx Directives** von admin.diesdas.events einsetzen. In `dashboard/dashboard.sh` die Zeile `BASIS=alt` und `--server.baseUrlPath` entfernen, dann deployen.
