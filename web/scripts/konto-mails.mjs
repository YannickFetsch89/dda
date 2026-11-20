// Baut die Mailvorlagen für Supabase Auth (Plan Nutzerkonten 10.3) im dies.das-Design.
// Aufruf (im Ordner web): node scripts/konto-mails.mjs
// Ergebnis: docs/konto-mails/<nr>-<name>.html (zum Kopieren in Supabase → Authentication → Emails → Templates)
//           docs/konto-mails/vorschau.html (alle Vorlagen mit Beispielwerten, zum Anschauen im Browser)
//
// Regeln (Plan 5.2, 10.1, 10.3):
// - Nie {{ .ConfirmationURL }}. Links bauen wir aus {{ .SiteURL }}, das Token steht im Fragment (#).
// - Keine Bilder, keine Schriften oder Dateien von fremden Servern, kein Tracking. Die Wortmarke ist Text.
// - Tabellen-Layout und Inline-Styles, damit Outlook, Gmail und Apple Mail gleich aussehen; lesbar auch ohne CSS.
// - Keine Go-Platzhalter in HTML-Kommentaren: Supabase würde sie trotzdem ersetzen.
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ZIEL = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "docs", "konto-mails");

const F = {
  navy: "#1B2540",
  gold: "#C9A84C",
  bg: "#F7F8FA",
  karte: "#FFFFFF",
  sand: "#F5F0E8",
  rand: "#E2E8F0",
  text: "#2D3748",
  leise: "#718096",
  link: "#457B9D",
};
const SERIF = "Georgia, 'Times New Roman', Times, serif";
const SANS = "-apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";

const absatz = (html) =>
  `<p style="margin:0 0 16px;font-family:${SANS};font-size:16px;line-height:1.55;color:${F.text};">${html}</p>`;
const klein = (html) =>
  `<p class="leise" style="margin:0 0 12px;font-family:${SANS};font-size:13px;line-height:1.5;color:${F.leise};">${html}</p>`;

/** Button, der auch in Outlook als Button erscheint (Tabellenzelle mit Hintergrund) */
const button = (href, text) => `
<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:8px 0 24px;">
  <tr>
    <td class="button" bgcolor="${F.navy}" style="border-radius:8px;background:${F.navy};">
      <a class="button-a" href="${href}" style="display:inline-block;padding:14px 28px;font-family:${SANS};font-size:16px;font-weight:700;line-height:1;color:#FFFFFF;text-decoration:none;border-radius:8px;">${text}</a>
    </td>
  </tr>
</table>`;

/**
 * Ersatz-Link unter dem Button, falls der Button nicht funktioniert. Bewusst OHNE die lange Adresse als Text:
 * GMX & Co. am Desktop brechen sie nicht um, die Mail wird dadurch breiter als das Lesefenster und dann
 * verkleinert dargestellt (Live-Test 17.11.2026). Der Link lässt sich weiter anklicken oder per Rechtsklick kopieren.
 */
const ersatzLink = (href, text) =>
  klein(`Klappt der Button nicht? Dann nutze diesen Link: <a href="${href}" style="color:${F.link};font-weight:700;">${text}</a>`);

const kasten = (html) => `
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 20px;">
  <tr>
    <td class="kasten" style="background:${F.sand};border-left:4px solid ${F.gold};border-radius:6px;padding:12px 16px;font-family:${SANS};font-size:14px;line-height:1.5;color:${F.text};">${html}</td>
  </tr>
</table>`;

const code = (wert) => `
<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:4px 0 24px;">
  <tr>
    <td class="kasten" style="background:${F.sand};border-radius:8px;padding:14px 22px;font-family:'Courier New',Courier,monospace;font-size:28px;font-weight:700;letter-spacing:6px;color:${F.navy};">${wert}</td>
  </tr>
</table>`;

/** Gemeinsames Gerüst: Wortmarke, Karte mit goldenem Strich, Titel, Inhalt, Fuß */
function geruest({ titel, vorschau, inhalt }) {
  return `<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="supported-color-schemes" content="light dark">
<title>${titel}</title>
<style>
  @media (prefers-color-scheme: dark) {
    .seite, .seite-td { background:#0D1117 !important; }
    .karte { background:#161B26 !important; border-color:#2D3748 !important; }
    .karte p, .karte td, .titel { color:#F7F8FA !important; }
    .leise, .leise a, .fuss, .fuss a { color:#A0AEC0 !important; }
    .wortmarke { color:#F7F8FA !important; }
    .kasten { background:#1F2533 !important; color:#F7F8FA !important; }
    .button { background:${F.gold} !important; }
    .button-a { color:${F.navy} !important; }
  }
  @media (max-width: 600px) { .innen { padding:24px 20px !important; } }
</style>
</head>
<body class="seite" style="margin:0;padding:0;background:${F.bg};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">${vorschau}</div>
<table role="presentation" class="seite" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:${F.bg};">
  <tr>
    <td class="seite-td" align="center" style="padding:32px 12px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;">
        <tr>
          <td style="padding:0 4px 18px;font-family:${SERIF};font-style:italic;font-size:24px;line-height:1;">
            <a class="wortmarke" href="https://diesdas.events" style="color:${F.navy};text-decoration:none;">dies<span style="color:${F.gold};">.</span>das<span style="color:${F.gold};">.</span>düsseldorf</a>
          </td>
        </tr>
        <tr>
          <td class="karte innen" style="background:${F.karte};border:1px solid ${F.rand};border-top:4px solid ${F.gold};border-radius:12px;padding:32px 36px;">
            <h1 class="titel" style="margin:0 0 18px;font-family:${SERIF};font-weight:normal;font-size:28px;line-height:1.2;color:${F.navy};">${titel}</h1>
            ${inhalt}
          </td>
        </tr>
        <tr>
          <td class="fuss" style="padding:20px 4px 0;font-family:${SANS};font-size:12px;line-height:1.6;color:${F.leise};">
            dies.das.düsseldorf · Rocktician e. K., Erkrather Str. 401, 40231 Düsseldorf<br>
            <a href="https://diesdas.events/impressum" style="color:${F.leise};">Impressum</a> ·
            <a href="https://diesdas.events/datenschutz" style="color:${F.leise};">Datenschutz</a>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>
`;
}

const LINK_NEU = "{{ .SiteURL }}/konto/bestaetigen#token_hash={{ .TokenHash }}&amp;art=neu";
const LINK_RESET = "{{ .SiteURL }}/konto/bestaetigen#token_hash={{ .TokenHash }}&amp;art=reset";
const LINK_EMAIL = "{{ .SiteURL }}/konto/bestaetigen#token_hash={{ .TokenHash }}&amp;art=email";

const VORLAGEN = [
  {
    datei: "1-confirm-signup",
    supabase: "Confirm signup",
    betreff: "Bitte bestätige deine Mailadresse für dies.das",
    html: geruest({
      titel: "Bestätige deine Mailadresse",
      vorschau: "Ein Klick, dann ist dein Konto bei dies.das.düsseldorf startklar.",
      inhalt: [
        absatz("Hallo!"),
        absatz("Schön, dass du ein Konto bei dies.das.düsseldorf anlegst. Bitte bestätige deine Mailadresse, dann ist deine Merkliste auf allen Geräten dabei."),
        button(LINK_NEU, "Adresse bestätigen"),
        kasten("Der Link gilt einmal. Öffnest du ihn auf einem anderen Gerät, bist du danach dort angemeldet."),
        ersatzLink(LINK_NEU, "Adresse bestätigen"),
        klein("Du hast kein Konto angelegt? Dann ignoriere diese Mail einfach, es passiert nichts."),
      ].join("\n"),
    }),
  },
  {
    datei: "2-reset-password",
    supabase: "Reset Password",
    betreff: "Neues Passwort für dies.das",
    html: geruest({
      titel: "Neues Passwort festlegen",
      vorschau: "Hier legst du ein neues Passwort für dein Konto fest.",
      inhalt: [
        absatz("Hallo!"),
        absatz("Jemand möchte das Passwort für dein Konto bei dies.das.düsseldorf zurücksetzen. Warst du das? Dann lege hier ein neues fest:"),
        button(LINK_RESET, "Neues Passwort festlegen"),
        kasten("Der Link gilt eine Stunde und nur einmal. Klappt er nicht, fordere auf der Website einfach einen neuen an."),
        ersatzLink(LINK_RESET, "Neues Passwort festlegen"),
        klein("Warst du das nicht? Dann ignoriere diese Mail. Dein Passwort bleibt, wie es ist."),
      ].join("\n"),
    }),
  },
  {
    datei: "3-reauthentication",
    supabase: "Reauthentication",
    betreff: "Dein Bestätigungscode für dies.das",
    html: geruest({
      titel: "Dein Bestätigungscode",
      vorschau: "Der Code für die Änderung deines Passworts.",
      inhalt: [
        absatz("Hallo!"),
        absatz("Du möchtest dein Passwort bei dies.das.düsseldorf ändern. Dein Bestätigungscode:"),
        code("{{ .Token }}"),
        klein("Warst du das nicht? Dann ignoriere diese Mail und ändere vorsichtshalber dein Passwort."),
      ].join("\n"),
    }),
  },
  {
    datei: "4-change-email",
    supabase: "Change Email Address",
    betreff: "Änderung deiner Mailadresse bei dies.das",
    // Seit 17.11.2026 im Konto selbst änderbar. Mit „Secure email change“ geht diese Mail an die alte UND die neue
    // Adresse, jeweils mit eigenem Link; die neue Adresse gilt erst, wenn beide bestätigt sind.
    html: geruest({
      titel: "Mailadresse ändern",
      vorschau: "Bitte bestätige die Änderung deiner Mailadresse.",
      inhalt: [
        absatz("Hallo!"),
        absatz("Für dein Konto bei dies.das.düsseldorf soll die Mailadresse von <b>{{ .Email }}</b> auf <b>{{ .NewEmail }}</b> geändert werden. Bitte bestätige das:"),
        button(LINK_EMAIL, "Änderung bestätigen"),
        kasten("Diese Mail geht an deine bisherige und an deine neue Adresse. Die Änderung gilt, sobald du beide Links bestätigt hast."),
        ersatzLink(LINK_EMAIL, "Änderung bestätigen"),
        klein("Warst du das nicht? Dann ignoriere diese Mail, es ändert sich nichts. Ändere vorsichtshalber dein Passwort."),
      ].join("\n"),
    }),
  },
  {
    datei: "5-magic-link",
    supabase: "Magic Link",
    betreff: "Anmeldung bei dies.das",
    html: geruest({
      titel: "Anmeldung bei dies.das",
      vorschau: "Bei uns meldest du dich mit Mailadresse und Passwort an.",
      inhalt: [
        absatz("Hallo!"),
        absatz("Für dein Konto bei dies.das.düsseldorf wurde eine Anmeldung per Link angefragt. Diese Anmeldeart bieten wir nicht an. Melde dich bitte mit Mailadresse und Passwort an."),
        button("{{ .SiteURL }}/konto/anmelden", "Zur Anmeldung"),
        klein("Warst du das nicht? Dann ignoriere diese Mail. Es passiert nichts."),
      ].join("\n"),
    }),
  },
  {
    datei: "6-invite-user",
    supabase: "Invite user",
    betreff: "Einladung zu dies.das",
    html: geruest({
      titel: "Einladung zu dies.das",
      vorschau: "Ein Konto legst du bei uns selbst an.",
      inhalt: [
        absatz("Hallo!"),
        absatz("Du hast eine Einladung zu dies.das.düsseldorf erhalten. Einladungen nutzen wir nicht. Ein Konto legst du auf unserer Website selbst an, sobald das möglich ist."),
        button("{{ .SiteURL }}/konto/anmelden", "Zu dies.das"),
        klein("Du weißt nichts davon? Dann ignoriere diese Mail."),
      ].join("\n"),
    }),
  },
  // Sicherheits-Hinweise (Supabase: Authentication → Emails, Bereich „Security“ bzw. Notifications), falls angeboten
  {
    datei: "7-password-changed",
    supabase: "Password changed (Hinweis)",
    betreff: "Dein Passwort bei dies.das wurde geändert",
    html: geruest({
      titel: "Passwort geändert",
      vorschau: "Das Passwort für dein Konto wurde gerade geändert.",
      inhalt: [
        absatz("Hallo!"),
        absatz("Das Passwort für dein Konto bei dies.das.düsseldorf ({{ .Email }}) wurde gerade geändert."),
        kasten("Warst du das nicht? Dann setz dein Passwort sofort über „Passwort vergessen“ neu und schreib uns an hallo@diesdas.events."),
        button("{{ .SiteURL }}/konto/passwort-vergessen", "Passwort neu setzen"),
      ].join("\n"),
    }),
  },
  {
    datei: "8-email-changed",
    supabase: "Email address changed (Hinweis)",
    betreff: "Deine Mailadresse bei dies.das wurde geändert",
    html: geruest({
      titel: "Mailadresse geändert",
      vorschau: "Die Mailadresse deines Kontos wurde geändert.",
      inhalt: [
        absatz("Hallo!"),
        absatz("Die Mailadresse deines Kontos bei dies.das.düsseldorf wurde von <b>{{ .OldEmail }}</b> auf <b>{{ .Email }}</b> geändert."),
        kasten("Warst du das nicht? Dann schreib uns bitte sofort an hallo@diesdas.events."),
      ].join("\n"),
    }),
  },
];

/** Ersatz-Code für die Bestätigungsmail – nur nach dem Vorversuch einsetzen (Plan 5.2) */
export const ERSATZ_CODE_BLOCK = klein(
  `Klappt der Button nicht? Dann gib auf der Seite deine Mailadresse und diesen Code ein: <strong style="color:${F.navy};font-size:16px;letter-spacing:2px;">{{ .Token }}</strong>`,
);

// ── Schreiben ──────────────────────────────────────────────────────────────
mkdirSync(ZIEL, { recursive: true });
for (const v of VORLAGEN) writeFileSync(join(ZIEL, `${v.datei}.html`), v.html, "utf8");
writeFileSync(join(ZIEL, "ersatz-code-block.html"), ERSATZ_CODE_BLOCK + "\n", "utf8");

// Vorschau mit Beispielwerten (nur zum Anschauen; wird nicht in Supabase eingetragen)
const beispiel = (html) =>
  html
    .replaceAll("{{ .SiteURL }}", "https://diesdas.events")
    .replaceAll("{{ .TokenHash }}", "pkce_8f2c1e0b9d7a4c3e5f6a1b2c3d4e5f60")
    .replaceAll("{{ .Token }}", "482915");
const esc = (s) => s.replaceAll("&", "&amp;").replaceAll('"', "&quot;");
const escText = (s) => s.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
// Je Vorlage: Betreff und HTML zum Kopieren (mit den echten Platzhaltern {{ .SiteURL }} usw., so wie Supabase sie
// braucht) und darunter die Ansicht mit Beispielwerten.
const vorschau = `<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Konto-Mails zum Eintragen</title>
<style>
  body { margin:0; padding:24px 16px; background:#e9ecf1; font-family:${SANS}; color:#1B2540; }
  h1 { font-family:${SERIF}; font-style:italic; font-weight:normal; margin:0 0 6px; }
  p.hinweis { margin:0 0 24px; color:#4a5568; font-size:14px; line-height:1.5; }
  section { max-width:680px; margin:0 auto 40px; }
  h2 { font-size:17px; margin:0 0 8px; }
  .zeile { display:flex; flex-wrap:wrap; align-items:center; gap:8px; margin:0 0 8px; font-size:14px; }
  .zeile code { background:#fff; border:1px solid #cbd5e0; border-radius:6px; padding:6px 8px; }
  button { font:inherit; font-size:14px; font-weight:700; padding:8px 14px; border:none; border-radius:8px; cursor:pointer; background:#1B2540; color:#fff; }
  button.ok { background:#2A9D8F; }
  textarea { width:100%; height:110px; box-sizing:border-box; font:12px/1.4 'Courier New', monospace; border:1px solid #cbd5e0; border-radius:8px; padding:8px; margin:0 0 12px; }
  iframe { width:100%; height:640px; border:1px solid #cbd5e0; border-radius:8px; background:#fff; }
</style></head><body>
<section><h1>Konto-Mails zum Eintragen</h1>
<p class="hinweis">So geht es: In Supabase unter Authentication → Emails → Templates die passende Vorlage öffnen.
„Betreff kopieren“ und ins Feld <b>Subject</b> einfügen, dann „HTML kopieren“ und den Inhalt von <b>Message body</b>
komplett ersetzen. Speichern. Die Ansicht darunter zeigt die Mail mit Beispielwerten.</p></section>
${VORLAGEN.map((v, i) => `<section><h2>${i + 1}. ${v.supabase}</h2>
<div class="zeile">Betreff: <code id="betreff-${i}">${escText(v.betreff)}</code>
<button type="button" data-kopie="betreff-${i}">Betreff kopieren</button>
<button type="button" data-kopie="html-${i}">HTML kopieren</button></div>
<textarea id="html-${i}" readonly spellcheck="false">${escText(v.html)}</textarea>
<iframe title="${v.supabase}" srcdoc="${esc(beispiel(v.html))}"></iframe></section>`).join("\n")}
<script>
  // Kopieren in die Zwischenablage; ohne Clipboard-API (z. B. bei file://) über Markieren und execCommand
  document.addEventListener("click", async (e) => {
    const knopf = e.target.closest("button[data-kopie]");
    if (!knopf) return;
    const quelle = document.getElementById(knopf.dataset.kopie);
    const text = quelle.value ?? quelle.textContent;
    let ok = false;
    try { await navigator.clipboard.writeText(text); ok = true; } catch {}
    if (!ok && quelle.select) { quelle.focus(); quelle.select(); ok = document.execCommand("copy"); }
    const alt = knopf.textContent;
    knopf.textContent = ok ? "Kopiert ✓" : "Bitte markieren und Strg+C";
    knopf.classList.toggle("ok", ok);
    setTimeout(() => { knopf.textContent = alt; knopf.classList.remove("ok"); }, 2000);
  });
</script>
</body></html>
`;
writeFileSync(join(ZIEL, "vorschau.html"), vorschau, "utf8");

console.log(`Mailvorlagen geschrieben nach ${ZIEL}:`);
for (const v of VORLAGEN) console.log(`  ${v.datei}.html  ←  ${v.supabase}  ·  Betreff: ${v.betreff}`);
console.log("  ersatz-code-block.html (erst nach dem Vorversuch)\n  vorschau.html");
