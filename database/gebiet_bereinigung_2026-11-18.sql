-- gebiet_bereinigung_2026-11-18.sql – DiesDasDüsseldorf
-- Events außerhalb von Düsseldorf, Neuss und Ratingen löschen (Plan Locations E3, 18.11.2026).
-- ERZEUGT von pipeline/gebiet.py (python -m pipeline.gebiet --sql). Abhängige Zeilen (Merkliste,
-- Sensibel-Kennzeichnung, SEO-Entscheidungen) löschen sich mit (ON DELETE CASCADE), Meldungen behalten
-- ihre Daten (SET NULL). Ausführen als postgres im Supabase-SQL-Editor, nicht während eines Pipeline-Laufs.
-- Anzahl: 348 Events. Gründe: {'Stadt': 326, 'auswärtiger': 16, 'PLZ': 6}
--
--   2026-11-24 | Theater Duisburg – Opernfoyer | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-12-06 | Opernplatz, Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-12 | Hopfen und Salz | Hopfen und Salz, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-04-03 | Online language evening "Gelsenkirchen and worldwide" (Onlin |  | Stadt Gelsenkirchen | Meetup.com
--   2026-11-06 | Neanderthal Museum |  | auswärtiger Ort | Rausgegangen
--   2026-12-23 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-12-26 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-10-31 | Vienna House Easy by Wyndham Dortmund | Vienna House Easy by Wyndham Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-10-31 | Hugendubel Ingolstadt | Hugendubel Ingolstadt, München | Stadt München | PRINZ.de Düsseldorf
--   2026-10-31 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-10-31 | Messe / Party | Messe / Party, Solingen | Stadt Solingen | PRINZ.de Düsseldorf
--   2026-10-31 | Lokschuppen Bottrop | Lokschuppen Bottrop | Stadt Bottrop | PRINZ.de Düsseldorf
--   2026-10-31 | Vienna House Easy by Wyndham Dortmund | Vienna House Easy by Wyndham Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-10-31 | Donkey Club | Donkey Club, Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-10-31 | Zirkus des Horrors - Oberhausen | Zirkus des Horrors - Oberhausen | Stadt Oberhausen | PRINZ.de Düsseldorf
--   2026-10-31 | Städtisches Bühnenhaus | Städtisches Bühnenhaus, Wesel | Stadt Wesel | PRINZ.de Düsseldorf
--   2026-10-31 | Opernhaus Wuppertal | Opernhaus Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-10-31 | Gaststätte Vennen Im alten Brauhaus | Gaststätte Vennen Im alten Brauhaus, Korschenbroic | Stadt Korschenbroich | PRINZ.de Düsseldorf
--   2026-10-31 | Steinbruch Duisburg | Steinbruch Duisburg | Stadt Duisburg | PRINZ.de Düsseldorf
--   2026-10-31 | Cabaret Queue | Cabaret Queue, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-10-31 | Theater Fletch Bizzel Olpketal | Theater Fletch Bizzel Olpketal, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-10-31 | Theater im Gründungshaus | Theater im Gründungshaus, Mönchengladbach | Stadt Mönchengladbach | PRINZ.de Düsseldorf
--   2026-10-31 | Werkhof Kulturzentrum Hagen - Hohenlimburg | Werkhof Kulturzentrum Hagen - Hohenlimburg | Stadt Hagen | PRINZ.de Düsseldorf
--   2026-10-31 | Rockin Rooster Club | Rockin Rooster Club, Haan | Stadt Haan | PRINZ.de Düsseldorf
--   2026-10-31 | Zum Köhlerliesel | Zum Köhlerliesel, Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-10-31 | Zum Köhlerliesel | Zum Köhlerliesel, Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-10-31 | Mietbar | Mietbar, Grevenbroich | Stadt Grevenbroich | PRINZ.de Düsseldorf
--   2026-10-31 | Zeche Carl | Zeche Carl, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-10-31 | Lokschuppen Bottrop | Lokschuppen Bottrop | Stadt Bottrop | PRINZ.de Düsseldorf
--   2026-10-31 | Kulturfabrik Krefeld | Kulturfabrik Krefeld | Stadt Krefeld | PRINZ.de Düsseldorf
--   2026-10-31 | Amici | Amici, Stuttgart | Stadt Stuttgart | PRINZ.de Düsseldorf
--   2026-10-31 | Lizzy Lou Club | Lizzy Lou Club, Bottrop | Stadt Bottrop | PRINZ.de Düsseldorf
--   2026-10-31 | Rouge Showpalast Bochum | Rouge Showpalast Bochum | Stadt Bochum | PRINZ.de Düsseldorf
--   2026-04-11 | Waldmeister | Holbeinstr.6, 42719 Solingen | PLZ 42719 | Resident Advisor
--   2026-11-12 | Kokerei Zollverein | Kokerei Zollverein, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-11-12 | MAKU Restaurant & Bar | MAKU Restaurant & Bar, Solingen | Stadt Solingen | PRINZ.de Düsseldorf
--   2026-11-12 | Talton Theater | Talton Theater, Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-11-12 | NEW Box | NEW Box, Mönchengladbach | Stadt Mönchengladbach | PRINZ.de Düsseldorf
--   2026-11-05 | Visiodrom im Gaskessel Wuppertal | Visiodrom im Gaskessel Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-10-31 | OBEX | Oberhausen | OBEX | Oberhausen | Stadt Oberhausen | PRINZ.de Düsseldorf
--   2026-10-31 | Café Yumi | Café Yumi, Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-11-12 | Theater im Gründungshaus | Theater im Gründungshaus, Mönchengladbach | Stadt Mönchengladbach | PRINZ.de Düsseldorf
--   2026-10-31 | Schauinsland-Reisen-Arena | Schauinsland-Reisen-Arena, Duisburg | Stadt Duisburg | PRINZ.de Düsseldorf
--   2026-10-31 | Nähe Fritz-Henßler-Haus | Nähe Fritz-Henßler-Haus, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-10-31 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-10-31 | Museum Tuppenhof | Museum Tuppenhof, Kaarst | Stadt Kaarst | PRINZ.de Düsseldorf
--   2026-10-31 | Sputnikhalle Münster | Sputnikhalle Münster, Munster | Stadt Münster | PRINZ.de Düsseldorf
--   2026-10-31 | Nähe Fritz-Henßler-Haus | Nähe Fritz-Henßler-Haus, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-10-31 | NEW Kunstwerk | NEW Kunstwerk, Mönchengladbach | Stadt Mönchengladbach | PRINZ.de Düsseldorf
--   2026-10-31 | Katakomben Theater im Girardet Haus | Katakomben Theater im Girardet Haus, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-10-31 | Westfalenhallen Dortmund | Westfalenhallen Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-10-31 | Bürgerzentrum Villa Rü | Bürgerzentrum Villa Rü, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-10-31 | Spö 407 | Spö 407, Mönchengladbach | Stadt Mönchengladbach | PRINZ.de Düsseldorf
--   2026-10-31 | Theater Mönchengladbach | Theater Mönchengladbach | Stadt Mönchengladbach | PRINZ.de Düsseldorf
--   2026-10-31 | Waldborn Eventlocation | Waldborn Eventlocation, Duisburg | Stadt Duisburg | PRINZ.de Düsseldorf
--   2026-11-12 | Cabaret Queue | Cabaret Queue, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-10-31 | Lizzy Lou Club | Lizzy Lou Club, Bottrop | Stadt Bottrop | PRINZ.de Düsseldorf
--   2026-11-12 | PROJEKT 42 | PROJEKT 42, Mönchengladbach | Stadt Mönchengladbach | PRINZ.de Düsseldorf
--   2026-10-31 | Neanderthal Museum |  | auswärtiger Ort | Rausgegangen
--   2026-12-13 | Opernplatz, Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-10-31 | Visiodrom im Gaskessel Wuppertal | Visiodrom im Gaskessel Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-10-31 | Neanderthal Museum |  | auswärtiger Ort | Rausgegangen
--   2026-10-31 | Opernhaus Dortmund (Opernfoyer) | Opernhaus Dortmund (Opernfoyer) | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-10-28 | Mettmann |  | Stadt Mettmann | Kulturportal Düsseldorf
--   2026-12-12 | Galerie für Zeitgenössische Kunst | Galerie für Zeitgenössische Kunst, Leipzig | Stadt Leipzig | PRINZ.de Düsseldorf
--   2026-11-14 | Galerie für Zeitgenössische Kunst | Galerie für Zeitgenössische Kunst, Leipzig | Stadt Leipzig | PRINZ.de Düsseldorf
--   2026-10-31 | Mettmann |  | Stadt Mettmann | Kulturportal Düsseldorf
--   2026-11-01 | oehme brot und kuchen | düsseldorferstr.81-85 meetup162 meerbusch | Stadt meerbusch | Meetup.com
--   2026-12-27 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-19 | Theater Duisburg – Opernfoyer | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-05 | Kölner Straße 11 | Kölner Str. 11, 47805 Krefeld, Germany 47805 Krefe | PLZ 47805 | Meetup.com
--   2026-11-15 | Theater Krefeld | Theater Krefeld | Stadt Krefeld | PRINZ.de Düsseldorf
--   2026-11-03 | Theater Krefeld | Theater Krefeld | Stadt Krefeld | PRINZ.de Düsseldorf
--   2026-11-03 | Westfalenhallen Dortmund | Westfalenhallen Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-03 | Großer Konzertsaal | Großer Konzertsaal, Solingen | Stadt Solingen | PRINZ.de Düsseldorf
--   2026-11-03 | Zeche Carl | Zeche Carl, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-11-12 | Hofbräu im Königshof | Hofbräu im Königshof, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-11-12 | Hansa Theater Hörde | Hansa Theater Hörde, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-03 | Haus für Familien / Campus | Haus für Familien / Campus, Kempen | Stadt Kempen | PRINZ.de Düsseldorf
--   2026-11-03 | 24m Ebene in der Kohlenwäsche, UNESCO-Welterbe Zollverein | 24m Ebene in der Kohlenwäsche, UNESCO-Welterbe Zol | Stadt Essen | PRINZ.de Düsseldorf
--   2026-11-03 | Weingrün | Weingrün, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-03 | Katakomben-Theater im Girardet Haus | Katakomben-Theater im Girardet Haus, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-11-03 | Ebertbad Oberhausen | Ebertbad Oberhausen | Stadt Oberhausen | PRINZ.de Düsseldorf
--   2026-12-06 | Opernplatz, Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-06 | Theater Duisburg | Theater Duisburg | Stadt Duisburg | PRINZ.de Düsseldorf
--   2026-11-06 | Kulturraffinerie K714 | Kulturraffinerie K714, Monheim am Rhein | Stadt Monheim | PRINZ.de Düsseldorf
--   2026-11-06 | Sputnikhalle Münster | Sputnikhalle Münster, Munster | Stadt Münster | PRINZ.de Düsseldorf
--   2026-10-31 | Neanderthal Museum |  | auswärtiger Ort | Rausgegangen
--   2026-11-06 | Cabaret Queue | Cabaret Queue, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-06 | BürgerTreff | BürgerTreff, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-11-06 | Kulturrampe | Kulturrampe, Krefeld | Stadt Krefeld | PRINZ.de Düsseldorf
--   2026-11-06 | FZW Dortmund | FZW Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-04-02 | ✅ Global Language Practice | Köln (Online) |  | Stadt Köln | Meetup.com
--   2026-04-18 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-06 | Kulturraffinerie K714 | Kulturraffinerie K714, Monheim am Rhein | Stadt Monheim | PRINZ.de Düsseldorf
--   2026-11-06 | Walder Stadtsaal | Walder Stadtsaal, Solingen | Stadt Solingen | PRINZ.de Düsseldorf
--   2026-11-06 | Steinbruch Duisburg | Steinbruch Duisburg | Stadt Duisburg | PRINZ.de Düsseldorf
--   2026-11-06 | Steinhof Duisburg-Huckingen | Steinhof Duisburg-Huckingen | Stadt Duisburg | PRINZ.de Düsseldorf
--   2026-11-06 | Kulturfabrik Krefeld | Kulturfabrik Krefeld | Stadt Krefeld | PRINZ.de Düsseldorf
--   2026-12-11 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-06 | Kulturfabrik Krefeld | Kulturfabrik Krefeld | Stadt Krefeld | PRINZ.de Düsseldorf
--   2026-11-06 | Live Club Barmen | Live Club Barmen, Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-11-06 | Kulturzentrum Immanuel | Kulturzentrum Immanuel, Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-11-06 | Kulturraffinerie K714 | Kulturraffinerie K714, Monheim am Rhein | Stadt Monheim | PRINZ.de Düsseldorf
--   2026-11-06 | Ev. Kirche am Markt Katernberg | Ev. Kirche am Markt Katernberg, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-10-31 | Theater Krefeld | Theater Krefeld | Stadt Krefeld | PRINZ.de Düsseldorf
--   2026-11-06 | Cabaret Queue | Cabaret Queue, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-06 | Cafe Lieber | Cafe Lieber, Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-11-06 | INSEL | INSEL, Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-11-06 | Kulturraffinerie K714 | Kulturraffinerie K714, Monheim am Rhein | Stadt Monheim | PRINZ.de Düsseldorf
--   2026-04-10 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-04-11 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-17 | Theater Duisburg – Opernfoyer | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-06 | KJT Dortmund in der Sckellstraße | KJT Dortmund in der Sckellstraße | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-08 | oehme brot und kuchen | düsseldorferstr.81-85 meetup162 meerbusch | Stadt meerbusch | Meetup.com
--   2026-11-03 | Parkplatz A3/A4 | Parkplatz A3/A4, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-10-31 | Opernhaus Dortmund | Opernhaus Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-12-31 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-29 | Theater Duisburg – Opernfoyer | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-05 | Kokerei Zollverein | Kokerei Zollverein, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-11-05 | KJT Dortmund in der Sckellstraße | KJT Dortmund in der Sckellstraße | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-05 | Theater Duisburg Bühne | Theater Duisburg Bühne | Stadt Duisburg | PRINZ.de Düsseldorf
--   2026-11-05 | Südbahnhof | Südbahnhof, Krefeld | Stadt Krefeld | PRINZ.de Düsseldorf
--   2026-11-05 | Treffpunkt: | Treffpunkt:, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-05 | Teo Otto Theater der Stadt Remscheid | Teo Otto Theater der Stadt Remscheid | Stadt Remscheid | PRINZ.de Düsseldorf
--   2026-11-05 | Cabaret Queue | Cabaret Queue, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-05 | Kulturfabrik Krefeld | Kulturfabrik Krefeld | Stadt Krefeld | PRINZ.de Düsseldorf
--   2026-11-05 | Museum der Niederrheinischen Seele, Villa Erckens | Museum der Niederrheinischen Seele, Villa Erckens, | Stadt Grevenbroich | PRINZ.de Düsseldorf
--   2026-11-05 | Hansa Theater Hörde | Hansa Theater Hörde, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-05 | literaturhaus.dortmund | literaturhaus.dortmund | Stadt dortmund | PRINZ.de Düsseldorf
--   2026-11-05 | Kulturfabrik Krefeld | Kulturfabrik Krefeld | Stadt Krefeld | PRINZ.de Düsseldorf
--   2026-11-05 | Schul- und Stadtteilbibliothek Gesamtschule Süd | Schul- und Stadtteilbibliothek Gesamtschule Süd, D | Stadt Duisburg | PRINZ.de Düsseldorf
--   2026-11-05 | Die Börse | Die Börse, Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2027-01-03 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-05 | Talton Theater | Talton Theater, Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-11-06 | Opernhaus Dortmund | Opernhaus Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-05 | Kulturraffinerie K714 | Kulturraffinerie K714, Monheim am Rhein | Stadt Monheim | PRINZ.de Düsseldorf
--   2026-11-05 | Szene 10 | Szene 10, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-11-06 | Theater Krefeld | Theater Krefeld | Stadt Krefeld | PRINZ.de Düsseldorf
--   2026-11-05 | WüRG Haus | WüRG Haus, Wülfrath | Stadt Wülfrath | PRINZ.de Düsseldorf
--   2026-11-05 | FZW | FZW, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-06 | AWO ( DorfWein Location ) | AWO ( DorfWein Location ), Duisburg | Stadt Duisburg | PRINZ.de Düsseldorf
--   2026-11-05 | Zentralbibliothek im Stadtfenster | Zentralbibliothek im Stadtfenster, Duisburg | Stadt Duisburg | PRINZ.de Düsseldorf
--   2026-11-05 | Werkhof Kulturzentrum Hagen - Hohenlimburg | Werkhof Kulturzentrum Hagen - Hohenlimburg | Stadt Hagen | PRINZ.de Düsseldorf
--   2026-11-06 | KONGRESS- und EVENTPARK Stadthalle Hagen GmbH | KONGRESS- und EVENTPARK Stadthalle Hagen GmbH | Stadt Hagen | PRINZ.de Düsseldorf
--   2026-11-06 | Albert-Einstein-Forum | Albert-Einstein-Forum, Kaarst | Stadt Kaarst | PRINZ.de Düsseldorf
--   2026-04-10 | Online language evening "Gelsenkirchen and worldwide" (Onlin |  | Stadt Gelsenkirchen | Meetup.com
--   2026-10-30 | Online language evening "Gelsenkirchen and worldwide" (Onlin |  | Stadt Gelsenkirchen | Meetup.com
--   2026-11-06 | Jugendzentrum Juzo | Jugendzentrum Juzo, Duisburg | Stadt Duisburg | PRINZ.de Düsseldorf
--   2026-11-06 | Hansa Theater Hörde | Hansa Theater Hörde, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-06 | domicil | domicil, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-06 | Szene 10 | Szene 10, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-11-06 | Visiodrom im Gaskessel Wuppertal | Visiodrom im Gaskessel Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-11-06 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-11-06 | Kulturzentrum GREND | Kulturzentrum GREND, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-11-06 | Altes Hafenamt | Altes Hafenamt, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-06 | FZW | FZW, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-06 | Musik Werkstatt Hörde | Musik Werkstatt Hörde, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-06 | Museum Tuppenhof | Museum Tuppenhof, Kaarst | Stadt Kaarst | PRINZ.de Düsseldorf
--   2026-11-06 | Theater Mönchengladbach | Theater Mönchengladbach | Stadt Mönchengladbach | PRINZ.de Düsseldorf
--   2026-11-06 | PROJEKT 42 | PROJEKT 42, Mönchengladbach | Stadt Mönchengladbach | PRINZ.de Düsseldorf
--   2026-11-06 | Kokerei Zollverein | Kokerei Zollverein, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-11-06 | Online language evening "Gelsenkirchen and worldwide" (Onlin |  | Stadt Gelsenkirchen | Meetup.com
--   2026-04-04 | Schloss Dyck |  | auswärtiger Ort | Rausgegangen
--   2026-04-12 | Neanderthal Museum |  | auswärtiger Ort | Rausgegangen
--   2026-04-06 | Café Aroma | Dorfstraße 34, meetup162 Meerbusch | Stadt Meerbusch | Meetup.com
--   2026-04-08 | ✅ Global Language Practice | Köln (Online) |  | Stadt Köln | Meetup.com
--   2026-04-13 | ✅ Global Language Practice | Köln (Online) |  | Stadt Köln | Meetup.com
--   2026-04-14 | MikroTik User Group Oberhausen (Online) |  | Stadt Oberhausen | Meetup.com
--   2026-04-06 | Meditation & Yoga lernen - Düsseldorf, Duisburg - Kostenfrei |  | Stadt Duisburg | Meetup.com
--   2026-04-05 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-04-11 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-10-29 | Frankenring 20 | Frankenring 20, 47798 Krefeld, Germany 47798 Krefe | PLZ 47798 | Meetup.com
--   2026-10-30 | Theater Duisburg – Opernfoyer | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-29 | Opernplatz, Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-05 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-09 | Theater Duisburg – Opernfoyer | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-12 | Kölner Straße 11 | Kölner Str. 11, 47805 Krefeld, Germany 47805 Krefe | PLZ 47805 | Meetup.com
--   2026-11-14 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2027-01-05 | Neanderthal Museum |  | auswärtiger Ort | Rausgegangen
--   2026-11-11 | Theater Duisburg, Ballettsaal | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-05 | Theater Krefeld | Theater Krefeld | Stadt Krefeld | PRINZ.de Düsseldorf
--   2026-11-01 | Schloss Dyck |  | auswärtiger Ort | Rausgegangen
--   2026-10-28 | Neanderthal Museum |  | auswärtiger Ort | Rausgegangen
--   2026-10-28 | Neanderthal Museum |  | auswärtiger Ort | Rausgegangen
--   2026-10-29 | Neanderthal Museum |  | auswärtiger Ort | Rausgegangen
--   2026-10-30 | Neanderthal Museum |  | auswärtiger Ort | Rausgegangen
--   2026-10-30 | Neanderthal Museum |  | auswärtiger Ort | Rausgegangen
--   2026-11-15 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-11-09 | FZW | FZW, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-15 | Opernhaus Wuppertal | Opernhaus Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-11-15 | Historische Stadthalle | Historische Stadthalle, Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-11-15 | Theater Fletch Bizzel Olpketal | Theater Fletch Bizzel Olpketal, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-28 | Schloss Dyck |  | auswärtiger Ort | Rausgegangen
--   2026-12-29 | Neanderthal Museum |  | auswärtiger Ort | Rausgegangen
--   2026-11-09 | SIGNAL IDUNA PARK | SIGNAL IDUNA PARK, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-10-28 | Opernhaus Dortmund (Operntreff) | Opernhaus Dortmund (Operntreff) | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-10-28 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-10-28 | KONGRESS- und EVENTPARK Stadthalle Hagen GmbH | KONGRESS- und EVENTPARK Stadthalle Hagen GmbH | Stadt Hagen | PRINZ.de Düsseldorf
--   2026-10-28 | Theater Krefeld | Theater Krefeld | Stadt Krefeld | PRINZ.de Düsseldorf
--   2026-10-28 | Enotria Ristorante und Winebar | Enotria Ristorante und Winebar, Hagen | Stadt Hagen | PRINZ.de Düsseldorf
--   2026-10-28 | Cabaret Queue | Cabaret Queue, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-10-28 | Historische Stadthalle | Historische Stadthalle, Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-11-15 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-10-28 | Sputnikhalle Münster | Sputnikhalle Münster, Munster | Stadt Münster | PRINZ.de Düsseldorf
--   2026-10-28 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-10-28 | Zeche Carl | Zeche Carl, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-10-28 | domicil | domicil, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-10-28 | Kulturfabrik Krefeld | Kulturfabrik Krefeld | Stadt Krefeld | PRINZ.de Düsseldorf
--   2026-10-28 | KONGRESS- und EVENTPARK Stadthalle Hagen GmbH | KONGRESS- und EVENTPARK Stadthalle Hagen GmbH | Stadt Hagen | PRINZ.de Düsseldorf
--   2026-10-28 | domicil | domicil, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-10-28 | Die Börse | Die Börse, Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-10-28 | Ebertbad Oberhausen | Ebertbad Oberhausen | Stadt Oberhausen | PRINZ.de Düsseldorf
--   2026-11-15 | Westfalenschenke | Westfalenschenke, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-10-28 | FZW | FZW, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-15 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-11-14 | Galerie für Zeitgenössische Kunst | Galerie für Zeitgenössische Kunst, Leipzig | Stadt Leipzig | PRINZ.de Düsseldorf
--   2026-11-15 | Theater Duisburg Bühne | Theater Duisburg Bühne | Stadt Duisburg | PRINZ.de Düsseldorf
--   2026-11-15 | Städtisches Bühnenhaus | Städtisches Bühnenhaus, Wesel | Stadt Wesel | PRINZ.de Düsseldorf
--   2026-11-15 | Hansa Theater Hörde | Hansa Theater Hörde, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-12-03 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-15 | Roto Theater | Roto Theater, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-15 | BürgerTreff | BürgerTreff, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-11-15 | Theater an der Niebuhrg | Theater an der Niebuhrg, Oberhausen | Stadt Oberhausen | PRINZ.de Düsseldorf
--   2026-11-13 | Online language evening "Gelsenkirchen and worldwide" (Onlin |  | Stadt Gelsenkirchen | Meetup.com
--   2026-11-15 | Szene 10 | Szene 10, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-11-15 | Opernhaus Dortmund | Opernhaus Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-15 | Teo Otto Theater der Stadt Remscheid | Teo Otto Theater der Stadt Remscheid | Stadt Remscheid | PRINZ.de Düsseldorf
--   2026-11-15 | Nonsense Bar | Nonsense Bar, Mönchengladbach | Stadt Mönchengladbach | PRINZ.de Düsseldorf
--   2026-11-06 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-15 | FZW Dortmund | FZW Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-15 | Marionettentheater Krieewelsche Pappköpp | Marionettentheater Krieewelsche Pappköpp, Krefeld | Stadt Krefeld | PRINZ.de Düsseldorf
--   2026-11-15 | FZW | FZW, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-15 | Theater Duisburg (Foyer) | Theater Duisburg (Foyer) | Stadt Duisburg | PRINZ.de Düsseldorf
--   2027-01-14 | Museum der bildenden Künste | Museum der bildenden Künste, Leipzig | Stadt Leipzig | PRINZ.de Düsseldorf
--   2027-01-14 | Galerie für Zeitgenössische Kunst | Galerie für Zeitgenössische Kunst, Leipzig | Stadt Leipzig | PRINZ.de Düsseldorf
--   2027-01-14 | Magicum - Berlin Magic Museum | Magicum - Berlin Magic Museum | Stadt Berlin | PRINZ.de Düsseldorf
--   2026-11-15 | Zeche Carl | Zeche Carl, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-11-15 | Kulturrampe | Kulturrampe, Krefeld | Stadt Krefeld | PRINZ.de Düsseldorf
--   2026-12-12 | Leipzig Zentrum | Leipzig Zentrum | Stadt Leipzig | PRINZ.de Düsseldorf
--   2026-12-12 | Galerie für Zeitgenössische Kunst | Galerie für Zeitgenössische Kunst, Leipzig | Stadt Leipzig | PRINZ.de Düsseldorf
--   2026-12-12 | IKONO Berlin | IKONO Berlin | Stadt Berlin | PRINZ.de Düsseldorf
--   2026-11-07 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2027-01-14 | Museum für Druckkunst | Museum für Druckkunst, Leipzig | Stadt Leipzig | PRINZ.de Düsseldorf
--   2027-01-14 | Kunstkraftwerk | Kunstkraftwerk, Leipzig | Stadt Leipzig | PRINZ.de Düsseldorf
--   2027-01-14 | Galerie für Zeitgenössische Kunst | Galerie für Zeitgenössische Kunst, Leipzig | Stadt Leipzig | PRINZ.de Düsseldorf
--   2026-12-12 | Theater Duisburg – Opernfoyer | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-12-12 | Hugendubel München Stachus | Hugendubel München Stachus | Stadt München | PRINZ.de Düsseldorf
--   2026-10-31 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-10-31 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-10-31 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-10-31 | Phoenix des Lumieres (Vorplatz) | Phoenix des Lumieres (Vorplatz), Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-10-31 | Alte Feuerwache Grevenbroich | Alte Feuerwache Grevenbroich | Stadt Grevenbroich | PRINZ.de Düsseldorf
--   2026-10-31 | Seelich | Seelich, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-10-31 | Rudolf Weber-ARENA | Rudolf Weber-ARENA, Oberhausen | Stadt Oberhausen | PRINZ.de Düsseldorf
--   2026-10-31 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-10-31 | Theater Duisburg Bühne | Theater Duisburg Bühne | Stadt Duisburg | PRINZ.de Düsseldorf
--   2026-10-31 | Theater am Engelsgarten | Theater am Engelsgarten, Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-10-31 | Szene 10 | Szene 10, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-11-05 | Opernhaus Dortmund (Opernfoyer) | Opernhaus Dortmund (Opernfoyer) | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-09 | Sputnikhalle Münster | Sputnikhalle Münster, Munster | Stadt Münster | PRINZ.de Düsseldorf
--   2026-11-14 | Leipzig Zentrum | Leipzig Zentrum | Stadt Leipzig | PRINZ.de Düsseldorf
--   2026-12-12 | Galerie für Zeitgenössische Kunst | Galerie für Zeitgenössische Kunst, Leipzig | Stadt Leipzig | PRINZ.de Düsseldorf
--   2026-11-09 | Historische Stadthalle | Historische Stadthalle, Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-04-02 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-04-12 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-10-29 | Herbrand's | Herbrand's, Köln | Stadt Köln | PRINZ.de Düsseldorf
--   2026-04-04 | ✅ Global Language Practice | Köln (Online) |  | Stadt Köln | Meetup.com
--   2026-04-07 | ✅ Global Language Practice | Köln (Online) |  | Stadt Köln | Meetup.com
--   2026-11-08 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-10-28 | Neanderthal Museum |  | auswärtiger Ort | Rausgegangen
--   2026-12-17 | Theater Duisburg – Opernfoyer | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-10-28 | OBEX | Oberhausen | OBEX | Oberhausen | Stadt Oberhausen | PRINZ.de Düsseldorf
--   2026-11-17 | Theater Duisburg – Opernfoyer | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-12 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-22 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-29 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-12-12 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-12-16 | Theater Duisburg – Opernfoyer | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-12-17 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-12-20 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-12-20 | Opernplatz, Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-19 | codecentric AG | Hochstraße 11 42697 Solingen | PLZ 42697 | Meetup.com
--   2026-11-15 | Großer Konzertsaal | Großer Konzertsaal, Solingen | Stadt Solingen | PRINZ.de Düsseldorf
--   2026-10-28 | Visiodrom im Gaskessel Wuppertal | Visiodrom im Gaskessel Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-11-15 | oehme brot und kuchen | düsseldorferstr.81-85 meetup162 meerbusch | Stadt meerbusch | Meetup.com
--   2026-04-02 | Mettmann |  | Stadt Mettmann | Kulturportal Düsseldorf
--   2026-11-14 | agra Messepark | agra Messepark, Leipzig | Stadt Leipzig | PRINZ.de Düsseldorf
--   2026-04-03 | ✅ Global Language Practice | Köln (Online) |  | Stadt Köln | Meetup.com
--   2026-11-14 | G2 Kunsthalle | G2 Kunsthalle, Leipzig | Stadt Leipzig | PRINZ.de Düsseldorf
--   2026-10-31 | Parkplatz A3/A4 | Parkplatz A3/A4, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-12 | Visiodrom im Gaskessel Wuppertal | Visiodrom im Gaskessel Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-11-14 | Wilhelm-Leuschner-Platz | Wilhelm-Leuschner-Platz, Leipzig | Stadt Leipzig | PRINZ.de Düsseldorf
--   2026-11-18 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-21 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-24 | Theater Duisburg – Opernfoyer | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-26 | Herbrand's | Herbrand's, Köln | Stadt Köln | PRINZ.de Düsseldorf
--   2026-12-02 | Theater Duisburg – Opernfoyer | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-19 | Kölner Straße 11 | Kölner Str. 11, 47805 Krefeld, Germany 47805 Krefe | PLZ 47805 | Meetup.com
--   2026-12-04 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-12-05 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-12-06 | Theater Duisburg – Opernfoyer | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-12-08 | Theater Duisburg – Opernfoyer | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-12-08 | Herbrand's | Herbrand's, Köln | Stadt Köln | PRINZ.de Düsseldorf
--   2026-12-16 | Theater Duisburg – Opernfoyer | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-12-18 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-12-19 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-12-22 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-12-23 | Theater Duisburg – Opernfoyer | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-12-30 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2027-01-02 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-20 | Online language evening "Gelsenkirchen and worldwide" (Onlin |  | Stadt Gelsenkirchen | Meetup.com
--   2026-11-12 | Kulturraffinerie K714 | Kulturraffinerie K714, Monheim am Rhein | Stadt Monheim | PRINZ.de Düsseldorf
--   2026-11-12 | Kulturraffinerie K714 | Kulturraffinerie K714, Monheim am Rhein | Stadt Monheim | PRINZ.de Düsseldorf
--   2026-11-12 | Mayersche Dortmund | Mayersche Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-12 | Centrum Westende - Kleinkunstbühne Meiderich | Centrum Westende - Kleinkunstbühne Meiderich, Duis | Stadt Duisburg | PRINZ.de Düsseldorf
--   2026-11-15 | Albert-Einstein-Forum | Albert-Einstein-Forum, Kaarst | Stadt Kaarst | PRINZ.de Düsseldorf
--   2026-11-15 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-11-12 | Fritz-Henßler-Haus | Fritz-Henßler-Haus, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-12 | Twenty Seven | Twenty Seven, Kaarst | Stadt Kaarst | PRINZ.de Düsseldorf
--   2026-11-12 | Parkplatz A3/A4 | Parkplatz A3/A4, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-12 | domicil | domicil, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-15 | Visiodrom im Gaskessel Wuppertal | Visiodrom im Gaskessel Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-11-12 | Theater Mönchengladbach - Theaterbar | Theater Mönchengladbach - Theaterbar | Stadt Mönchengladbach | PRINZ.de Düsseldorf
--   2026-11-15 | Theater Krefeld | Theater Krefeld | Stadt Krefeld | PRINZ.de Düsseldorf
--   2026-11-06 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-11-15 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-11-15 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-10-31 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-11-15 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-11-12 | Rudolf Weber-ARENA | Rudolf Weber-ARENA, Oberhausen | Stadt Oberhausen | PRINZ.de Düsseldorf
--   2027-01-09 | Theater Duisburg | Heinrich-Heine-Allee 16a, 40213 Düsseldorf | Stadt Duisburg | Deutsche Oper am Rhein
--   2026-11-14 | Galerie für Zeitgenössische Kunst | Galerie für Zeitgenössische Kunst, Leipzig | Stadt Leipzig | PRINZ.de Düsseldorf
--   2026-12-12 | Galerie für Zeitgenössische Kunst | Galerie für Zeitgenössische Kunst, Leipzig | Stadt Leipzig | PRINZ.de Düsseldorf
--   2027-01-14 | Galerie für Zeitgenössische Kunst | Galerie für Zeitgenössische Kunst, Leipzig | Stadt Leipzig | PRINZ.de Düsseldorf
--   2026-11-12 | Szene 10 | Szene 10, Essen | Stadt Essen | PRINZ.de Düsseldorf
--   2026-10-31 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-10-28 | Planetarium Erkrath | Planetarium Erkrath | Stadt Erkrath | PRINZ.de Düsseldorf
--   2026-11-15 | Ebertbad Oberhausen | Ebertbad Oberhausen | Stadt Oberhausen | PRINZ.de Düsseldorf
--   2026-11-14 | Galerie für Zeitgenössische Kunst | Galerie für Zeitgenössische Kunst, Leipzig | Stadt Leipzig | PRINZ.de Düsseldorf
--   2026-11-15 | Fritz-Henßler-Haus | Fritz-Henßler-Haus, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-15 | Mercatorhalle Duisburg im CityPalais | Mercatorhalle Duisburg im CityPalais | Stadt Duisburg | PRINZ.de Düsseldorf
--   2026-11-15 | Treffpunkt: | Treffpunkt:, Dortmund | Stadt Dortmund | PRINZ.de Düsseldorf
--   2026-11-15 | Talton Theater | Talton Theater, Wuppertal | Stadt Wuppertal | PRINZ.de Düsseldorf
--   2026-11-15 | Ruhr-Beef auf dem Bauernhof Maaßen | Ruhr-Beef auf dem Bauernhof Maaßen, Bottrop | Stadt Bottrop | PRINZ.de Düsseldorf
--   2026-11-15 | Theater Mönchengladbach - Konzertsaal | Theater Mönchengladbach - Konzertsaal | Stadt Mönchengladbach | PRINZ.de Düsseldorf
--   2026-11-15 | Lukaskirche Kaarst-Holzbüttgen | Lukaskirche Kaarst-Holzbüttgen | Stadt Kaarst | PRINZ.de Düsseldorf
--   2027-01-14 | GRASSI Museum für Angewandte Kunst | GRASSI Museum für Angewandte Kunst, Leipzig | Stadt Leipzig | PRINZ.de Düsseldorf

BEGIN;

DELETE FROM public.events WHERE id IN (
    'fdfe7520-0139-49cb-89d8-13f7b1d6e178',
    '598d9676-774b-4613-a073-37d12cabbc3d',
    '48518e0e-0d4d-41b2-bdaa-87ee6e8af545',
    '924240a2-0dcc-43f3-bb9c-e449e4b58619',
    '8792bd3c-bf0c-42a5-9593-7749053c0434',
    '80d5391f-f0a4-455c-8a2d-33318d8c3cd3',
    'cbc72dd7-34bd-4fb8-b16f-487b8da21901',
    'f805ff65-2e58-4f24-8067-009dcc745914',
    '4dc5d7fe-41ce-42fb-a36c-fa00c3034de6',
    '3a802453-0bd3-4fd1-9ded-bda5df95efea',
    '699fe378-2e11-4eef-a4e3-1c62b66b863d',
    'b8ee3043-e4ff-40fe-a05a-d4b748146364',
    '9ad9dd4f-9d58-4591-a41f-0e6ba1cd5918',
    '2bb3922b-2ebf-4d94-a4cb-c954b7d2c96a',
    'd9c4d879-5873-4a16-9c9f-049e11b2b7c0',
    '0b3b6d2c-0b77-40b4-9d97-9dbf087e4ed9',
    'da0bbde7-a335-4059-a69e-85f75c2105ba',
    'cf32c586-2e03-445d-9a49-7299c1ad3605',
    'e108d7ad-69a4-47ad-a9a2-75c2743f9e59',
    'ee884f9c-46ab-4434-95a4-8c32cdcd1527',
    '75e5989e-99a7-47db-9784-02976c235ce0',
    'd08fe37f-ba42-456e-902f-945b38edf56c',
    '2fc1cfc4-fb36-4d88-9db9-6b41334df5d9',
    'ccfbf5be-1d29-43cb-90ad-7d34ced8c6bb',
    '3c618821-38ad-4df5-b77e-be418d13ae12',
    '6fd06474-87f8-4e51-8802-a7a2b7434848',
    '1f8934cb-a996-4b9d-ab7b-4e47df18a9a9',
    '958e474e-1ab5-46cf-8b73-f999d6990bb4',
    'afcb2adf-f698-435a-946a-78ea0187a456',
    '88d463b4-4e22-47e2-87cc-ea77525940fe',
    '475296e4-51a7-4235-b1f1-e62adf135ea5',
    '8b6111f2-ed84-4f90-aab8-85b34971d25d',
    '427f9871-e981-4f72-9aba-0346281cb745',
    'a5767c23-1022-408c-b366-c08d52523c5b',
    'b7b1cb48-0c9b-4a54-be72-7f3f568f6e93',
    'd1990b20-ecf7-4f15-a6c2-a5297dc52704',
    'ffd6de9f-61f8-4392-9bd9-5279cefb7bc7',
    'dc1de054-9f8a-4986-8500-f3077dde30b8',
    '34ba2e99-719b-4d81-b6d3-b32354f4fb67',
    'b4249d59-a00d-4274-b02e-13888965f5dd',
    'f912ab38-f860-41bd-849e-1bcb06fdefdb',
    '1cd96f73-9afe-4622-91ca-b2b9d68c0366',
    '88d6011a-a17a-484a-b0a8-39907ce131f6',
    'd91847d9-1967-4909-99f0-01d52a5e57c9',
    '92308b88-1d3b-49e8-9a23-63699ccdeda8',
    'cbc4b8eb-5aa3-4de1-abe9-cc199a0cbddf',
    'f2dfdc9f-e9cb-4eb6-b7d6-1d6a1c118e3e',
    '532f6784-f069-4f74-abf8-fd6289e09b22',
    'dafcd9fc-d55c-4400-af50-3a23bfe75b2f',
    '939bed39-8ccb-45c0-80c4-217a900bd0df',
    '9ade6613-830b-4076-b02d-cc8f77effc72',
    'f9164de5-2908-4d1c-b6ef-165e732e9306',
    '50eb2f99-12c2-4115-a919-ff4cbf4bb97e',
    '594ffe7f-6071-4d57-bb9f-bf30cc0dcd0e',
    '490721f8-a657-40e8-bcb7-72112af730c0',
    'acb419b9-4646-4716-8103-3d0f4815fe87',
    '298c3d4c-6441-4317-bd86-f162ef33f35a',
    '6ca27ee3-85c3-407f-bdf1-1a6fb54e430a',
    'a381f56f-7ce1-4772-a268-678a7c0b6959',
    '7ade5861-817e-495e-8d06-a8a082a5bb95',
    '8e8e0d2a-eaf5-475f-bebd-cef630c0ccbf',
    '4a9b0c7e-dc5f-4b60-9d7d-dcea9d23dc2f',
    '59e79bd7-e3b3-4674-aebc-df4df7ec2b5e',
    '22b1fa78-c5aa-4bc3-9e15-0a352f4956ef',
    '51facc2c-40af-4fda-a5d1-61c294d08fbb',
    '2878b67b-293d-4e54-b265-5e161570f58e',
    'dd2e0f61-615e-422b-876f-1dc56aa3a87f',
    '47496026-2b51-4b04-9532-4fb1bd423ef7',
    '17992ec9-5ec3-4ae3-9447-91b7802f5a2f',
    '7b9a2f93-4a95-4318-8190-c7c15c7be0fe',
    '14419f61-ee29-4a04-966a-f561e378bdb4',
    '019f36b9-0b55-4cef-a4eb-9faadcfd9173',
    '47487ba9-027a-4675-be64-3ccafb11e684',
    'e6d8f082-8a30-40d8-8c70-dce9bbf203fa',
    '87ca4b2a-a29b-4630-8b6a-26dc8e88bd37',
    'a43e0a53-250e-441b-8a6d-c27f61944c1b',
    '53583d68-bc96-4e21-ad10-a4e5be18b13f',
    '0b5f0aa5-a27d-4859-890f-09acc49407d6',
    '1b6099c3-e951-4bdc-9547-720fe376a3e1',
    'a51d17ae-69b2-49c7-87db-fd6e093f7186',
    'c920970a-2ec3-42f0-96c6-321e8e6d90aa',
    'b4e0070d-ce43-438b-babd-8709a78ae299',
    '674e6f07-6d4b-42b1-a5d1-2997bd11f02e',
    '8f9e88d5-6dee-476a-98cc-537f90a5eff3',
    '054eec4e-d373-4b4c-be16-89637906f1fe',
    '5c8e3c07-6e73-44fb-aee4-2fa09ae5c159',
    '5e157d14-488a-4cdd-88bd-45951913a3d1',
    '3deb5ff8-c3bc-4642-bb67-caef6ff001cd',
    'b4b25472-d9d4-4db3-bf91-aa1277a910a2',
    '3e1483f6-84d6-45b3-bfed-cba12984a03c',
    'f5969e22-591d-4a58-9a8d-feeef81c8077',
    '4d1e5c1f-b493-4b47-ba49-0ab9123d5726',
    'f6913dc9-006a-4bfd-8ca6-6b6146037281',
    '9ee1e864-c625-4429-bfbf-657d5b99cb7e',
    'b6548625-6e22-449e-82d7-4aaacc5389c2',
    'bb2a8424-2158-49a5-8928-0a2aca6231d5',
    '54add7d9-d656-4108-90a5-5175ebf83e81',
    'cbb6d87c-b944-450f-ab08-ad15fca56864',
    'b376ac0f-620c-4439-aa02-6707728b135e',
    '7f9f7f80-3373-44a0-a3ae-69cb771b842f',
    '3c750741-2af8-4230-a017-4b610bc8cd88',
    '671e9e3f-a6e4-4ff9-9bf2-c7f2a01130a7',
    'b9c92d5c-5224-4db3-a3eb-a33dd6c2e558',
    'e80367e5-b876-46d6-b269-e7e7c310fa2e',
    '819f0411-2aba-43e0-83cb-3c7cbd611124',
    'af2964f3-ced6-4f3e-a87c-1d6f01b24583',
    '05b4873f-d54d-47a2-be7d-3f3d0501b60f',
    '08d023c6-1df9-4dc7-9ce5-6ac342c73228',
    '6a110689-3c3e-4bd1-a0dd-c66fc2d4eef3',
    'f3eeed57-9842-42f8-b729-a393fc630d60',
    '8659a448-7dd2-4a49-9b75-a29210e4f500',
    'b3c436c9-722d-447c-a077-4dc29ab22db7',
    '0256f238-5e0c-4aa5-9d70-3d12998f75ed',
    '1280eaff-2874-4224-9984-c88ef3bef837',
    '244213b4-e4ee-4122-a829-711198deb62b',
    '63f43707-578c-4b93-9d3e-5f8ea6c5c6f8',
    '2ae12a91-1034-4fd6-8063-b5ae8227d3e2',
    '864ef45a-234e-4614-99ef-5934a6efd54a',
    '3e16de25-a606-4178-8dee-88fa68ee0f7e',
    '08a3e59f-df41-428a-9893-122b387832d3',
    '5a710a42-d465-40df-af2d-5049f637e9c6',
    'e51fea8f-a850-4006-94f9-86debd282776',
    '4dd23cef-f0c9-40c4-955b-44f655bf2efa',
    'c33ff4c0-bc64-4b9b-9af4-75f194aefcce',
    '98484366-b821-4da5-8496-95ac6a30c657',
    'ad73929e-759f-482c-ba9d-bb9383bea3fc',
    'd6304b63-eb2b-4ab8-858c-94f53a3a8c18',
    '554c9d4c-fed8-4254-8e1d-7c4bdba5e523',
    '42a40cf7-5f62-48c5-8e15-5294f860fe1d',
    '0a9fb239-825e-425c-a84f-1b6f32675b16',
    '7e4c7c70-bb74-4d55-92da-093a89cd3686',
    '32a1578b-4bd7-499f-bda6-2ef134ed3341',
    '2c2511cf-2677-484b-8a0d-80db0b5a005c',
    'b2c32ceb-2e5e-432d-a71b-6525eb576c74',
    'c7cfd957-73d2-42e4-aa2e-db68e049c12d',
    'df0540a6-bdd4-4902-946e-6afc9a1606ad',
    '38736bbd-0c02-401c-a0ae-f758a98a4f48',
    '01893f7f-7982-4c31-b377-f8bac5ef154f',
    'e35c75ed-a7bc-429e-a0f5-3d0e0ced6899',
    'bce9f3ba-d559-4c3b-9062-521065fe05e9',
    '120974a7-6800-4b89-94f1-1ed414ea563a',
    '416032ed-470b-4e10-8be1-1da0508ff6b2',
    '225f410e-79e5-4e9c-a85c-a55e589cc57f',
    '6fa03d1d-e641-4912-8d9b-562632add531',
    'c76efa7d-4eee-4a11-8402-5d49934927c8',
    '4448e56f-8cbf-4498-a18e-3cee360de1d7',
    '0fe386b6-a002-4a62-ba18-7efeaf1ec6ec',
    '574d6adb-0854-419f-bc71-72d9a78334d2',
    '8462159a-3a96-40ea-a393-9d0bb3515176',
    'cbe2eeac-92a2-4a02-87cb-6ae8dcbdafc6',
    'dc28be34-1382-4368-9973-07f024976e85',
    '5c3df6fd-cbbe-41f1-85ad-a9b09004a9e6',
    '12dc3406-c869-41b4-b503-b6afe1be8add',
    '16dd7537-0e0b-47b3-acd7-b4035de34427',
    '4e0ee8d4-91be-474e-a035-3daf91c8d124',
    '16d77aa4-874f-4023-91d7-1d182fcb4b45',
    '4dd9165d-871f-4bb7-bb94-124ee077fec5',
    'a42769a0-9dd0-464b-898e-48e9089d2835',
    '935d7eca-9e28-4902-9637-e94762ecd3b5',
    '919c2e07-8c89-48d1-977f-5a2780fdc0e6',
    '446876db-3eff-44db-ac7b-8d8aede775dd',
    'd2019904-b696-40cb-b423-5d2c9feeb191',
    '07c0c327-8ba1-4d04-97df-67beef36e471',
    '919c7d11-8c47-4cd6-b6e2-21f677722172',
    'ffcf8ba6-5c4b-4ff0-b7cb-8af7f81aba43',
    'cc6b3717-8c42-4db5-818b-aceec22817b0',
    '4157acc6-cbbd-41d0-b7fe-5a2371180b0d',
    '163a0ec2-f125-4fdc-9435-3139c56d2341',
    '0b5a3eb2-795c-4fdf-aa57-edde6cf7c3ce',
    '4d8a099c-8e45-4601-861d-1b7e8444ec5e',
    '1413245a-c473-4568-a047-7a4d6e98ccc1',
    'f937af01-de36-49d4-a7fc-f5c695d10070',
    '10e5fcb5-e3c5-408d-8894-85befddd1794',
    '575de92b-1cec-4821-a7b4-baf7715c6a99',
    'e069f790-c487-48dc-8fdb-2de39160e71b',
    '1ec2b122-1b66-402a-9295-0283f1714959',
    '4d35d455-f203-4312-8d9c-3b4642fb5495',
    '8516b0ae-b660-4592-bfca-f79fdeabefc3',
    '5af17a83-ca38-441e-bade-b1932d1ff851',
    'c5254358-0d56-49b1-a398-556ddb26b3c9',
    '313cae15-f2b6-4e46-9d44-18d6f45f5ff7',
    '8c507067-472d-411a-85e2-0a7cd601cc80',
    '7cbf3ba5-3d08-4be1-b76e-c97e43138017',
    'ab81c106-718e-41f6-8a42-71767f07e9ba',
    'ee52ac4a-16ac-414a-967f-2c1470bbb868',
    'df640e38-4b41-41d5-8ed7-c18095446504',
    'dd1aaca0-d5f2-4576-bcde-ed345cb50bde',
    'd5b57e40-accd-4f70-91f0-c914f50720dd',
    '61dff0e4-6159-47e1-b2b5-65dba1a40d91',
    'a74213c7-f4c6-4b2f-8aec-7e7e4430fb21',
    '12b8325f-f86a-4e86-ae28-324b10168b9b',
    '04130758-4d53-43e1-b223-3fddc24723b7',
    '46189c0e-bd28-40f1-8cc1-9f70816210b9',
    '9d3fe867-7dac-46f5-8b6f-2e0f6937ad90',
    '751854b1-aec8-4231-b582-2aad8975fc9a',
    '25efacb8-c9b8-4fe1-9ded-90e2d64e16d9',
    '17f017b3-c7dc-476f-b231-161dd93dd8e1',
    'fbde95f0-e2de-4f03-b717-3657f26d7ad4',
    '938702fe-4431-4338-a514-73377f56118d',
    'b4fe7858-f9fd-43e2-bccf-42a98cc041f0',
    '706a687d-8085-46ae-be2d-30b75cf67da8',
    'b8e681fd-32dd-436a-950b-bffc4be10d30',
    'ba09ee76-fb8c-4ae7-87a9-c417755745b5',
    'e6e483de-8177-4df7-8e2b-0592d053a244',
    'f85e8bf5-cb9d-4313-9c5d-086d3d71745f',
    'd2208010-dcc3-4081-ae4b-ec3a36fb1639',
    '7c28eac3-d81b-4c3c-85bc-259cd6d4605d',
    'cafe7a32-5fce-4692-ad6d-35ae18d3c90a',
    '14a08de0-5c32-4e76-94ca-9f796f8335de',
    '67ebaa1a-bf19-462e-a613-067fbf28a89a',
    '986afcff-2688-4933-80f8-88369f5bc3c1',
    'cfdacc50-e074-428c-ac2a-8e3d659ebb32',
    '9e27eaad-eb5b-4382-a420-34be41263aed',
    '8f30c2bd-16c1-43e4-b696-f09a4dbecbb5',
    '1effa924-9577-48f1-9a69-5079d73306f2',
    '9e6b7840-1b5a-4467-b305-aeed5bf8dcda',
    'fdc21f65-b132-483f-a133-9e5fdbc8545f',
    'c951a0c1-6ccb-40e0-bfa9-57c825ccce6f',
    '9dc2183e-7ec9-41cb-84c9-8f0774646f3d',
    '943860d6-d5a8-4979-99d3-472370ef7687',
    'd3e3d7a8-4b9a-432a-981f-f23a23336d24',
    '0ddcad9c-d075-452f-b06c-241b246625ed',
    'a3c9e9e2-504d-470a-9b89-ba1207af6751',
    '2fbbae2c-b5e1-4956-87db-8df380757a62',
    'b01e50ec-08ac-48df-b205-768e9e3369c8',
    '62455cae-1659-48d3-98ae-f54d0771ea19',
    'c23145e4-b90c-4c1a-9b7f-0cb5af04ba4c',
    'd6b4309a-6d07-4fa6-b0fb-0413aaf4591c',
    '97fa706f-82e8-4fcf-9041-49db5f975dc5',
    'c2d53d97-8e02-4a4a-8e54-9b00126830a4',
    '04f639f7-e173-462f-a083-41b627252f2b',
    '15d96ec9-87c9-431c-88ef-20ff6ddcb8ba',
    '1e2a434f-965c-4dcb-9522-37bf6a0adede',
    '967eb9b1-36c7-4243-9992-d9559099d849',
    '09a409d4-8812-4d47-8614-f33080cb9c7e',
    'f43ef79e-b38c-4d7b-b20f-6282b76fcf47',
    'e65e6614-4b73-4bee-893b-eb10a189314f',
    'c02fbb60-f280-4ce5-9957-bffc488e939f',
    '43245bed-7a8c-4597-8636-ccdcdba122bd',
    'c78a3da1-dcfe-4f1d-92f1-d5fc5d5fdb00',
    '800b6de3-8b41-46b1-8f14-3a97946821ea',
    '3f7665f9-2865-45cc-a5ea-2ba8853e49a8',
    'a4cb2b33-f91e-43d7-9248-45a24aa0e202',
    '8c91e775-53da-4d51-9cc6-d319d9c63f3c',
    '6b74fd75-7a81-4f09-bdf1-d6daf25bea0f',
    '124ed401-0a6a-4026-a86c-205beba83dec',
    '9d0465b2-10ca-4ffa-b52a-69db5d792cd8',
    'da4534f4-e60a-410a-805f-71648f477464',
    '399a88f1-77e1-4dc2-8592-bbd71b0b1de8',
    '507f39b8-cf29-4597-b3a7-57cdb543c613',
    'f9ab95db-160d-4187-86c6-07e4ca0b0459',
    '5bc830e6-5eca-4720-a7e2-565cbed9116e',
    'b0d590af-859f-40d4-b164-f7a5d920b5b0',
    'e94793b9-ba5e-4870-aa11-00d1e73c677b',
    '210abb22-6ae5-4f14-8d57-3524a150299a',
    'd6e403a8-b2b5-4b03-924f-44abffaeff3e',
    '2f0c37d5-ee08-4e08-adc9-88e4c59cb950',
    '740c900b-fabd-4fda-8b76-38da0d9c99fc',
    '6bbfe4dc-441b-402c-96ea-74d380e2cb30',
    'd2b44c10-a050-478a-a20e-b9a7e06f4d49',
    'aac0de97-2006-405d-812e-41f201c9f98e',
    '4efd09ef-8f96-447b-bacc-266cd00699aa',
    '532e522a-024c-4635-a1a2-acb05c9a67e5',
    '74199668-3dc7-4ea1-8463-5a328ecff780',
    '083ae932-b0ef-4f96-88cb-4a8ef073ee50',
    '90cdab47-c73c-4083-9db5-f16e8153b15f',
    '10c7302b-f34f-4584-b131-ebf375c19fb5',
    '721ec3f7-3edc-45fc-aee0-86090fe75b34',
    '57d1bb3b-5f09-4e2e-8543-3682d5205676',
    'cae51a85-2401-4ce6-af03-22717fbc352d',
    'a132a79d-8518-4883-91c4-ed3f52e4e080',
    '1e726c53-0235-4590-acc5-35e7c508da49',
    'c1cdbba6-a8f9-4f52-a256-a5a853e7a1cd',
    '28aaeb8f-e347-44bb-b0d0-849425e336d1',
    '678b1cc2-e2d5-46b7-a43e-b7888f6628c5',
    '52d99aea-7296-44ae-8507-6dc938cc6ecc',
    '970d5a56-3692-4d57-ab2b-7b20d9ff2a38',
    '8194430b-b9cc-49eb-839d-6b4c03748514',
    'bf803958-69a5-425e-85ad-c8ab4fbbd45e',
    '5e0996c3-a44a-488b-9252-0ddcacda198d',
    '70536629-5692-42ee-afe0-fb29d2eecb78',
    '15836d15-e4d2-4d3c-8d43-16577149fbf1',
    '72571bfc-49cb-4b6b-8aa5-f53f93886b06',
    '79788201-c74a-4aa0-a566-3e1d93f2676b',
    '122935d1-7e90-4216-bec7-da502a8c6aac',
    '3e52c745-c302-4ce6-81a7-6da24bab918b',
    '284aa5d3-5824-4626-8c06-0276f168b0f4',
    '9fc32409-86c9-4508-9efa-b092fb936a0d',
    '4602eb9d-eff1-47a0-9ed5-afc112b2543d',
    '6fc4fdc7-fc16-419f-8b56-7e83e34cc97c',
    'f0b75c25-036e-47f3-8c2e-10ad730e027b',
    '4dbed81c-090d-4655-820d-a0b6dc49d85e',
    'd738a953-ea8e-42ea-b684-c9081401c665',
    'aa2e9fcd-a269-4f7e-9b39-78aba342e0fc',
    '209c1468-f5a2-47cd-9f96-d8e1df5a66e3',
    '6325a612-0f22-43c4-ade4-414a546ea630',
    'ac32e3ef-8cd8-4622-9fbc-a554546800f4',
    '27679e44-c2da-4db6-8353-3dcd7cf3547e',
    '9c6f3a17-a9b5-44a4-9411-37912fc35fcf',
    'bfe200e6-4a74-4089-9756-0dbbafb5fbd6',
    '51f159f4-5edd-4176-b0f3-d47a82d25286',
    'd2d3112d-923b-450b-b381-7abb84a182ce',
    '86ea3110-e76d-43ba-939b-a3cea9a8819b',
    '457ab8ce-844f-4a00-ac43-aa5e57adca2c',
    '416d9d85-7c3b-4b53-b8f6-b92295044811',
    '26af3035-b154-4834-9ba8-96613926c93b',
    'f3e8201d-93f7-412a-ae30-a3efa33f25a8',
    '2549bbd7-0a79-4384-bd65-c4e09657c471',
    '39cccbaa-90b7-45ec-a0be-200a3df7c2a7',
    'd4913f9d-002e-4a56-90af-5ed06a46da54',
    '3a66febd-a214-45c7-baa7-a371a255a8f0',
    'bcb14236-385c-4c47-8da4-212ae0092a51',
    'f4bfac68-11c2-4049-89dc-47517ddba6e3',
    '89c8af2c-07d9-4381-a13f-e6ccb55bda6b',
    '07e3b1b0-dac5-4cd5-a9ef-e3a6bb7efb44',
    'e0306456-59d6-4d0a-81d3-a8c964fed980',
    '850c6ba0-81ab-41e4-b5d8-6f2796b38e94',
    'ee22d5c7-c2a6-44fb-89f2-f1ca1a1356ae',
    'd45d88f4-17b1-40ff-8e3b-18d63ca7f2bb',
    '208ef0b8-3164-4474-bf22-794cdaede4cf',
    '672783de-9556-49d8-b3ac-83bd96954e10',
    '80c9c395-1382-4ae1-b4b8-a28ed2a6489e',
    '6bf146a1-74d9-4fec-81d8-3ecd5c6894a0',
    '6726500d-8f9b-4445-b789-b2158666a05a',
    '0d35deb1-7f86-41c3-a9cc-eb140a31e75b',
    '13e37e90-98ce-4609-bef2-3f6d60eda5e2',
    '67f0aa7d-5191-4b29-9e58-7cf48ad6ac5d',
    '51f16652-dbc5-4b20-8683-b88ed3602ce5',
    'bb4d51a8-65dc-4047-b206-8e4cffcbc498',
    '0c98a23f-6f93-48c8-b76a-538acdab8999',
    '52c122a6-a260-4126-8574-1f52f62d4460',
    'eb60f47f-26c1-472c-8824-fd954d45d7ea',
    '31b3e47d-168a-4b10-89ad-49b0e6ecb8dd',
    'de775359-e6c5-4338-b26a-79daf155fbde',
    '71d5865c-1db4-4ca1-b3aa-0469244c588e',
    '95ec02ce-7872-4e43-ae7c-e67826991cf8',
    'a5f4f8ba-f810-49f3-a0aa-b8c7942995df',
    'bf7c8d65-42c3-4478-ae8f-a96ee723e775',
    'd9fc05b5-e6c1-4a7d-a9ea-4c01d4394c2d',
    'e741d998-953d-40c5-9255-9489077de3af',
    '94e9cbad-1827-4390-af47-eee2aeeabf52',
    '33ef5b20-cfa8-4681-aa2f-2a0a71f318f6',
    '53034cfc-3adf-4007-bf56-668cde0151e8',
    'fb06c370-3947-4b7b-b7f4-f6c7351c1049',
    '992cce30-8642-41fb-921a-72550ae68abe',
    'fb9eac04-58fc-4ec0-a3ff-99818babfad1',
    '8afb8680-be17-4f8e-917e-75ae2af7970a',
    'cda44a88-65d9-4cfe-82e5-bbf7a510b7d6'
);

COMMIT;

-- Kontrolle: Zahl der gelöschten Events steht oben; danach sollte diese Abfrage 0 ergeben
SELECT count(*) AS noch_da FROM public.events WHERE id IN ('fdfe7520-0139-49cb-89d8-13f7b1d6e178', '598d9676-774b-4613-a073-37d12cabbc3d', '48518e0e-0d4d-41b2-bdaa-87ee6e8af545', '924240a2-0dcc-43f3-bb9c-e449e4b58619', '8792bd3c-bf0c-42a5-9593-7749053c0434', '80d5391f-f0a4-455c-8a2d-33318d8c3cd3', 'cbc72dd7-34bd-4fb8-b16f-487b8da21901', 'f805ff65-2e58-4f24-8067-009dcc745914', '4dc5d7fe-41ce-42fb-a36c-fa00c3034de6', '3a802453-0bd3-4fd1-9ded-bda5df95efea', '699fe378-2e11-4eef-a4e3-1c62b66b863d', 'b8ee3043-e4ff-40fe-a05a-d4b748146364', '9ad9dd4f-9d58-4591-a41f-0e6ba1cd5918', '2bb3922b-2ebf-4d94-a4cb-c954b7d2c96a', 'd9c4d879-5873-4a16-9c9f-049e11b2b7c0', '0b3b6d2c-0b77-40b4-9d97-9dbf087e4ed9', 'da0bbde7-a335-4059-a69e-85f75c2105ba', 'cf32c586-2e03-445d-9a49-7299c1ad3605', 'e108d7ad-69a4-47ad-a9a2-75c2743f9e59', 'ee884f9c-46ab-4434-95a4-8c32cdcd1527', '75e5989e-99a7-47db-9784-02976c235ce0', 'd08fe37f-ba42-456e-902f-945b38edf56c', '2fc1cfc4-fb36-4d88-9db9-6b41334df5d9', 'ccfbf5be-1d29-43cb-90ad-7d34ced8c6bb', '3c618821-38ad-4df5-b77e-be418d13ae12', '6fd06474-87f8-4e51-8802-a7a2b7434848', '1f8934cb-a996-4b9d-ab7b-4e47df18a9a9', '958e474e-1ab5-46cf-8b73-f999d6990bb4', 'afcb2adf-f698-435a-946a-78ea0187a456', '88d463b4-4e22-47e2-87cc-ea77525940fe', '475296e4-51a7-4235-b1f1-e62adf135ea5', '8b6111f2-ed84-4f90-aab8-85b34971d25d', '427f9871-e981-4f72-9aba-0346281cb745', 'a5767c23-1022-408c-b366-c08d52523c5b', 'b7b1cb48-0c9b-4a54-be72-7f3f568f6e93', 'd1990b20-ecf7-4f15-a6c2-a5297dc52704', 'ffd6de9f-61f8-4392-9bd9-5279cefb7bc7', 'dc1de054-9f8a-4986-8500-f3077dde30b8', '34ba2e99-719b-4d81-b6d3-b32354f4fb67', 'b4249d59-a00d-4274-b02e-13888965f5dd', 'f912ab38-f860-41bd-849e-1bcb06fdefdb', '1cd96f73-9afe-4622-91ca-b2b9d68c0366', '88d6011a-a17a-484a-b0a8-39907ce131f6', 'd91847d9-1967-4909-99f0-01d52a5e57c9', '92308b88-1d3b-49e8-9a23-63699ccdeda8', 'cbc4b8eb-5aa3-4de1-abe9-cc199a0cbddf', 'f2dfdc9f-e9cb-4eb6-b7d6-1d6a1c118e3e', '532f6784-f069-4f74-abf8-fd6289e09b22', 'dafcd9fc-d55c-4400-af50-3a23bfe75b2f', '939bed39-8ccb-45c0-80c4-217a900bd0df');
