"use client";
// Admin-Bereich – Rahmen mit Navigation (Plan Admin-Dashboard 4.1). Die Navigation steht fest für alle Stufen;
// was noch nicht gebaut ist, steht als „Stufe n“ da. Der Rahmen fragt /api/admin/ich: ohne Sitzung zur Anmeldung,
// ohne Zwei-Faktor zum Code. Daten liefern nur die Routen unter /api/admin, die das selbst noch einmal prüfen.
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

const NAVIGATION: { titel: string; href?: string; stufe?: string }[] = [
  { titel: "Cockpit", href: "/admin" },
  { titel: "Events", href: "/admin/events" },
  { titel: "Vorschläge", href: "/admin/vorschlaege" },
  { titel: "Empfehlungen", href: "/admin/empfehlungen" },
  { titel: "Scraper", href: "/admin/scraper" },
  { titel: "Magazin", href: "/admin/magazin" },
  { titel: "Orte & Guides", href: "/admin/orte" },
  { titel: "Instagram", stufe: "eigener Plan" },
  { titel: "Newsletter", href: "/admin/newsletter" },
  { titel: "Meldungen", href: "/admin/meldungen" },
  { titel: "SEO-Aufräumen", href: "/admin/seo" },
  { titel: "Konten", href: "/admin/konten" },
  { titel: "Technik", href: "/admin/technik" },
  { titel: "Protokoll", href: "/admin/protokoll" },
];

/** Seiten ohne Rahmen und ohne Prüfung (sie führen erst zur Sitzung) */
const OHNE_RAHMEN = new Set(["/admin/anmelden", "/admin/zwei-faktor"]);

export function AdminRahmen({ children }: { children: ReactNode }) {
  const pfad = usePathname();
  const [email, setEmail] = useState<string | null>(null);
  const ohneRahmen = OHNE_RAHMEN.has(pfad);

  useEffect(() => {
    if (ohneRahmen) return;
    let aktiv = true;
    fetch("/api/admin/ich", { cache: "no-store" })
      .then(async (r) => {
        if (!aktiv) return;
        if (r.status === 401) return window.location.assign("/admin/anmelden");
        const daten = (await r.json().catch(() => ({}))) as { email?: string; code?: string };
        if (r.status === 403 && daten.code === "zwei_faktor") return window.location.assign("/admin/zwei-faktor");
        if (r.status === 403) return window.location.assign("/admin/anmelden");
        if (r.ok) setEmail(daten.email ?? "");
      })
      .catch(() => {});
    return () => {
      aktiv = false;
    };
  }, [ohneRahmen, pfad]);

  if (ohneRahmen) return <div className="admin-rahmen admin-rahmen--leer">{children}</div>;

  return (
    <div className="admin-rahmen">
      <aside className="admin-seitenleiste">
        <div className="admin-marke">
          dies<span>.</span>das<span>.</span>düsseldorf
          <small>Admin</small>
        </div>
        <nav className="admin-nav" aria-label="Admin-Bereiche">
          {NAVIGATION.map((n) =>
            n.href ? (
              <Link key={n.titel} href={n.href} aria-current={pfad === n.href || (n.href !== "/admin" && pfad.startsWith(n.href + "/")) ? "page" : undefined}>
                {n.titel}
              </Link>
            ) : (
              <span key={n.titel} aria-disabled="true">
                {n.titel} <small>Stufe {n.stufe}</small>
              </span>
            ),
          )}
        </nav>
        <div className="admin-nutzer">
          {email !== null && <span>{email}</span>}
          <button type="button" className="admin-knopf admin-knopf--leise" onClick={abmelden}>
            Abmelden
          </button>
        </div>
      </aside>
      <div className="admin-inhalt">{email === null ? <p className="admin-unterzeile">Wird geladen …</p> : children}</div>
    </div>
  );
}

async function abmelden() {
  await fetch("/api/admin/abmelden", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" }).catch(() => {});
  window.location.assign("/admin/anmelden");
}
