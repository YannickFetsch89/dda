# Vorlagen: Transfer-Folgenabschätzung Supabase und Eintrag ins Verarbeitungsverzeichnis

Stand: 16.11.2026 · zu Plan 9.2 (`docs/plan-nutzerkonten-2026-11-16.md`), Schritt 2. **Entwurf, keine Rechtsberatung.**
- Der Auftraggeber füllt die Lücken `[…]` aus den Supabase-Unterlagen aus (Checkliste Teil H).
- Beide Texte gehen mit den übrigen Rechtstexten in die anwaltliche Durchsicht (Schritt 6).
- Die ausgefüllten Fassungen gehören in die Firmenunterlagen. Ins Repo kommt nur diese Vorlage.

---

## 1. Transfer-Folgenabschätzung (TIA) – Supabase

**1.1 Beteiligte**
- Verantwortlicher: Rocktician e. K., Erkrather Str. 401, 40231 Düsseldorf (Angebot dies.das.düsseldorf, diesdas.events)
- Auftragsverarbeiter: Supabase Inc. [Sitz laut DPA]. Datenbank-Region: AWS eu-central-1 (Frankfurt), Projekt `dqckcszxoyaxiwwcgxxk`
- Unterauftragsverarbeiter: laut Liste vom [Datum] (abgelegt unter […]), u. a. Amazon Web Services [weitere aus der Liste]

**1.2 Übermittelte Daten**
| Kategorie | Inhalt |
|---|---|
| Kontodaten | Mailadresse, Passwort-Hash, Anlage- und Anmeldezeitpunkte, Sitzungen |
| Merkliste | Event-IDs und Zeitpunkt des Merkens |
| Besondere Kategorien (Art. 9) | Merkungen von Events, die im Backend als sensibel gekennzeichnet sind (z. B. religiöse, gesundheitliche oder queere Veranstaltungen). **Nur mit ausdrücklicher Einwilligung (b)**, sonst nur auf dem Gerät |
| Interessen | Kategorien, Stadtteile, Merkmale (nur mit Einwilligung a) |
| Geburtsdatum | nur mit Einwilligung (d) |
| Einwilligungsnachweise | Handlung, Zeitpunkt, Textfassung |
| Protokolle | IP-Adresse, Zeitpunkt, Nutzer-ID und Mail in den Auth-Logs der Plattform. Aufbewahrung laut Tarif: [Tage] |

Betroffene: registrierte Nutzerinnen und Nutzer ab 16 Jahren, Admins. Erwartete Zahl im ersten Jahr: [Schätzung].

**1.3 Art der Übermittlung**
- Gespeichert wird in Frankfurt.
- Eine Übermittlung in ein Drittland liegt vor, soweit Supabase Inc. oder Unterauftragsverarbeiter aus Drittländern (insbesondere USA, Singapur) auf die Daten zugreifen können, etwa für Betrieb, Support und Fehleranalyse.
- Ein dauerhafter Datenexport in Drittländer ist nach unserem Kenntnisstand nicht vorgesehen. [Mit DPA und Subprocessor-Liste abgleichen.]

**1.4 Übermittlungsinstrument**
- Standardvertragsklauseln der EU-Kommission (2021/914), Modul 2, als Teil des DPA vom [Datum], [Anhang/Seite].
- EU-US Data Privacy Framework: Supabase Inc. ist [zertifiziert / nicht zertifiziert] (Prüfung am [Datum] auf dataprivacyframework.gov). Wenn ja, ergänzend. Die Datenschutzerklärung nennt das DPF nur, wenn es tatsächlich als Grundlage dient (Plan 9.2).

**1.5 Rechtslage im Drittland**
- **USA:** Zugriffsbefugnisse nach FISA Section 702 und Executive Order 12333. Seit Executive Order 14086 (2022) gelten Verhältnismäßigkeitsgrenzen und ein Rechtsbehelfsverfahren (Data Protection Review Court), auf das sich auch die Angemessenheitsentscheidung zum DPF stützt.
  - **Frage an den Anwalt:** Fällt Supabase Inc. unter FISA Section 702 (Anbieter elektronischer Kommunikationsdienste)? Diese Einordnung ist eine Rechtsfrage. Die Vorlage trifft sie nicht.
  - [Transparenzbericht von Supabase prüfen, falls vorhanden: Zahl behördlicher Anfragen.]
- **Singapur:** [nur falls laut DPA oder Subprocessor-Liste Zugriff aus Singapur: Befugnisse nach dem Criminal Procedure Code und dem Personal Data Protection Act. Sonst streichen.]

**1.6 Ergänzende Maßnahmen**
Hier stehen nur Maßnahmen, die auch ohne eigene Schlüsselhoheit wirken.
- Technisch:
  - Speicherung in der EU (Frankfurt).
  - Zugriffe der Website nur über unseren Server. Der Browser spricht nie direkt mit Supabase (Plan 3).
  - Row Level Security auf allen Tabellen, geprüft am 16.11.2026 (Plan 4.0).
  - Transportverschlüsselung (TLS) schützt nur den Übertragungsweg, nicht vor einem Herausgabeverlangen an Supabase. Sie steht deshalb nicht als ergänzende Maßnahme hier.
  - **Frage an den Anwalt:** Supabase verschlüsselt auch im Ruhezustand, hält aber die Schlüssel selbst. Nach den EDSA-Empfehlungen 01/2020 schützt das nicht vor einem Herausgabeverlangen an Supabase. Soll es in der TIA überhaupt genannt werden, und wenn ja, nur als allgemeine Sicherheitsmaßnahme, nicht als ergänzende Maßnahme für den Transfer?
- Datenminimierung:
  - Keine Klarnamen, keine Anschrift, keine Zahlungsdaten.
  - Interessen und Geburtsdatum freiwillig.
  - Sensible Merkungen nur mit ausdrücklicher Einwilligung, nie in Statistik oder Empfehlungen (Plan 9.1, E13).
- Fristen: Löschfristen für unbestätigte, nicht altersbestätigte und inaktive Konten (Plan 9.3).
- Einwilligung: Besondere Kategorien (sensible Merkungen) nur mit ausdrücklicher Einwilligung (b).
- Vertraglich: DPA mit Weisungsbindung, Pflicht zur Information über Behördenanfragen [Klausel im DPA nennen].

**1.7 Ergebnis**
[Das Ergebnis legt der Anwalt fest, nachdem die Fragen in 1.5, 1.6 und unten beantwortet sind. Eine mögliche Form wäre: „Unter Berücksichtigung der SCC, der Speicherung in der EU, der Datenminimierung und der Maßnahmen aus 1.6 ist ein im Wesentlichen gleichwertiges Schutzniveau gewährleistet. Besonders geprüft wurde die Speicherung sensibler Merkungen (Art. 9). Sie erfolgt nur auf ausdrückliche Einwilligung.“ Ob die Einwilligung auf den möglichen Drittlandzugriff hinweisen muss, ist die offene Frage unten.]
- Offener Punkt für den Anwalt: Muss der Einwilligungstext (b) den möglichen Drittlandzugriff ausdrücklich nennen (Art. 49 Abs. 1 lit. a als zusätzliche Absicherung)?

Erstellt am [Datum] von [Name]. Nächste Überprüfung: bei Änderung der Subprocessor-Liste, spätestens [Datum + 1 Jahr].

---

## 2. Verzeichnis der Verarbeitungstätigkeiten (Art. 30) – Eintrag „Nutzerkonten“

| Feld | Inhalt |
|---|---|
| Bezeichnung | Nutzerkonten auf diesdas.events (Merkliste, Interessen, Geburtstagsmails) |
| Verantwortlicher | Rocktician e. K., Erkrather Str. 401, 40231 Düsseldorf, [Kontakt] |
| Zwecke | Konto führen und Anmeldung; Merkliste geräteübergreifend; persönliche Empfehlungen (mit Einwilligung); Beliebtheits-Summen ohne Personenbezug im Ergebnis; Geburtstagsmails (mit Einwilligung); Sicherheit des Dienstes |
| Rechtsgrundlagen | Art. 6 Abs. 1 lit. b (Konto, Merkliste, Nutzungsbedingungen); lit. a (Interessen, Empfehlungen, Geburtstagsmails); Art. 9 Abs. 2 lit. a (sensible Merkungen); lit. f (Summen mit Widerspruch, Sicherheitsprotokolle, Missbrauchsschutz); § 25 Abs. 2 Nr. 2 TDDDG (Cookies, lokaler Speicher) |
| Betroffene | registrierte Personen ab 16 Jahren; Admins |
| Datenkategorien | Mailadresse, Passwort-Hash, Zeitpunkte, Event-IDs der Merkliste, Interessen, Geburtsdatum (freiwillig), Einwilligungsnachweise, IP-Adressen in Protokollen; besondere Kategorien nur ableitbar aus Merkungen gekennzeichneter Events und nur mit ausdrücklicher Einwilligung |
| Empfänger | Supabase Inc. (Auftragsverarbeiter, Datenbank und Anmeldung); [Hoster] (Auftragsverarbeiter, Webserver und Mailversand). Keine Weitergabe an Veranstalter oder Werbepartner |
| Drittlandübermittlung | möglicher Zugriff durch Supabase Inc. und Unterauftragsverarbeiter (USA, ggf. Singapur); SCC Modul 2, TIA vom [Datum]; DPF [ja/nein] |
| Löschfristen | unbestätigte Konten 48 Stunden (spätestens 5 Tage); bestätigte Konten ohne Altersbestätigung 7 Tage (spätestens 10); wegen Alter unter 16 gesperrte Konten beim nächsten Lauf des Aufräumjobs; inaktive Konten nach 24 Monaten; Geburtsdatum sofort beim Widerruf; Plattform-Protokolle laut Supabase-Tarif [Tage]; Missbrauchsschutz rund 1 Stunde im Arbeitsspeicher |
| Technische und organisatorische Maßnahmen | TLS; Speicherung in Frankfurt; Row Level Security und Rechte-Prüfung (16.11.2026); Sitzung nur in HttpOnly-Cookie; Passwörter nur als Hash bei Supabase; Bremslimits; Sensibel-Kennzeichnung im Backend; Zugriff nur für Admins; Protokoll der Einwilligungen mit archiviertem Wortlaut |
| DSFA | Schwellenwertprüfung `docs/dsfa-schwellenwert-nutzerkonten-<datum>.md` (Plan 9.1), Ergebnis: [ … ] |
| Stand | [Datum] |
