import type { Metadata } from "next";
import { MerklisteInhalt } from "@/components/merkliste";

export const metadata: Metadata = {
  title: "Merkliste",
  robots: { index: false },
};

export default function Merkliste() {
  return (
    <div className="container">
      <div className="seitentitel">
        <h1 className="d">Merkliste</h1>
        <span>Nur auf diesem Gerät gespeichert</span>
      </div>
      <div className="sektion">
        <MerklisteInhalt />
      </div>
    </div>
  );
}
