"use client";
// Feld mit der Feed-Adresse und Button zum Kopieren (Seite /rss). Ohne Zwischenablage-API (alter Browser, kein HTTPS)
// markiert der Button den Text im Feld, damit man ihn von Hand kopieren kann.
import { useRef, useState } from "react";

export function FeedAdresse({ url }: { url: string }) {
  const feld = useRef<HTMLInputElement>(null);
  const [kopiert, setKopiert] = useState(false);
  return (
    <div className="feed-adresse">
      <label htmlFor="feed-url" className="feed-adresse__label">Adresse des Feeds</label>
      <div className="feed-adresse__zeile">
        <input
          id="feed-url"
          ref={feld}
          className="feed-adresse__feld"
          type="text"
          readOnly
          value={url}
          onFocus={(e) => e.currentTarget.select()}
        />
        <button
          type="button"
          className="btn btn--gold"
          onClick={async () => {
            try {
              await navigator.clipboard.writeText(url);
              setKopiert(true);
              setTimeout(() => setKopiert(false), 2000);
            } catch {
              feld.current?.select();
            }
          }}
        >
          {kopiert ? "Kopiert!" : "Adresse kopieren"}
        </button>
      </div>
    </div>
  );
}
