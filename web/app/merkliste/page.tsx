import type { Metadata } from "next";
import { MerklisteInhalt, MerklisteUntertitel } from "@/components/merkliste";
import { kontenAktiv } from "@/lib/konto/konfig";

export const metadata: Metadata = {
  title: "Merkliste",
  robots: { index: false },
};

export default function Merkliste() {
  return (
    <div className="container">
      <div className="seitentitel">
        <h1 className="d">Merkliste</h1>
        <MerklisteUntertitel />
      </div>
      <div className="sektion">
        <MerklisteInhalt kontenAn={kontenAktiv()} />
      </div>
    </div>
  );
}
