# Plan: Freunde und Sichtbarkeit der Merkliste („Wer darf sehen, was dir gefällt?“)

Stand: 17.11.2026 · **erste Fassung, Entwurf zur Durchsicht, nicht freigegeben, nichts umgesetzt.** Erstellt von Claude auf Wunsch des Auftraggebers. Kein Rechtsrat: Die rechtlichen Punkte sind Einschätzungen und gehen vor dem Bau an den Anwalt (Abschnitt 9).

**Ziel:** Angemeldete Nutzer können sich mit Freunden verbinden. Jeder entscheidet selbst, wer seine gemerkten Events sieht: nur er selbst, seine Freunde oder alle angemeldeten Nutzer. Auf Eventseiten steht dann zum Beispiel „Lena und 2 weitere Freunde haben das gemerkt“. Vorbild ist die Abfrage bei Rausgegangen, aber mit datenschutzfreundlicher Voreinstellung und ohne die Schwächen, die dort auffallen (Abschnitt 1.3).

**Baut auf:** `docs/plan-nutzerkonten-2026-11-16.md` (Konten, Merkliste im Konto, Sensibel-Filter E13, Einwilligungs-Nachweis 4.4). Dieser Plan beginnt erst, wenn die Konten live sind (Schritt 8 dort).

Es gelten dieselben Regeln wie bei den anderen Plänen: Deploy nur nach OK. SQL liegt als Datei in `database/`, der Auftraggeber führt sie aus. Keine neue Bibliothek ohne Rückfrage. Texte auf Deutsch, Konto-Seiten per du, Datenschutzerklärung in Sie-Form, „Button“ statt „Knopf“.

---

## 1. Ausgangslage

### 1.1 Was es schon gibt (Stand 17.11.2026)
- **Merkliste im Konto:** Tabelle `public.merkliste (nutzer_id, event_id, gemerkt_am)`. Die RLS erlaubt nur das eigene Lesen, Ergänzen und Löschen (`konten_2026-11-16.sql`, Policies „Eigene Merkliste …“). Andere Nutzer sehen heute nichts.
- **Sensibel-Filter (E13):** `public.event_sensibel` kennzeichnet Events, aus deren Merkung sich Art.-9-Daten ableiten lassen. Die Kennzeichnung ist nirgends für Nutzer erkennbar. Ohne ausdrückliche Einwilligung (b) bleiben solche Merkungen nur auf dem Gerät.
- **Anonyme Zählung (E4):** `merk_statistik()` nur für Admins, nur Konten ohne Widerspruch, nie sensible Events. Der Hinweistext verspricht: „Wer was gemerkt hat, sieht dabei niemand.“ Eine öffentliche Zahl („42 haben das gemerkt“) ist laut Kontenplan 13 nur nach eigener Entscheidung und **frühestens ab 5 Personen** vorgesehen.
- **Namen (E16):** Vorname, Nachname und Geburtsdatum sind Pflicht. Sie sind **nicht** für andere gedacht.
- **`profiles.anzeigename`:** Die Spalte gibt es seit `auth_rollen.sql`, ohne Prüfbedingung. `authenticated` darf sie direkt ändern. Der Trigger `profil_anlegen` übernimmt sie aus `raw_user_meta_data`, und die kann jeder beim `signUp` mit dem anon-Key setzen. **Für eine Anzeige vor anderen ist die Spalte so nicht geeignet** (Abschnitt 4.1).
- **Eventseiten** (`app/event/[kategorie]/[slug]/page.tsx`) sind statisch und gecacht (cacheComponents). Persönliches darf dort nur clientseitig nachgeladen werden (Kontenplan 3.5).
- **Mindestalter 16.** Konten von 16- und 17-Jährigen sind möglich.

### 1.2 Begriff
Bei uns heißt es „merken“ (Herz). Rausgegangen nennt das „Likes“. Dieser Plan macht **gemerkte Events** sichtbar, nichts anderes. Orte und Veranstalter folgen erst, wenn man sie merken kann (Kontenplan E8).

### 1.3 Was bei Rausgegangen auffällt (geprüft 17.11.2026)
- Die Datenschutzerklärung (Stand 24.06.2026, `rausgegangen.de/privacy/`, App-Fassung identisch) sagt **nichts** zur Sichtbarkeit von Likes, zu Freunden, Profilen oder Nutzernamen. Weder Zweck noch Rechtsgrundlage noch Voreinstellung sind beschrieben. Als Vorlage taugt sie für diesen Teil nicht.
- In der Abfrage ist „Alle auf Rausgegangen“ vorausgewählt und als „Empfohlen“ hervorgehoben. Das widerspricht dem Grundsatz datenschutzfreundlicher Voreinstellungen (Art. 25 Abs. 2 DSGVO). Die europäischen Datenschutzbehörden (EDSA, Leitlinien 03/2022) zählen solches Hervorheben zu den manipulativen Gestaltungsmustern.
- Die Abfrage koppelt: Wer seine Likes zeigt, sieht im Gegenzug die der anderen. Ob diese Kopplung bei uns zulässig ist, ist Frage A3 an den Anwalt.

---

## 2. Entscheidungen (offen, vom Auftraggeber zu treffen)

| Nr. | Frage | Vorschlag Claude |
|---|---|---|
| F1 | Welche Stufen gibt es? | **Drei Stufen:** „Nur ich“ (Voreinstellung), „Meine Freunde“, „Alle mit dies.das-Konto“. „Alle“ heißt nur angemeldete Nutzer, **nie** das offene Web: nichts im statischen HTML, nichts für Suchmaschinen. |
| F2 | Kopplung wie bei Rausgegangen („dafür siehst du auch die der anderen“)? | **Nur bei Freunden, und dort automatisch:** Freunde sehen sich gegenseitig nur, wenn beide mindestens „Meine Freunde“ gewählt haben. Bei „Alle“ keine Kopplung. Das ist einfacher zu erklären und lässt die Freiwilligkeit der Einwilligung unberührt (Frage A3). |
| F3 | Wie findet man Freunde? | **Version 1 nur per Einladungslink** (einmal gültig, 7 Tage). Keine Suche nach Namen, kein Hochladen von Kontakten, keine Vorschläge „Leute, die du kennen könntest“. Eine Suche nach Anzeigenamen kann später kommen (eigene Entscheidung, Missbrauchsschutz nötig). |
| F4 | Unter welchem Namen erscheint man? | **Frei wählbarer Anzeigename**, Pflicht nur für soziale Funktionen, 3–30 Zeichen, nicht der echte Name. Vor- und Nachname (E16) erscheinen **nie** vor anderen. **Kein Profilbild** in Version 1 (sonst Bild-Upload, Prüfung, Speicher). Stattdessen ein farbiger Kreis mit Initiale. |
| F5 | 16- und 17-Jährige | Höchstens „Meine Freunde“. „Alle“ ist erst ab 18 wählbar (Alter aus dem Pflicht-Geburtsdatum). |
| F6 | Zahl „X haben das gemerkt“ auf Eventseiten | **In Version 1 nicht.** Sichtbar sind nur Freunde und Personen mit „Alle“, jeweils mit Anzeigename. Eine anonyme Gesamtzahl ist ein eigener Zweck (Kontenplan 13, ab 5 Personen) und bleibt eine eigene Entscheidung. |
| F7 | Welche Merkungen sind sichtbar? | **Nur kommende Events** (Datum bzw. `datum_bis` ab heute), **nie sensible Events** (E13), unabhängig von jeder Einwilligung, auch nicht mit (b). |
| F8 | Benachrichtigungen | In Version 1 **keine Mails** (Freundschaftsanfrage, „Lena hat X gemerkt“). Anfragen erscheinen im Konto. Mails wären ein eigener Schritt mit eigenen Texten. |
| F9 | Wann wird gefragt? | **Erst mit dem Start der Freunde-Funktion**, nicht schon jetzt (Abschnitt 5.1). Neue Konten sehen die Frage im Fragebogen, bestehende einmal als Hinweis im Konto mit „Später“. |

---

## 3. Rechtliche Einordnung (Einschätzung, Prüfung durch den Anwalt in Schritt 1)

| Verarbeitung | Daten | Rechtsgrundlage (Vorschlag) | Dauer |
|---|---|---|---|
| Freundschaften | Wer mit wem verbunden ist, Zeitpunkte, offene Anfragen, Sperren | Art. 6 Abs. 1 lit. b DSGVO (vom Nutzer gewählte Funktion des Nutzungsvertrags) | bis zum Entfernen, spätestens mit dem Konto; offene Anfragen 30 Tage |
| Anzeigename | selbst gewählter Name | Art. 6 Abs. 1 lit. b DSGVO | bis zur Änderung, spätestens mit dem Konto |
| Merkliste für andere sichtbar machen | gemerkte kommende Events, Anzeigename | **Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)**, jederzeit widerrufbar, mit Nachweis (Kontenplan 4.4) | bis zum Widerruf, wirkt sofort |
| Einladungslinks | zufälliges Token (nur als Hash gespeichert), Ersteller, Ablauf | Art. 6 Abs. 1 lit. b DSGVO | bis zur Nutzung, höchstens 7 Tage |

Warum Einwilligung für die Sichtbarkeit: Sie macht Verhalten einer Person für Dritte sichtbar, und daraus lassen sich Vorlieben, Wohnort-Nähe und Gewohnheiten ablesen. Mit Einwilligung ist die Entscheidung klar nachweisbar, und der Widerruf ist einfach zu erklären.

**Kritische Punkte und wie der Plan sie löst:**
1. **Art. 9 DSGVO:** Sensible Events sind für andere **nie** sichtbar und werden nicht mitgezählt (F7). Weil die Kennzeichnung nirgends erkennbar ist, verrät auch das Fehlen eines Events nichts. Die Datenbank filtert, nicht die Oberfläche (Abschnitt 4.3).
2. **Voreinstellung (Art. 25 Abs. 2 DSGVO):** „Nur ich“ gilt, bis jemand aktiv etwas anderes wählt. Die drei Optionen sind gleich gestaltet, ohne „Empfohlen“ und ohne Vorauswahl einer offeneren Stufe. „Später“ bzw. Überspringen heißt „Nur ich“.
3. **Kein manipulatives Design:** gleiche Größe, Farbe und Reihenfolge-Logik (von privat nach offen), neutrale Texte, kein Hinweis „die meisten wählen …“.
4. **Klarnamen:** Vor- und Nachname bleiben intern (E16). Andere sehen nur den Anzeigenamen (F4).
5. **Minderjährige:** 16- und 17-Jährige höchstens „Meine Freunde“ (F5).
6. **Bestehende Zusage:** Der Hinweis zur anonymen Zählung („Wer was gemerkt hat, sieht dabei niemand“) bezieht sich auf die Zählung und bleibt wahr. Die Datenschutzerklärung stellt klar, dass Sichtbarkeit nur mit eigener Einwilligung entsteht (Abschnitt 9.2).
7. **DSFA:** Die Entscheidung „keine DSFA“ (`docs/dsfa-schwellenwert-nutzerkonten-2026-11-17.md`) bezog sich auf Konten ohne soziale Funktionen. Mit sichtbarem Verhalten und Freundesnetz wird die Schwellenwertprüfung **neu gemacht** (Schritt 1).
8. **Nutzerinhalte (DSA):** Anzeigenamen sind Inhalte, die Nutzer einstellen und andere sehen. Es braucht einen Meldeweg („Namen melden“) und eine Regel in den Nutzungsbedingungen, dass wir unpassende Namen ändern dürfen. Nach Einschätzung genügt für unsere Größe ein einfacher Meldeweg mit Prüfung (Frage A5).

---

## 4. Datenmodell (`database/freunde_<datum>.sql`, Entwurf)

### 4.1 `profiles` erweitern
- **`anzeigename`** bekommt eine Prüfbedingung: 3–30 Zeichen, Buchstaben, Ziffern, Leerzeichen, `.`, `-`, `_`, beginnt mit Buchstabe oder Ziffer, ohne Leerraum am Rand. Das **direkte Spaltenrecht für `authenticated` entfällt**. Geschrieben wird nur noch über die Funktion `anzeigename_setzen` (Sperrliste, Ratenbegrenzung). Der Trigger `profil_anlegen` übernimmt **keinen** Anzeigenamen mehr aus den Metadaten. Bestehende Werte werden vorher geprüft und notfalls geleert (Kontrollabfrage).
- **`oeffentliche_kennung TEXT UNIQUE`**: zufällig (z. B. 10 Zeichen base32), für Links auf ein Freundesprofil. **Nie die Nutzer-ID nach außen.**
- **`sichtbarkeit TEXT NOT NULL DEFAULT 'ich' CHECK (sichtbarkeit IN ('ich', 'freunde', 'alle'))`**. Geschrieben nur über `einwilligung_setzen` (neue Arten, 4.4).
- Prüfbedingung: `sichtbarkeit <> 'alle'` für Konten unter 18 wird **in der Funktion** geprüft, nicht als CHECK, weil das Alter mit der Zeit wächst.
- Prüfbedingung: `sichtbarkeit = 'ich' OR anzeigename IS NOT NULL`.

### 4.2 Neue Tabellen
- **`freundschaften (a UUID, b UUID, erstellt_am, PRIMARY KEY (a, b), CHECK (a < b))`**: eine Zeile je Paar, Fremdschlüssel auf `profiles` mit `ON DELETE CASCADE`.
- **`freundschaftsanfragen (von UUID, an UUID, erstellt_am, PRIMARY KEY (von, an), CHECK (von <> an))`**: offen, bis angenommen, abgelehnt oder nach 30 Tagen vom Aufräumjob gelöscht.
- **`einladungen (token_hash TEXT PRIMARY KEY, von UUID, erstellt_am, gueltig_bis)`**: Das Token steht nur im Link, gespeichert wird sein SHA-256. Höchstens 5 offene Einladungen je Konto.
- **`sperren (nutzer UUID, gesperrt UUID, erstellt_am, PRIMARY KEY (nutzer, gesperrt))`**: Eine Sperre beendet eine Freundschaft, löscht offene Anfragen in beide Richtungen und verhindert neue. Die gesperrte Person erfährt davon nichts. Sie sieht die andere Person einfach nicht mehr.
- **`anzeigename_meldungen (id, gemeldet UUID, von UUID, grund TEXT, erstellt_am, erledigt_am)`**: Meldeweg (3.8). Nur Admins lesen.
- Alle Tabellen: RLS an, **kein** direktes Recht für `anon`. `authenticated` liest höchstens eigene Zeilen. Geschrieben wird nur über Funktionen.

### 4.3 Lesen fremder Merkungen nur über eine Funktion
Die Policies auf `merkliste` bleiben „nur eigene Zeilen“. Fremde Merkungen gibt **nur** `SECURITY DEFINER`-Funktionen mit `search_path ''` heraus. Sie prüfen innen alle Regeln:
- `wer_hat_gemerkt(event UUID)` → Liste aus `{anzeigename, kennung, ist_freund}`, höchstens 50 Einträge. Enthalten sind:
  - Freunde mit `sichtbarkeit IN ('freunde', 'alle')`, aber nur, wenn die fragende Person selbst mindestens „freunde“ gewählt hat (F2);
  - andere Konten mit `sichtbarkeit = 'alle'`.
  Immer gilt: das Event ist nicht in `event_sensibel`, das Event ist nicht vorbei, keine Sperre in eine der beiden Richtungen, das Konto ist nicht gesperrt (`unter16_gesperrt_am`). Die fragende Person selbst ist nicht enthalten.
- `freund_merkliste(kennung TEXT)` → kommende, nicht sensible Merkungen einer Person, mit denselben Regeln. Für Fremde mit „alle“ ist die Seite ebenfalls erreichbar. Gibt es keine Berechtigung, ist das Ergebnis **leer**, kein Fehler: Ob eine Kennung existiert, verrät die Funktion nicht.
- Nie in den Ergebnissen: Nutzer-ID, Mailadresse, Vor- und Nachname, Geburtsdatum, Zeitpunkt des Merkens.
- `anon` darf keine dieser Funktionen ausführen.

### 4.4 Einwilligungen
- Neue Arten in `einwilligungen`/`einwilligungstexte`: **`sichtbar_freunde`** und **`sichtbar_alle`**. Die Auswahl im Formular wird auf zwei Nachweiszeilen abgebildet: „Nur ich“ = beide `false`, „Freunde“ = `true`/`false`, „Alle“ = beide `true`. So bleibt das bestehende Nachweismodell (ja/nein je Art) unverändert.
- `einwilligung_setzen` bekommt die beiden Zweige. Er setzt `profiles.sichtbarkeit` und prüft: Anzeigename vorhanden, „alle“ nur ab 18, Konto nicht gesperrt.
- Der Widerruf wirkt **sofort**, weil alle Antworten `private, no-store` sind und nichts davon gecacht wird.

### 4.5 Löschen und Export
- Konto löschen → Freundschaften, Anfragen, Einladungen, Sperren per `CASCADE`. Meldungen zu dieser Person werden anonymisiert (`gemeldet = NULL`).
- Export (`/api/konto/export`): eigene Freundesliste (Anzeigenamen), offene Anfragen, eigene Sperren, Sichtbarkeit, Einwilligungsverlauf. **Nicht enthalten:** wer einen selbst gesperrt hat, und die Merklisten anderer.
- Aufräumjob (`pipeline/konten_aufraeumen.py`): offene Anfragen nach 30 Tagen, abgelaufene Einladungen.

---

## 5. Abläufe

### 5.1 Wann die Frage kommt (F9)
- **Neue Konten:** Im Fragebogen kommt nach „Noch kurz zu dir“ ein Schritt „Wer darf sehen, was du merkst?“ mit Anzeigename (Pflicht nur, wenn nicht „Nur ich“) und den drei Optionen. Keine Vorauswahl einer offeneren Stufe, „Überspringen“ = „Nur ich“.
- **Bestehende Konten:** einmaliger Hinweis oben im Konto mit denselben Optionen und „Später“. Kein Pop-up über der ganzen Seite. Das Ändern ist jederzeit im Konto möglich.

### 5.2 Freund hinzufügen (Einladungslink, F3)
1. A erzeugt im Konto einen Link `/konto/freunde/einladung#t=<token>` und teilt ihn selbst (Messenger, Mail). Das Token steht im Fragment, damit es nicht in Server-Logs landet (wie bei den Mail-Links, Kontenplan 5.2).
2. B öffnet den Link angemeldet, sieht A's Anzeigenamen und bestätigt „Freund hinzufügen“. Erst die Bestätigung legt die Freundschaft an. Ein bloßer Aufruf durch Link-Scanner bewirkt nichts.
3. Der Link ist danach verbraucht. B ist nicht angemeldet → Anmeldung mit `weiter` zurück zum Link.
- Freund entfernen: still, ohne Nachricht an die andere Person.

### 5.3 Anzeige auf der Eventseite
- Unter dem Herz eine kleine Zeile, **clientseitig** nachgeladen, nur für angemeldete Nutzer und nur bei kommenden Events: „Lena und 2 weitere Freunde haben das gemerkt“. Ein Klick öffnet die Liste.
- Die statische Seite bleibt unverändert. Ohne Konto, ohne Treffer oder bei sensiblen Events erscheint **nichts**. Es gibt keine Zeile „0 Freunde“, und das Fehlen verrät nichts.

### 5.4 Freundesseite `/konto/freunde/[kennung]`
- `noindex`, statische Hülle, Daten per Client-Abruf. Zeigt Anzeigename, Initialen-Kreis und kommende sichtbare Merkungen. Buttons „Freund entfernen“, „Sperren“, „Namen melden“.

### 5.5 Konto-Seite
- Neuer Abschnitt **„Freunde und Sichtbarkeit“**: drei gleich gestaltete Optionen, Anzeigename ändern, Einladungslink erzeugen, offene Anfragen (annehmen/ablehnen), Freundesliste, gesperrte Personen (entsperren).

---

## 6. API-Routen (unter `web/app/api/konto/`, `private, no-store`, gleicher Wrapper `kontoRoute`)

| Route | Zweck | Bremslimit |
|---|---|---|
| `PUT sichtbarkeit` | `{stufe: 'ich'|'freunde'|'alle'}` → zwei Einwilligungszeilen | 30/Std |
| `PUT anzeigename` | `{anzeigename}` | 10/Std |
| `GET freunde` | Freundesliste, offene Anfragen, eigene Sperren | 120/Std |
| `POST freunde/einladung` | neuen Link erzeugen (max. 5 offen) | 10/Std |
| `POST freunde/einladung/annehmen` | `{token}` → Freundschaft | 20/Std |
| `DELETE freunde/[kennung]` | entfernen | 60/Std |
| `POST sperren` / `DELETE sperren/[kennung]` | sperren/entsperren | 30/Std |
| `POST anzeigename/melden` | `{kennung, grund}` | 10/Std |
| `GET event/[id]/gemerkt-von` | `wer_hat_gemerkt` | 300/Std |
| `GET freunde/[kennung]/merkliste` | `freund_merkliste` | 120/Std |

Ein eigener Schalter **`FREUNDE_AKTIV`** steuert alle Teile wie `KONTEN_AKTIV` (aus → 404, keine Links, keine Frage).

---

## 7. Oberfläche (Einbaustellen)
- `components/interessen-fragebogen.tsx`: neuer Schritt nach „ueber“ (5.1), nur im Modus `onboarding` und nur mit Schalter.
- `components/konto-bereich.tsx`: Abschnitt „Freunde und Sichtbarkeit“ (5.5), einmaliger Hinweis für bestehende Konten.
- `components/client.tsx` (`HerzButton` bzw. Eventseite `app/event/[kategorie]/[slug]/page.tsx`): Client-Insel „… haben das gemerkt“ (5.3).
- Neue Seiten: `app/konto/freunde/[kennung]/page.tsx`, `app/konto/freunde/einladung/page.tsx`.
- Gestaltung der drei Optionen: gleich groß, gleiche Farbe, keine Hervorhebung, Reihenfolge von privat nach offen. Kurze Erklärung je Option, was andere sehen (mit Beispiel-Zeile).

### 7.1 Entwurf der Texte (zur Freigabe in Schritt 1)
> **Wer darf sehen, was du merkst?**
> Du entscheidest, wer deine gemerkten Events sehen kann. Sichtbar sind nur kommende Events und dein Anzeigename, nie dein echter Name. Du kannst das jederzeit im Konto ändern.
>
> ◯ **Nur ich.** Niemand sonst sieht, was du merkst.
> ◯ **Meine Freunde.** Deine Freunde sehen, was du merkst, und du siehst, was sie merken, wenn sie das auch erlauben.
> ◯ **Alle mit dies.das-Konto.** Alle angemeldeten Nutzer sehen bei einem Event, dass du es gemerkt hast. (Ab 18 Jahren.)
>
> Mit „Meine Freunde“ oder „Alle“ willigst du ein, dass wir deine gemerkten kommenden Events mit deinem Anzeigenamen so anzeigen. Du kannst das jederzeit im Konto widerrufen. Dann sieht sie sofort niemand mehr.

Die Sätze für den Nachweis (`sichtbar_freunde-<version>`, `sichtbar_alle-<version>`) kommen wie in Kontenplan 4.4 aus `web/lib/konto/texte.ts` und werden per Generator in `einwilligungstexte` eingetragen.

---

## 8. Sicherheit und Missbrauch
- **Keine Aufzählung von Nutzern:** keine Suche in Version 1. Kennungen sind zufällig. Unbekannte und nicht berechtigte Kennungen liefern dieselbe leere Antwort.
- **Einladungslinks:** 128 Bit Zufall, gespeichert nur als Hash, einmal gültig, 7 Tage, max. 5 offen.
- **Stalking-Schutz:** Sperren wirkt sofort und in beide Richtungen und ist für die gesperrte Person nicht erkennbar. „Alle“ zeigt nie den Zeitpunkt des Merkens und nie vergangene Events, damit sich keine Bewegungsprofile ablesen lassen.
- **Anzeigenamen:** Sperrliste (z. B. „admin“, „diesdas“, „support“, Beleidigungen), Änderung höchstens 3-mal am Tag, Meldeweg mit Admin-Prüfung im Dashboard.
- **Rechte-Prüfung:** Die Whitelist in `konten_rechte_pruefung_<datum>.sql` bekommt die neuen Funktionen. Kein neues `SECURITY DEFINER` ohne Eintrag dort.

---

## 9. Rechtstexte und Freigaben

### 9.1 Fragen an den Anwalt (`docs/anwalt-fragen-freunde-<datum>.md`)
- A1: Reicht Art. 6 Abs. 1 lit. b für Freundschaften und Anzeigenamen, und ist die Einwilligung (lit. a) für die Sichtbarkeit der richtige Weg?
- A2: Ist „Alle mit dies.das-Konto“ (nur angemeldete Nutzer, nicht öffentlich im Web) mit Art. 25 Abs. 2 DSGVO vereinbar, wenn „Nur ich“ voreingestellt ist?
- A3: Ist die Kopplung bei Freunden (gegenseitige Sicht nur, wenn beide zustimmen) unproblematisch für die Freiwilligkeit (Art. 7 Abs. 4 DSGVO)? Wäre auch die Rausgegangen-Kopplung bei „Alle“ zulässig?
- A4: 16- und 17-Jährige: Genügt die Begrenzung auf „Meine Freunde“?
- A5: Welche Pflichten aus dem Digital Services Act treffen uns wegen der Anzeigenamen (Meldeweg, Begründung bei Änderung)?
- A6: Neue DSFA-Schwellenwertprüfung: Reicht eine Begründung, oder ist eine DSFA nötig?

### 9.2 Texte
- **Datenschutzerklärung** (Sie-Form), Abschnitt 13 „Nutzerkonto“: neuer Unterabschnitt „Freunde und Sichtbarkeit“ mit Tabelle (Abschnitt 3), Hinweis auf „Nur ich“ als Voreinstellung, sensible Events nie sichtbar, Sperren und Melden. Klarstellung zur anonymen Zählung.
- **Nutzungsbedingungen:** Regeln für Anzeigenamen (keine fremden Namen, keine Beleidigungen, keine Werbung), unser Recht, unpassende Namen zu ändern, Sperren und Melden.
- **Einwilligungstexte:** `sichtbar_freunde`, `sichtbar_alle` (7.1).
- **DSFA-Schwellenwertprüfung** neu (A6).

---

## 10. Ablauf und Freigaben

| Schritt | Inhalt | Wer | Freigabe/Ergebnis |
|---|---|---|---|
| 0 | Dieser Plan, Entscheidungen F1–F9, Cursor-Prüfung | Auftraggeber | Plan freigegeben |
| 1 | Rechtstexte (9.2), Anwaltsfragen (9.1), DSFA-Prüfung | Claude, dann Anwalt | schriftliche Freigabe |
| 2 | `database/freunde_<datum>.sql` + Tests + Rückbau, Rechte-Prüfung erweitert | Claude, Ausführung Auftraggeber | Kontrolle „ok“, SQL-Tests ohne FEHLER |
| 3 | API-Routen (6), Unit-Tests | Claude | Tests grün |
| 4 | Oberfläche (5, 7), Browser-Prüfung lokal mit zwei Testkonten | Claude | Screenshots |
| 5 | Cursor-Prüfung der Umsetzung | Auftraggeber | ohne kritischen Befund |
| 6 | Deploy mit `FREUNDE_AKTIV` aus, Live-Prüfung (404) | Claude nach OK | — |
| 7 | Schalter an | Auftraggeber | zweites OK |

Jeder Push ist ein Live-Deploy. Gepusht wird nur nach ausdrücklichem OK.

---

## 11. Tests (Auszug)
- **SQL:**
  - A und B befreundet, A „freunde“, B „ich“ → A sieht B nicht, B sieht A nicht (Kopplung F2).
  - A „alle“ → C (nicht befreundet) sieht A bei einem kommenden Event.
  - Sensibles oder vergangenes Event → nie in `wer_hat_gemerkt`.
  - Sperre → beidseitig unsichtbar, Freundschaft und Anfragen gelöscht.
  - 17-Jährige + „alle“ → Fehler `unter_18`.
  - „freunde“ ohne Anzeigename → Fehler.
  - `anon` → keine Rechte.
  - Direkter SELECT auf fremde `merkliste` als `authenticated` → 0 Zeilen.
  - Unbekannte Kennung → leer, kein Fehler.
- **Unit:**
  - `sichtbarkeit` schreibt genau zwei Nachweiszeilen mit Version aus Konstanten.
  - Anzeigename-Regeln und Sperrliste.
  - Einladung einmal gültig, abgelaufen → neutral.
  - Antworten enthalten nie `nutzer_id`, `vorname`, `nachname`, `geburtsdatum`, `gemerkt_am` oder ein Merkmal „sensibel“.
- **Browser:**
  - Zwei Konten, Einladung, Freundschaft.
  - Eventseite zeigt die Zeile nur angemeldet.
  - Widerruf → nach Neuladen sofort weg.
  - Ohne Schalter nichts sichtbar.

## 12. Risiken
- **Unbeabsichtigtes Offenlegen:** durch Voreinstellung „Nur ich“, Filter in der Datenbank und Tests auf verbotene Felder abgesichert.
- **Belästigung:** Sperren, keine Suche, Meldeweg.
- **Leere Funktion zum Start:** Ohne Freunde sieht man nichts. Einladungslinks machen den Einstieg leicht. „Alle“ füllt die Anzeige, sobald genug Nutzer zustimmen.
- **Aufwand:** etwa so groß wie die Schritte 3–5 des Kontenplans. Profilbilder, Suche, Mails und die anonyme Zahl sind bewusst ausgeklammert.

## 13. Offene Punkte
- F1–F9 entscheiden.
- Anwalt A1–A6.
- Später, je eigener Plan: Suche nach Anzeigenamen, Profilbilder, Mail-Benachrichtigungen, anonyme Zahl „X haben das gemerkt“ ab 5 (Kontenplan 13), Orte und Veranstalter folgen.

## 14. Prüfhistorie
- 17.11.2026: erste Fassung (Claude). Anlass: Abfrage bei Rausgegangen „Wer darf sehen was dir gefällt?“. Deren Datenschutzerklärung (Stand 24.06.2026) beschreibt die Funktion nicht. Die Abfrage dort stellt die offenste Stufe voraus und hebt sie als „Empfohlen“ hervor. Beides wird hier bewusst anders gelöst (1.3, 3).
