# Konzept: Eingeloggter Bereich, Personalisierung und Weg zur App

Stand: 18.11.2026 · **zweite Fassung, mit den Antworten des Auftraggebers vom 18.11.2026 (Abschnitt 2).** Noch kein Bauplan, nichts umgesetzt. Erstellt von Claude. Aus Stufe 1 (Abschnitt 8) entsteht als Nächstes ein eigener Plan mit Prüfungen und Freigaben wie beim Kontenplan.

**Bauplan Stufe 1:** `docs/plan-mein-bereich-stufe1-2026-11-18.md` (dritte Fassung, 19.11.2026; S1–S7 vom Auftraggeber am 18.11. bestätigt, noch nicht gebaut).

Verwandt: Die **Location-Seiten** (eigene Seite für jeden Veranstaltungsort, Vorbild rausgegangen.de/locations/…) plant eine eigene Sitzung in `docs/plan-locations-<datum>.md`. Das „Folgen“ von Orten (B4) baut darauf auf.

---

## 1. Ausgangslage
- **Konten sind live** (17.11.2026): Merkliste im Konto, Interessen aus dem Fragebogen (nur mit Einwilligung), Name und Geburtsdatum, Einwilligungen, Auskunft und Export, Mailadresse und Passwort ändern, Löschen.
- **Der eingeloggte Bereich ist heute eine einzige Seite `/konto`.** Die Merkliste liegt getrennt unter `/merkliste`.
- **Interessen werden gesammelt, aber noch nirgends genutzt.** Der Einwilligungstext verspricht „passende Events vorschlagen“. Die Regeln dafür stehen im Kontenplan, Abschnitt 13 („Für euch“: Punkte für Unterkategorie, Kategorie, Stadtteil, Merkmal, gleiche Reihe oder gleicher Ort, nie aus sensiblen Events).
- **Startseite** mit Empfehlungs-Stufen und Fokustag (live seit 13.11.2026). Sie ist gecacht und für alle gleich.
- **Für die App gibt es noch keinen Plan.** Vorgesorgt ist: Die Routen nehmen auch ein Bearer-Token an, und Push ist erst mit der App vorgesehen.

## 2. Entscheidungen des Auftraggebers (18.11.2026)

| Nr. | Frage | Entscheidung |
|---|---|---|
| P1 | Wichtigste Bausteine | **B1 „Für dich“, B2 Startseite eingeloggt, B4 Folgen, B7 Wochenmail**. Alle übrigen sind sinnvoll, nichts fehlt. **Neu dazu B18:** Vorschau „Für dich empfohlen“ für Abgemeldete, verschwommen, mit Hinweis zur Registrierung (wie bei Rausgegangen) |
| P2 | Navigation | **Mehrere Unterseiten.** Inhalte (Events, Orte, Tipps) sind getrennt vom Organisatorischen (Konto, Mailadresse, Passwort, Datenschutz) |
| P3 | Startseite eingeloggt | **Bleibt im Wesentlichen wie gehabt**, bekommt aber 2–3 zusätzliche persönliche Module, z. B. „Für dich empfohlen“ mit echten persönlichen Picks |
| P4 | Erinnerungen und Wochenmail | **Später, niedrige Priorität.** Sie werden umgesetzt, aber nach Stufe 1–3 |
| P5 | App | **iOS und Android.** Gedacht wie die heutige Mobilversion der Website, nur als App. Den Weg der Umsetzung schlägt Claude vor (Abschnitt 7) |
| P6 | Folgen | **Erst Orte und Reihen.** Künstler kommen später |
| P7 | Wochenmail und Newsletter | **Zusammenlegen** (eine Mail, persönlich für eingeloggte Abonnenten) |

## 3. Wie es andere machen (Kurzüberblick)

| Anbieter | Personalisierung | Was für uns interessant ist |
|---|---|---|
| **Rausgegangen** | Profil für bessere Empfehlungen, Events speichern, Künstler:innen, Locations und Freund:innen folgen, „Social Profiles“, „Preference Center“ für Mail, Push und In-App, „Mitgegangen“ (Chat zu einem Event, kostenpflichtig). Abgemeldet sieht man „Für dich empfohlen“ verschwommen mit Registrier-Hinweis. Eigene Seite für fast jede Location. | Folgen von Locations, Preference Center, Vorschau für Abgemeldete, Location-Seiten |
| **Eventbrite** (App-Relaunch März 2025) | Onboarding: Stadt, Interessen, Veranstalter vorgeschlagen zum Folgen, mit „Überspringen“. Der Tab „Discover“ ist ein persönlicher Feed. | Onboarding mit „Folgen“-Vorschlägen |
| **DICE** | Künstler und Venues folgen, Spotify oder Apple Music verbinden, Erinnerungen zum Vorverkauf | Folgen + Erinnerung |
| **Resident Advisor** | DJs, Clubs und Veranstalter folgen, „For You“ und „New events“, Knopf „Interested“, Tickets in der App | „Neu bei dem, dem du folgst“ |
| **Songkick, Bandsintown, Fever, Time Out** (allgemein bekannt) | Künstler tracken, Mail oder Push bei neuen Terminen, persönliche Wochenmails | Benachrichtigung und Wochenmail |

Muster, das fast alle teilen: Merken und Folgen als Grundbausteine, ein persönlicher Feed als Einstieg, Benachrichtigungen als Grund, eingeloggt zu bleiben, Einstellungen je Kanal in einem Preference Center.

## 4. Leitideen
1. **Ein Bereich für Web und App.** Was eingeloggt passiert, läuft über `/api/konto/*` (JSON, Cookie im Web, Bearer-Token in der App). Die App nutzt dieselben Routen.
2. **Öffentliche Seiten bleiben schnell und gecacht.** Persönliches kommt als nachgeladene Insel dazu, wie heute bei Merkliste und Herz.
3. **Nur ausdrückliche Signale:** Merken, Folgen, „Mehr davon“ und „Nicht interessiert“, Fragebogen. **Kein heimliches Klick-Tracking** (bräuchte eine eigene Einwilligung nach TDDDG).
4. **Sensible Events nie** in Empfehlungen und nie in der Statistik (E13, S4). Die **eigene** Merkliste, „Deine nächsten Events“, Erlebt und die Zählungen kommende/erlebt dürfen eigene sensible Merkungen zeigen, ohne Kennzeichnung. Datenschutzfreundliche Voreinstellungen.
5. **Jede neue Nutzung mit Zweck.** Werbliche Mails und Push nur mit Einwilligung nach § 7 UWG. Dienstmails, um die jemand bittet, laufen als Teil des Vertrags. Das klärt der Anwalt je Baustein.

## 5. Aufbau des eingeloggten Bereichs („Mein dies.das“, P2)

Zwei Gruppen, getrennt auch in der Navigation:

**A. Inhalte – „Für mich“**

| Seite | Inhalt |
|---|---|
| **Für dich** | Persönlicher Feed: „Heute für dich“, „Dein Wochenende“, „Weil du X gemerkt hast“, später „Neu bei deinen Orten und Reihen“. Je Karte „Mehr davon“ und „Nicht interessiert“ |
| **Merkliste** | Kommende Events (Liste, später Kalender), Hinweis bei Absage oder Änderung, in den eigenen Kalender übernehmen |
| **Erlebt** | Vergangene gemerkte Events, „Warst du da?“ mit Daumen hoch oder runter, später ein Jahresrückblick |
| **Ich folge** | Orte und Reihen (P6), mit Liste der nächsten Termine. „Folgen“-Button auf Orts- und Reihenseiten |
| **Interessen** | Fragebogen-Ergebnis ansehen und ändern (gibt es schon) |

**B. Organisatorisches – „Konto“**

| Seite | Inhalt |
|---|---|
| **Konto** | Name und Geburtsdatum, Mailadresse, Passwort, Abmelden (auf diesem Gerät / überall), Konto löschen |
| **Datenschutz** | Alle Einwilligungen mit gestuftem Text, Widerspruch zur Zählung, Auskunft nach Art. 15 herunterladen, später Sichtbarkeit für Freunde |
| **Benachrichtigungen** | Preference Center: Newsletter bzw. Wochenmail (P7), Erinnerungen, Neues bei Gefolgtem, Geburtstagsmail. Je Kanal Mail und (in der App) Push. Kommt mit den Benachrichtigungen (Stufe 4) |

**Navigation:**
- **Mobil und App:** Die Leiste unten bekommt eingeloggt „Für dich“ und „Profil“. Über „Profil“ erreicht man A und B als Liste.
- **Desktop:** Unter „Mein Konto“ gibt es eine Seitenleiste mit den Gruppen A und B.

## 6. Bausteine der Personalisierung

Aufwand: S = klein, M = mittel, L = groß. **Fett = von P1 als wichtig markiert.**

| Nr. | Baustein | Nutzen | Aufwand | Recht und Daten |
|---|---|---|---|---|
| **B1** | **„Für dich“-Feed** nach Kontenplan 13 | Kernversprechen der Einwilligung (a) einlösen | M | abgedeckt durch (a) |
| **B2** | **Startseite eingeloggt: 2–3 persönliche Module** (P3) | sofort spürbar persönlich, Startseite bleibt sonst gleich | S–M | wie B1 |
| B3 | Feedback „Mehr davon“ / „Nicht interessiert“ / „Warst du da?“ | Empfehlungen lernen sichtbar | M | unter (a); neue Daten, im Export |
| **B4** | **Folgen von Orten und Reihen** (P6), Künstler später | „Neu bei …“-Listen, Grundlage für Benachrichtigungen | M | Vertrag (lit. b), im Export; braucht die Location-Seiten |
| B5 | Merkliste ausbauen: Kalenderansicht, Kalender-Abo (ICS-Link), Hinweis bei Absage | Alltagsnutzen | S–M | ICS-Link mit geheimem, widerrufbarem Token |
| B6 | Erinnerungen an gemerkte Events (P4: später) | Grund, eingeloggt zu bleiben | M | Dienstmail auf Wunsch, Abmeldelink |
| **B7** | **Wochenmail, zusammen mit dem Newsletter** (P7; P4: später) | starke Bindung | M–L | Werbung → Einwilligung nach § 7 UWG mit Double-Opt-in; bestehende Newsletter-Anmeldungen bestätigen lassen (stehen ohnehin noch aus) |
| B8 | Benachrichtigungen bei Neuem zu Gefolgtem | wie Songkick oder RA | M | Werbung → Einwilligung |
| B9 | Preference Center | Übersicht, weniger Abmeldungen | S | Pflicht, sobald es mehrere Mailarten gibt |
| B10 | Gespeicherte Filter / Suchalarm | schneller Zugriff | S–M | Alarm = Werbung → Einwilligung |
| B11 | Heimat-Stadtteil / „In deiner Nähe“ | bessere Reihenfolge | S | Standort nur im Gerät |
| B12 | Orte aus den Guides merken (Kontenplan E8) | Restaurants, Bars, Spielplätze im Konto | M | wie Merkliste |
| B13 | Jahresrückblick | teilbar, Spaß | S–M | nur eigene Daten |
| B14 | Geburtstagsmail (Kontenplan 9a) | Einwilligungen liegen vor | S | geregelt |
| B15 | Freunde und Sichtbarkeit (Entwurf liegt vor) | sozialer Effekt | L | eigener Plan, Anwalt |
| B16 | Tickets über das Konto | Grund für den Pflicht-Namen | L | eigener Plan |
| B17 | Musikdienst verbinden, Künstler folgen (P6: später) | genaue Musik-Tipps | L | Drittanbieter, eigene Einwilligung |
| **B18** | **Vorschau „Für dich empfohlen“ für Abgemeldete** (P1, wie Rausgegangen): verschwommene Karten mit Schloss-Symbol, Text und Button „Kostenlos registrieren“ | macht den Nutzen eines Kontos sichtbar | S | keine Personendaten; ehrlich gestalten (siehe unten) |

**Zu B2, Vorschlag für die Module auf der Startseite** (eingeloggt, als nachgeladene Insel an fester Stelle):
1. **„Für dich empfohlen“:** bis zu 8 persönliche Picks aus B1, weniger sind erlaubt. Abgemeldet steht an derselben Stelle B18.
2. **„Deine nächsten Events“:** die nächsten gemerkten Events. Die Karte beschriftet sie über `metaZeile`: „Heute“, „Morgen“ oder den Wochentag, laufende mehrtägige Events mit „läuft bis …“. Ausgeblendet, wenn nichts gemerkt ist.
3. **„Neu bei deinen Orten“:** erst mit B4. Bis dahin bleibt es bei zwei Modulen.

Dazu oben eine kurze Begrüßung („Hallo Yannick“), ohne Platz zu verschieben.

**Zu B18, Gestaltung:**
- Die verschwommenen Karten sind feste Platzhalter oder beliebte Events des Tages. Sie werden in der gecachten Seite ausgeliefert, nicht personenbezogen.
- Der Text verspricht nur, was B1 wirklich leistet, z. B. „Mit Konto zeigen wir dir hier Events, die zu deinen Interessen passen.“
- Die Vorschau kann man nicht wegklicken, sie verdeckt aber keine anderen Inhalte (nur dieses Modul).
- Der Button führt zu `/konto/anmelden?neu=1`. Der Stufe-1-Plan hängt `weiter` mit der aktuellen Start-URL an (`web/lib/konto/weiter.ts` lässt `/?datum=…` durch).

## 7. Weg zur App (P5)

**Empfehlung: Capacitor**, also eine App-Hülle um die bestehende Mobil-Website, mit nativen Teilen:
- **Warum:** Der Auftraggeber möchte die heutige Mobilversion als App. Capacitor nutzt genau diesen Code für iOS und Android, ohne zweite Oberfläche. Das ist der schnellste und günstigste Weg, und jede Verbesserung der Website kommt sofort auch in der App an.
- **Native Teile, damit die App mehr ist als eine Website:** Push über Firebase/APNs, Deep Links (diesdas.events/… öffnet die App), Teilen, „In Kalender eintragen“, Merkliste offline, Anmeldung mit sicher gespeichertem Token (Bearer, Kontenplan 3.3) statt Cookie.
  - Das ist auch wichtig für die App-Prüfung von Apple: Reine Website-Hüllen ohne eigenen Mehrwert werden abgelehnt (Richtlinie 4.2).
- **Alternative für später:** React Native/Expo mit eigener Oberfläche, falls die App deutlich anders werden soll als die Website. Teurer, zwei Oberflächen zu pflegen.
- **Pflichten:**
  - Apple- und Google-Entwicklerkonten.
  - Konto-Löschung in der App (gibt es schon).
  - Datenschutz-Angaben im Store („Privacy Nutrition Label“, Google „Data safety“).
  - Datenschutzerklärung um die App ergänzen (Push-Token, Geräte-ID).
- **Ablauf:** Machbarkeitsstudie (1 Woche: Hülle, Anmeldung per Token, Push-Probe, Store-Anforderungen), dann ein eigener App-Plan.

## 8. Stufen (neu nach P1–P7)

| Stufe | Inhalt | Warum hier |
|---|---|---|
| **1** | „Mein dies.das“ mit Unterseiten (Abschnitt 5, ohne Benachrichtigungen), **B1** „Für dich“, **B2** Startseiten-Module 1 und 2, **B18** Vorschau für Abgemeldete | löst das Versprechen der Interessen ein, Struktur für alles Weitere |
| **2** | **B4** Folgen von Orten und Reihen (nach den Location-Seiten), B2-Modul 3 „Neu bei deinen Orten“, B5 Merkliste ausbauen, B3 Feedback | Alltagsnutzen, mehr Signale für Vorschläge |
| **3** | **App:** Machbarkeitsstudie, dann Capacitor-App für iOS und Android, Push-Grundlage | P5; baut auf Stufe 1–2 |
| **4** | Benachrichtigungen (P4: später): B9 Preference Center, **B7** Wochenmail = Newsletter (P7), B6 Erinnerungen, B8 Neues bei Gefolgtem, B14 Geburtstagsmail – per Mail und in der App per Push | ein gemeinsamer Benachrichtigungs-Plan |
| **5** | B15 Freunde, B16 Tickets, B17 Künstler/Musikdienste, B10–B13 | größere eigene Pläne |

## 9. Offene Punkte für den Plan zu Stufe 1
S1–S7 sind bestätigt (18.11.2026), ausgearbeitet in `docs/plan-mein-bereich-stufe1-2026-11-18.md`. Offen bleibt nur S3 (Anrede mit Vornamen) bis zur schriftlichen Bestätigung des Anwalts. App-Entwicklerkonten erst für Stufe 3.

## Quellen (Recherche 18.11.2026)
- Rausgegangen: [App-Seite](https://rausgegangen.de/l/app-download), [Über uns](https://rausgegangen.de/l/about-us), [Social Profiles](https://rausgegangen.de/en/blog/social-profiles/), Datenschutzerklärung `rausgegangen.de/privacy/`, Location-Beispiel [Roncalli's Apollo Varieté](https://rausgegangen.de/locations/roncallis-apollo-variete/)
- Eventbrite: [App-Relaunch 2025](https://ausleisure.com.au/news/eventbrite-reimagines-app-to-focus-on-personalised-event-discovery), [Hilfe „Attending an event“](https://www.eventbrite.com/help/en-us/articles/783059/), [Onboarding-Ablauf (Lazyweb)](https://lazyweb.com/canvas/flows/eventbrite/social-login-and-onboarding)
- DICE: [App Store](https://apps.apple.com/gb/app/dice-live-shows/id898358948?uo=2)
- Resident Advisor: [RA Guide im App Store](https://apps.apple.com/gb/app/ra-guide/id981952703), [Spotify-Partnerschaft](https://musictech.com/news/spotify-resident-advisor-partnership/)
- Songkick, Bandsintown, Fever, Time Out: allgemeine Kenntnis, nicht eigens recherchiert
- Capacitor und die App-Store-Richtlinie 4.2: allgemeine Kenntnis, vor dem App-Plan im Detail zu prüfen
