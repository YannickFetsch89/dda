import Link from "next/link";
import { Leer } from "@/components/karten";

export default function NichtGefunden() {
  return (
    <div className="container sektion">
      <Leer titel="Hier ist nichts los.">
        <span>Die Seite gibt es nicht oder das Event ist schon vorbei.</span>
        <Link href="/" className="btn btn--gold">
          Zur Startseite
        </Link>
      </Leer>
    </div>
  );
}
