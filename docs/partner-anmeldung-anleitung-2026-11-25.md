# Partner-Anmeldungen (Schritt A1) – Anleitung für den Auftraggeber

Stand 25.11.2026. Plan: docs/plan-quellen-ausbau-2026-11-23.md, 5.5.1. Claude legt keine Konten an – alle Anmeldungen
macht der Auftraggeber. Mail-Texte für Ticketmaster und Reservix: docs/partner-anfragen-2026-11-24.md.

**Was du überall brauchst:** Website `https://diesdas.events`, kurze Beschreibung („Event-Kalender und Stadtguide für
Düsseldorf, Neuss und Ratingen; Events direkt von den Häusern; Ticket-Links auf Eventseiten“), Kontaktdaten wie im
Impressum, Bankverbindung für Auszahlungen, ggf. Steuernummer/USt-ID (vorher mit dem Steuerberater klären, ob ein
Gewerbe nötig ist). Reichweite: Besucherzahlen aus Google Analytics bereithalten (Reservix fragt danach).

---

## 1. Awin – für Eventim, Reservix und ADticket (wichtigster Schritt)

1. Anmelden als **Publisher**: https://ui.awin.com/publisher-signup/de/awin/ – Typ „Content/Website“, Website
   diesdas.events eintragen. Awin verlangt je nach Land eine kleine **Sign-up-Kaution**, die mit der ersten Auszahlung
   zurückkommt (Betrag steht im Formular).
2. Nach der Freischaltung im Awin-Konto: **Advertiser → Programme beitreten / „Join programmes“** und dort suchen und
   bewerben bei:
   - **eventim DE** (Programm-ID 11388)
   - **Reservix** (31293) – fragt nach Reichweite
   - **ADticket** (18490)
   Bei „Werbeformen“ angeben: Textlinks/Deeplinks auf Eventseiten, kein Gutschein, keine Preisvergleiche.
3. Die **Publisher-ID** findest du oben rechts im Awin-Konto (Zahl neben dem Kontonamen).
4. Optional: Unter „Toolbox → Produktfeeds“ nachsehen, ob Eventim oder Reservix einen **Event-Feed** anbieten
   (das wäre die Datenquelle für Schritt T2). Wenn ja: den Feed-Link oder einen API-Token erzeugen.

**Was ich brauche:** die Publisher-ID; welche der drei Programme zugesagt haben; ggf. Feed-Link/Token.

## 2. Ticketmaster – über Impact

1. Erst den **Partner-Account bei Impact** anlegen: Einstieg über die offizielle Ticketmaster-Seite
   https://developer.ticketmaster.com/partners/distribution-partners/affiliate-sign-up → dort zur Impact-Anmeldung.
   Bei Impact als „Partner“ (Publisher) registrieren.
2. In Impact im Marktplatz nach **Ticketmaster Germany** (bzw. „Ticketmaster DE“) suchen und dich bewerben.
   Ticketmaster verlangt je Land eine eigene Bewerbung – nur Deutschland reicht.
3. Im **Ticketmaster-Entwicklerkonto** (wo dein API-Schlüssel liegt) die Impact-ID eintragen, wenn das Formular danach
   fragt.
4. Die vorbereitete Mail aus `docs/partner-anfragen-2026-11-24.md` an Ticketmaster schicken: Bestätigung, dass
   **API-Daten + Affiliate-Links zusammen** erlaubt sind, und ob wir die **Bilder** nutzen dürfen.
5. Nach der Zusage: In Impact unter „Create a link“ / „Tracking-Link“ für **irgendein** Event auf ticketmaster.de einen
   **Deeplink** erzeugen und mir den kompletten Link schicken. Daraus baue ich die Vorlage.

**Was ich brauche:** den Beispiel-Deeplink aus Impact; die schriftliche Bestätigung (weiterleiten oder Inhalt nennen) –
erst dann `TICKETMASTER_PARTNER_OK=1`, bei Bildfreigabe auch `TICKETMASTER_BILDER_OK=1`.

## 3. Reservix – Daten-API (zusätzlich zu Awin)

1. Mail an **affiliate@reservix.de** (Text in `docs/partner-anfragen-2026-11-24.md`): Zugang zur Event-API für
   Düsseldorf/Neuss/Ratingen, Nutzung als Kalenderquelle mit Awin-Deeplinks.

**Was ich brauche:** den API-Schlüssel bzw. die Zugangsdaten und die Doku, die Reservix schickt.

## 4. Tiqets – Museen und Attraktionen

1. Partnerprogramm (kostenlos): https://www.tiqets.com/de/partnerprogramm/ → als **Affiliate** anmelden.
2. Nach der Freischaltung im **Affiliate-Portal**: „Tools → API Access → Create a token“. Der Token wird **nur einmal**
   angezeigt – sofort sicher notieren (sonst neuen erzeugen).
3. Die **Partner-ID** (steht im Portal bzw. in den erzeugten Links als `partner=`) notieren.
4. Laut Tiqets müssen manche API-Funktionen beim Account-Manager freigeschaltet werden: affiliates@tiqets.com.
   Bilder: dort nachfragen, ob wir die Produktbilder auf unseren Seiten zeigen dürfen.

**Was ich brauche:** Partner-ID; API-Token; Antwort zur Bildnutzung.

## 5. GetYourGuide – Führungen und Touren

1. Partnerprogramm: https://partner.getyourguide.com → als Partner (Website) anmelden. (GetYourGuide gibt es auch bei
   Awin; das eigene Programm ist für API-Zugang der bessere Weg.)
2. Im Partner-Konto die **Partner-ID** ablesen (erscheint in Links als `partner_id=`).
3. **API-Zugang** im Partner-Konto bzw. beim Partner-Team beantragen (Partner-API mit Zugangs-Token). Dazu die Frage, ob
   wir Tour-Bilder zeigen dürfen.

**Was ich brauche:** Partner-ID; API-Token; Antwort zur Bildnutzung.

---

## Wo die Werte hinkommen

GitHub → Repository → Settings → Secrets and variables → Actions. **Variables** sind öffentlich lesbar im Repo-Kontext
(Kennungen stehen ohnehin in jedem Link), **Secrets** sind geheim.

| Was | Art | Name | Von |
|---|---|---|---|
| Awin-Publisher-ID | Variable | `AWIN_PUBLISHER_ID` | Awin |
| Ticketmaster-Deeplink-Vorlage | Variable | `TICKETMASTER_PARTNER_VORLAGE` | baue ich aus deinem Beispiel-Link |
| Ticketmaster-Bestätigung | Variable | `TICKETMASTER_PARTNER_OK` = 1 | erst nach schriftlicher Zusage |
| Ticketmaster-Bilder | Variable | `TICKETMASTER_BILDER_OK` = 1 | erst nach schriftlicher Zusage |
| Tiqets-Partner-ID | Variable | `TIQETS_PARTNER_ID` | Tiqets-Portal |
| Tiqets-API | Secret | `TIQETS_API_TOKEN` | Tiqets-Portal |
| GetYourGuide-Partner-ID | Variable | `GYG_PARTNER_ID` | GYG-Konto |
| GetYourGuide-API | Secret | `GYG_API_TOKEN` | GYG |
| Reservix-API | Secret | `RESERVIX_API_KEY` (Name je nach Antwort) | Reservix |
| Eventim-Feed | Secret | je nach Awin-Angebot | Awin |
| **Einschalten** | Variable | `PARTNERLINKS_AKTIV` = 1 | wenn mindestens eine Kennung steht – danach ein Deploy |

Du kannst die Werte selbst eintragen oder mir die Kennungen (keine Tokens!) im Chat nennen – Tokens und Schlüssel bitte
immer direkt als Secret in GitHub eintragen, nie in den Chat.

## Reihenfolge

1. Awin (größter Hebel, weil viele Häuser schon über Eventim/Reservix verkaufen) → sobald die Publisher-ID da ist und
   ein Programm zugesagt hat: `AWIN_PUBLISHER_ID` + `PARTNERLINKS_AKTIV=1` → Deploy. Ab dann verdienen die
   vorhandenen Ticket-Buttons.
2. Ticketmaster/Impact parallel anstoßen (dauert wegen der schriftlichen Bestätigung).
3. Reservix-API, Tiqets, GetYourGuide → daraus baue ich T2 und T3.

## Stand der Anmeldungen

- **25.11.2026:** Awin angemeldet, Bewerbungen bei eventim DE, Reservix und ADticket laufen. Impact/Ticketmaster
  angemeldet, Bewerbung in Prüfung. Tiqets angemeldet, Bewerbung in Prüfung. **GetYourGuide fertig:** Partner-ID
  `MDZIQUO` (→ Variable `GYG_PARTNER_ID`), **Bilder dürfen verwendet werden** (gilt für T3: `bild_url` aus der
  GetYourGuide-API erlaubt). Reservix-API-Mail noch offen (optional, siehe Abschnitt 3).
- **25.11.2026, GetYourGuide-API geprüft:** Der API-Token ist nicht im Partner-Portal erzeugbar; laut offizieller Doku
  (github.com/getyourguide/partner-api-spec, „Getting started“) wird er „provided by GetYourGuide“. Für T3 reicht die
  Stufe BASIC/LIMITED_READ (`/tours`, `/tours/{id}`). Die Doku bittet ausdrücklich, die API nicht abzugreifen, um die
  Ausgabe zu cachen („please do not scrape the API in an attempt to cache its output“) → T3 muss das mit GetYourGuide
  klären (tägliche Übernahme von ~50 Düsseldorf-Touren) oder die Touren beim Seitenaufruf mit kurzem Cache abrufen.
  Anfrage an das Partner-Team (über „Hilfe“ im Portal) enthält deshalb beide Fragen. Die Seite
  supply.getyourguide.support („Unterstützte Systeme“) betrifft Anbieter/Buchungssysteme, nicht Affiliates.
