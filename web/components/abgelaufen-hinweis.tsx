// Hinweis oben auf der Seite eines abgelaufenen Events. Die Seite bleibt online und indexierbar.
import Link from "next/link";

export function AbgelaufenHinweis({ abgelaufen }: { abgelaufen: boolean }) {
  if (!abgelaufen) return null;
  return (
    <p className="abgelaufen-hinweis" role="status">
      <span className="icon" aria-hidden data-icon="history" />
      <span>
        <b>Dieses Event hat bereits stattgefunden.</b>{" "}
        <Link href="/entdecken" className="link">
          Aktuelle Events in Düsseldorf entdecken
        </Link>
      </span>
    </p>
  );
}
