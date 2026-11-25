-- Magazin: Redaktionsbeiträge magazin_beitraege_2026-11-25 (Claude-Code-Session, Prüfungen (a)–(i) grün)
-- Erzeugt von docs/magazin-startbeitraege/beitraege_sql.py aus docs/magazin-startbeitraege/beitraege_2026_11_25.py –
-- Texte dort ändern und neu erzeugen. Legt die Beiträge als „in_pruefung“ an (nur per Vorschau-Link sichtbar),
-- wiederholbar, solange nicht veröffentlicht. Veröffentlichen mit der Datei _freigabe.

BEGIN;

-- Top 5 Cafés in Flingern: Wo sich der Weg für Kaffee und Kuchen lohnt
INSERT INTO public.magazin_beitraege (id, slug, rubrik, autor_slug, titel, seo_titel, teaser, inhalt_md, kurzfassung, faq, hero_bild, hero_alt, hero_nachweis, hero_ki, status, gueltig_von, gueltig_bis, naechste_pruefung, event_ids, ort_slugs, quellen, ki_entwurf, pruefung, vorschau_hash)
VALUES ('9a0d7dfc-a326-4901-ac63-aab64c124e6a', 'top-5-cafes-in-flingern', 'genuss', 'laurenz-weigelt', 'Top 5 Cafés in Flingern: Wo sich der Weg für Kaffee und Kuchen lohnt', 'Top 5 Cafés in Flingern – Kaffee, Kuchen, Frühstück', 'Specialty Coffee, italienische Espressobar, Frühstück mit Ruhe: unsere fünf liebsten Cafés in Flingern – und warum die Ackerstraße eine Kaffeemeile ist.', 'Flingern ist eines der besten Viertel Düsseldorfs, um einfach Kaffee trinken zu gehen. In unserem Guide stehen allein hier mehr als zehn Cafés – von der kleinen Rösterei bis zum Frühstückscafé. Die Auswahl ist also groß, und genau deshalb lohnt sich ein genauer Blick.

Unsere fünf Favoriten haben jeweils ein eigenes Profil: Hier geht es um sorgfältig zubereiteten Kaffee, gutes Gebäck, eine Atmosphäre zum Bleiben und das gewisse Etwas, das man nicht in jedem Viertel findet. Die Reihenfolge ist keine strenge Rangliste – jedes Café ist für einen anderen Moment das richtige.

## 1. Jaenner Modern Coffee: für alle, die Kaffee ernst nehmen

Das kleine Café an der Ackerstraße ist die erste Adresse für Kaffeeliebhaber. Der Kaffee wird hier mit viel Sorgfalt zubereitet, besonders der Pour Over hat einen sehr guten Ruf, und die Bohnenauswahl ist vielseitig. Wer auf den Geschmack gekommen ist, nimmt die Bohnen frisch geröstet für zu Hause mit.

Dazu gibt es Kuchen und süße Teilchen, allen voran ein Pistazien-Croissant und einen Schokokuchen, der angenehm wenig süß ist. Am Wochenende kommt ein Frühstück dazu – ein guter Grund, den Samstag hier zu beginnen.

{{ort:jaenner-modern-coffee-flingern}}

## 2. No Worries: Kaffee mit Gastbohnen und Herz

An der Lindenstraße wartet ein kleines Café, das mit richtig gutem Kaffee punktet und immer wieder Gastbohnen zum Probieren anbietet. Neben Espresso-Varianten gibt es Matcha, Tee und einen klassischen Babyccino für die Kleinen – praktisch, wenn Kinder mit dabei sind. Der Iced Latte ist ein Favorit vieler Gäste.

Auf der Theke liegen Croissants, Zimtschnecken, Schokomürbchen und eine wechselnde Kuchenauswahl. Die Atmosphäre ist entspannt, die Inhaber und das Team sind herzlich, und auch hier gibt es Kaffeebohnen zum Mitnehmen.

{{ort:no-worries-flingern}}

## 3. NOSTIMO: ein Stück Italien an der Ackerstraße

Im NOSTIMO fühlt sich der Espresso an wie in einer italienischen Bar: aromatisch, sorgfältig zubereitet, dazu ein Cappuccino mit cremigem Milchschaum. Frische Cornetti, hausgemachte Dolci und herzhafte Panini – etwa mit Mortadella, warm und knusprig serviert – machen es auch zum Ort für ein schnelles Mittagessen.

Wer Pistazie mag, sollte die kleinen Köstlichkeiten damit probieren. Der Inhaber und sein Team empfangen ihre Gäste persönlich und warmherzig, das hübsch eingerichtete Café ist familiär und lädt zum Verweilen ein.

{{ort:nostimo-flingerns-finest-flingern}}

## 4. MERCY coffee company: Kuchen, Bagels und Zeit zum Lesen

Das MERCY an der Birkenstraße ist klein, aber richtig gemütlich und liebevoll eingerichtet – ein Ort, an dem man gerne hängen bleibt, ein Buch dabei hat oder sich mit Freunden trifft. Neben gutem Kaffee kommen auch heiße Schokolade und Tee gut an.

Die Stärke ist der Kuchen: Karottenkuchen und Zitronen-Käsekuchen gehören zu den Empfehlungen. Wer es herzhaft mag, nimmt einen frisch getoasteten Bagel, etwa mit Tomate und Mozzarella. Verschiedene Milchalternativen sind selbstverständlich.

{{ort:mercy-coffee-company-flingern}}

## 5. Café Liebe: Frühstück ohne Eile

Wer in Flingern in Ruhe frühstücken möchte, ist im Café Liebe an der Platanenstraße richtig. Das marokkanische Frühstück ist der Tipp des Hauses: Eier, die genau auf den Punkt kommen, dazu Lachs und frische Beilagen, die gut zusammenpassen. Die Beeren-Bowl mit frischem Obst, Banane und Nüssen ist liebevoll angerichtet.

Das Ambiente ist stilvoll und gemütlich, draußen lässt es sich angenehm sitzen. Ideal für ein ausgiebiges Frühstück zu zweit oder mit Freunden.

{{ort:cafe-liebe-flingern}}

## Die Ackerstraße: Flingerns Kaffeemeile

Auffällig ist, wie viele gute Cafés an einer einzigen Straße liegen. Neben Jaenner und NOSTIMO findet ihr an der Ackerstraße das [Café Kleinod](/guides/restaurants-cafes/cafe-kleinod-flingern), in dem ein Paar aus Italien hausgemachte Kuchen, Tiramisu und Gebäck mit Pistazie serviert – ruhig gelegen und ideal zum Plaudern. Das [coffiez](/guides/restaurants-cafes/coffiez-flingern) ist modern und gemütlich zugleich, der Chef bedient oft selbst, und der Matcha mit Erdbeeren ist ein Hingucker. Weiter östlich röstet das [Fjaka Café & Clubhouse](/guides/restaurants-cafes/fjaka-cafe-clubhouse-flingern) seinen Kaffee selbst, dazu gibt es einen sehr cremigen New York Cheesecake.

Wer an einem freien Vormittag Zeit hat, kann die Ackerstraße entlangspazieren und sich von Café zu Café treiben lassen – Flingern lässt sich so gut kennenlernen.

## Noch mehr gute Adressen

Zwei weitere Tipps für den Brunch: Im [Dritan Alsela Coffee](/guides/restaurants-cafes/dritan-alsela-coffee-flingern) an der Schlüterstraße hat das Frühstück einen festen Platz, mit internationalen Gerichten und frischen Baguettes. Und im [Espresso Perfetto](/guides/restaurants-cafes/espresso-perfetto-flingern) an der Grafenberger Allee lohnt sich die schöne Terrasse, dazu gibt es ukrainische Syrnyki, frisch gebratene Käsepfannkuchen.

Alle Cafés und Restaurants im Viertel findet ihr in unserem Guide unter [Flingern](/guides/restaurants-cafes/stadtteil/flingern).

{{guide:restaurants-cafes}}
', ARRAY['Jaenner Modern Coffee: Pour Over und frisch geröstete Bohnen zum Mitnehmen.', 'No Worries: wechselnde Gastbohnen, Zimtschnecken und ein Babyccino für die Kleinen.', 'NOSTIMO: Espresso, Cornetti und Panini wie in einer italienischen Bar.', 'MERCY coffee company: Kuchen und Bagels in einem kleinen, gemütlichen Café.', 'Café Liebe: marokkanisches Frühstück und Bowls ohne Eile.']::text[], '[{"frage": "Wo gibt es in Flingern besonders guten Kaffee?", "antwort": "Für Specialty Coffee sind Jaenner Modern Coffee und No Worries gute Adressen, beide verkaufen auch Bohnen zum Mitnehmen. Das Fjaka röstet seinen Kaffee selbst."}, {"frage": "Wo kann man in Flingern gut frühstücken?", "antwort": "Im Café Liebe gibt es ein marokkanisches Frühstück und Bowls, im Dritan Alsela Coffee internationale Frühstücksgerichte. Jaenner Modern Coffee bietet am Wochenende Frühstück an."}, {"frage": "Welches Café in Flingern passt mit Kindern?", "antwort": "No Worries hat einen Babyccino für die Kleinen und eine entspannte Atmosphäre."}]'::jsonb, '/fallback/sprachcafe-1.webp', 'Symbolbild: Gäste an Holztischen in einem Café mit großen Fenstern', 'Symbolbild', FALSE, 'in_pruefung', NULL, NULL, '2027-02-01', '{}'::uuid[], ARRAY['jaenner-modern-coffee-flingern', 'no-worries-flingern', 'nostimo-flingerns-finest-flingern', 'mercy-coffee-company-flingern', 'cafe-liebe-flingern']::text[], '[{"titel": "dies.das.düsseldorf: Restaurants & Cafés in Flingern", "url": "https://diesdas.events/guides/restaurants-cafes/stadtteil/flingern", "abgerufen_am": "2026-11-25"}]'::jsonb, '{"modell": "claude-opus-5-5", "art": "claude-code-session", "profil": "laurenz-weigelt", "prompt_version": "manuell-2026-11-25", "datenbasis": "Guide Restaurants & Cafés (orte, Flingern), Stand 25.11.2026", "zeitpunkt": "2026-11-25T15:16:59.308688+00:00"}'::jsonb, '{"ergebnis": "gruen", "punkte": [], "zeitpunkt": "2026-11-25T15:16:59.312608+00:00", "lauf": "claude-code-session"}'::jsonb, 'b3c91efdbbfc5eaf9d2f459fbde1fd07787a494c8bfecf226da90020bca69cbd')
ON CONFLICT (slug) DO UPDATE SET rubrik = EXCLUDED.rubrik, autor_slug = EXCLUDED.autor_slug, titel = EXCLUDED.titel, seo_titel = EXCLUDED.seo_titel, teaser = EXCLUDED.teaser, inhalt_md = EXCLUDED.inhalt_md, kurzfassung = EXCLUDED.kurzfassung, faq = EXCLUDED.faq, hero_bild = EXCLUDED.hero_bild, hero_alt = EXCLUDED.hero_alt, hero_nachweis = EXCLUDED.hero_nachweis, hero_ki = EXCLUDED.hero_ki, status = EXCLUDED.status, gueltig_von = EXCLUDED.gueltig_von, gueltig_bis = EXCLUDED.gueltig_bis, naechste_pruefung = EXCLUDED.naechste_pruefung, event_ids = EXCLUDED.event_ids, ort_slugs = EXCLUDED.ort_slugs, quellen = EXCLUDED.quellen, ki_entwurf = EXCLUDED.ki_entwurf, pruefung = EXCLUDED.pruefung, vorschau_hash = EXCLUDED.vorschau_hash
WHERE public.magazin_beitraege.status <> 'veroeffentlicht';

-- 10 Empfehlungen für Familien im Dezember: Düsseldorf mit Kindern
INSERT INTO public.magazin_beitraege (id, slug, rubrik, autor_slug, titel, seo_titel, teaser, inhalt_md, kurzfassung, faq, hero_bild, hero_alt, hero_nachweis, hero_ki, status, gueltig_von, gueltig_bis, naechste_pruefung, event_ids, ort_slugs, quellen, ki_entwurf, pruefung, vorschau_hash)
VALUES ('79b06de0-41f3-4647-bed2-d07956059ebf', '10-empfehlungen-fuer-familien-im-dezember', 'familie', 'amelie-glasner', '10 Empfehlungen für Familien im Dezember: Düsseldorf mit Kindern', 'Düsseldorf mit Kindern im Dezember: 10 Tipps', 'Musical, Kinderkino, Marionettentheater und ein Weihnachtsmarkt mit Rodelbahn: zehn Ideen für Familien in Düsseldorf und Umgebung im Dezember.', 'Im Dezember ist in Düsseldorf für Familien besonders viel los: Bühnen spielen Weihnachtsstücke, Museen laden zu Familienführungen ein, und auf den Weihnachtsmärkten drehen sich die Karussells. Aus unserem Kalender haben wir zehn Ideen ausgewählt, die gut zu Kindern passen – von der großen Musicalbühne bis zur Vorlesestunde in der Bücherei um die Ecke.

Termine, Uhrzeiten und Preise stehen in den Karten unter jedem Tipp. Sie kommen live aus unserem Kalender – ändert sich etwas, seht ihr es dort sofort.

## 1. Musical-Klassiker im Capitol: Der Glöckner von Notre Dame

Im Capitol Theater in Flingern steht das Disney-Musical über den Glöckner Quasimodo auf dem Spielplan, der sich in Notre-Dame versteckt und sich nach dem Leben draußen sehnt – bis die mutige Esmeralda ihm beisteht. Die Songs stammen von Alan Menken und Stephen Schwartz, das Ensemble des Budapester Operettentheaters spielt mit einem vierzehnköpfigen Live-Orchester. Gespielt wird an vielen Terminen im Dezember. Die Geschichte hat auch ernste Momente, für Schulkinder ist sie ein großes Bühnenerlebnis.

{{event:6d392e7f-f941-4161-a698-a312c088d5b3}}

## 2. Weihnachtsmusical in Ratingen: Santa Claus

Ein Musical ausdrücklich für Kinder und Familien: In der Stadthalle Ratingen kommt „Santa Claus – das Musical“ auf die Bühne – ein kurzer Ausflug über die Stadtgrenze, der sich zum Start in die Adventszeit anbietet.

{{event:0496484d-939e-47a4-8322-43de7a900e12}}

## 3. Geburtstagsparty mit den tonies in der Tonhalle

Wer zu Hause eine Toniebox hat, kennt die kleinen Hörfiguren. Jetzt laden die tonies zur großen Geburtstagsparty in die Tonhalle ein – ein Termin für alle, bei denen die Box im Kinderzimmer nicht mehr stillsteht.

{{event:d9f8745e-3f2d-4507-9045-c7105067d9d9}}

## 4. Kinderkino am Sonntag: Momo im Filmmuseum

Das Familienkino in der Black Box im Filmmuseum in der Altstadt zeigt „Momo“ – die Geschichte nach Michael Ende über das Mädchen, das den grauen Herren die gestohlene Zeit zurückholt. Ein schöner Programmpunkt für einen Adventssonntag, der draußen vielleicht grau ist.

{{event:d787de03-bca6-4aea-af7e-7019709cb691}}

## 5. Michael Ende auf der Marionettenbühne: Der Wunschpunsch

Noch einmal Michael Ende: Das Düsseldorfer Marionetten-Theater in der Altstadt spielt „Der satanarchäolügenialkohöllische Wunschpunsch“. Schon der Titel ist ein Zungenbrecher, den Kinder lieben – und Marionettentheater ist eine Kunstform, die viele Kinder heute gar nicht mehr kennen.

{{event:ac40e918-e39d-4cea-981b-df9b0f155a21}}

## 6. Anime, Mangas und Super Mario: Familienführung im NRW-Forum

Ob Sailor Moon, One Piece oder Super Mario: Die Familienführung im NRW-Forum ist eine Entdeckungsreise durch die ostasiatische Popkultur. Rund tausend Werke zeigen Essen, Mode, Filme und Comics aus China, Hongkong, Japan, Südkorea und Taiwan. Kleine und große Besucherinnen und Besucher schauen, hören und probieren gemeinsam aus – ideal für Familien mit Kindern, die selbst gerade Fans sind.

{{event:47b0356c-ad3a-42dc-a9f0-cddbd6ec9b42}}

## 7. Kunst zum Mitmachen: Familienworkshop im K20

Im K20 am Grabbeplatz öffnet der Playground für einen offenen Familienworkshop. Offen heißt: Ihr könnt dazukommen und gemeinsam mit euren Kindern kreativ werden – ein guter Weg, Kinder ohne Druck an ein Kunstmuseum heranzuführen.

{{event:55e7be0d-5bf0-4851-b895-0c2fa34e3f7a}}

## 8. Spieletag in Neuss: Rheingespielt XXL

Das Rheinische Landestheater in Neuss wird zum großen Spieletag: Bei „Rheingespielt XXL“ dreht sich alles ums gemeinsame Spielen. Für Familien, die gerne am Tisch zusammensitzen, ist das ein Ausflug wert.

{{event:f414c593-afa4-4043-bdba-e6b49c4c51c4}}

## 9. Weihnachtsmarkt mit Rodelbahn: Gerresheim

Unter den Weihnachtsmärkten ist der Markt auf dem Gerricusplatz in Gerresheim für Kinder ein Höhepunkt. An zwei Adventswochenenden gibt es dort eine rund zwanzig Meter lange Rodelbahn, ein Puppentheater und Eisstockschießen für Groß und Klein. Wer an anderen Tagen unterwegs ist: Im Areal Böhler in Heerdt spielt die Puppenbühne Maatz, dazu gibt es Kinderschminken und Mitmachaktionen, und vor Schloss Benrath fährt die traditionelle Eisenbahn für Kinder. Welche Märkte heute geöffnet haben, zeigt unser [Weihnachtsmarkt-Guide](/guides/weihnachtsmaerkte).

{{ort:weihnachtsmarkt-gerresheim}}

{{ort:weihnachtszauber-areal-boehler-heerdt}}

## 10. Vorlesen und Basteln in den Stadtbüchereien

Die Stadtbüchereien sind im Dezember eine kleine Fundgrube für Familien: In vielen Stadtteilen gibt es Geschichtenzeiten zum Zuhören, weihnachtliche Bastelaktionen und Workshops mit 3D-Stiften. Zwei Beispiele: In der Zentralbibliothek im KAP1 wartet man gemeinsam aufs Christkind, in der Stadtbücherei Unterrath wird weihnachtlich vorgelesen. Der Vorteil: Die Büchereien liegen oft direkt im Viertel, der Weg ist kurz.

{{event:732761d0-8557-46eb-adf8-d1bb6bc89517}}

{{event:8738c603-107d-4a9e-952f-c348551f619a}}

## Noch mehr Ideen für Familien

Das waren unsere zehn Tipps – im Kalender gibt es noch viel mehr: Kindertheater, Kreativworkshops, Nikolausaktionen und Familienbrunch. Alle Termine findet ihr gesammelt unter [Familie](/kategorie/familie), und was am Wochenende los ist, steht in unserem [Wochenend-Programm](/wochenende).

{{guide:weihnachtsmaerkte}}
', ARRAY['Musicals für Kinder: „Der Glöckner von Notre Dame“ im Capitol, „Santa Claus“ am 5. Dezember in Ratingen.', 'Am 6. Dezember läuft „Momo“ im Familienkino des Filmmuseums.', 'Am 12. Dezember: Familienführung im NRW-Forum, Familienworkshop im K20 und Spieletag in Neuss.', 'Weihnachtsmarkt Gerresheim mit Rodelbahn und Puppentheater an zwei Adventswochenenden.', 'Vorlesen und Basteln in den Stadtbüchereien, etwa am 19. Dezember in der Zentralbibliothek.']::text[], '[{"frage": "Was kann man im Dezember mit Kindern in Düsseldorf unternehmen?", "antwort": "Zum Beispiel ein Musical im Capitol, Kinderkino im Filmmuseum, Marionettentheater in der Altstadt, Familienführungen in Museen wie dem NRW-Forum und dem K20, Weihnachtsmärkte mit Kinderprogramm und Vorlesestunden in den Stadtbüchereien."}, {"frage": "Welcher Weihnachtsmarkt in Düsseldorf hat besonders viel für Kinder?", "antwort": "Gerresheim mit Rodelbahn und Puppentheater, das Areal Böhler mit der Puppenbühne Maatz, Schloss Benrath mit der Kindereisenbahn und die Nordstraße mit ihrem Kids-Day am Montag."}, {"frage": "Wo finde ich alle Familienevents in Düsseldorf?", "antwort": "Im Kalender von dies.das.düsseldorf unter der Kategorie Familie, mit Datum, Ort und Preis."}]'::jsonb, '/ort-bilder/weihnachtsmaerkte/gerresheim.webp', 'Weihnachtsmarkt in Gerresheim am Abend: Kinderkarussell vor der Basilika, beleuchtete Hütten', 'dies.das.düsseldorf', FALSE, 'in_pruefung', '2026-12-01', '2026-12-31', '2026-12-08', ARRAY['6d392e7f-f941-4161-a698-a312c088d5b3', '0496484d-939e-47a4-8322-43de7a900e12', 'd9f8745e-3f2d-4507-9045-c7105067d9d9', 'd787de03-bca6-4aea-af7e-7019709cb691', 'ac40e918-e39d-4cea-981b-df9b0f155a21', '47b0356c-ad3a-42dc-a9f0-cddbd6ec9b42', '55e7be0d-5bf0-4851-b895-0c2fa34e3f7a', 'f414c593-afa4-4043-bdba-e6b49c4c51c4', '732761d0-8557-46eb-adf8-d1bb6bc89517', '8738c603-107d-4a9e-952f-c348551f619a']::uuid[], ARRAY['weihnachtsmarkt-gerresheim', 'weihnachtszauber-areal-boehler-heerdt']::text[], '[{"titel": "dies.das.düsseldorf: Familienevents", "url": "https://diesdas.events/kategorie/familie", "abgerufen_am": "2026-11-25"}, {"titel": "dies.das.düsseldorf: Weihnachtsmärkte", "url": "https://diesdas.events/guides/weihnachtsmaerkte", "abgerufen_am": "2026-11-25"}]'::jsonb, '{"modell": "claude-opus-5-5", "art": "claude-code-session", "profil": "amelie-glasner", "prompt_version": "manuell-2026-11-25", "datenbasis": "Eventkalender (Kategorie family, Dezember 2026) und Weihnachtsmarkt-Guide, Stand 25.11.2026", "zeitpunkt": "2026-11-25T15:16:59.308688+00:00"}'::jsonb, '{"ergebnis": "gruen", "punkte": [], "zeitpunkt": "2026-11-25T15:16:59.315214+00:00", "lauf": "claude-code-session"}'::jsonb, '42f5d0b2da9d10c30c69335ff912c643e1531cec5cfd4abfea4d57fa09af661e')
ON CONFLICT (slug) DO UPDATE SET rubrik = EXCLUDED.rubrik, autor_slug = EXCLUDED.autor_slug, titel = EXCLUDED.titel, seo_titel = EXCLUDED.seo_titel, teaser = EXCLUDED.teaser, inhalt_md = EXCLUDED.inhalt_md, kurzfassung = EXCLUDED.kurzfassung, faq = EXCLUDED.faq, hero_bild = EXCLUDED.hero_bild, hero_alt = EXCLUDED.hero_alt, hero_nachweis = EXCLUDED.hero_nachweis, hero_ki = EXCLUDED.hero_ki, status = EXCLUDED.status, gueltig_von = EXCLUDED.gueltig_von, gueltig_bis = EXCLUDED.gueltig_bis, naechste_pruefung = EXCLUDED.naechste_pruefung, event_ids = EXCLUDED.event_ids, ort_slugs = EXCLUDED.ort_slugs, quellen = EXCLUDED.quellen, ki_entwurf = EXCLUDED.ki_entwurf, pruefung = EXCLUDED.pruefung, vorschau_hash = EXCLUDED.vorschau_hash
WHERE public.magazin_beitraege.status <> 'veroeffentlicht';

COMMIT;

-- Kontrollabfrage – erwartet je Beitrag eine Zeile mit „ok“
SELECT slug, status, pruefung ->> 'ergebnis' AS pruefung,
       CASE WHEN status = 'in_pruefung' AND pruefung ->> 'ergebnis' = 'gruen' AND vorschau_hash IS NOT NULL
            THEN 'ok' ELSE 'FEHLER' END AS kontrolle
FROM public.magazin_beitraege WHERE slug IN ('top-5-cafes-in-flingern', '10-empfehlungen-fuer-familien-im-dezember') ORDER BY slug;
