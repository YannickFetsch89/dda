import type { Metadata } from "next";
import { MerklisteInhalt, MerklisteUntertitel } from "@/components/merkliste";
import { kontenAktiv } from "@/lib/konto/konfig";
import { KontoRaster } from "../konto/rahmen";

export const metadata: Metadata = {
  title: "Merkliste",
  robots: { index: false },
};

// Seitenleiste von Mein dies.das am Desktop, nur bei html[data-konto="1"] sichtbar (Plan Mein Bereich 3.2, 3.4)
export default function Merkliste() {
  return (
    <div className="container">
      <KontoRaster>
        <div className="seitentitel">
          <h1 className="d">Merkliste</h1>
          <MerklisteUntertitel />
        </div>
        <div className="sektion">
          <MerklisteInhalt kontenAn={kontenAktiv()} />
        </div>
      </KontoRaster>
    </div>
  );
}
