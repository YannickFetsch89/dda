// Legacy-Route: /event/{uuid} → 301-Redirect auf /event/{kategorie}/{slug}
import { notFound, redirect } from "next/navigation";
import { eventLaden } from "@/lib/daten";
import { eventPfad } from "@/components/karten";

export const instant = false;

type Props = { params: Promise<{ kategorie: string }> };

export default async function LegacyEventSeite(props: Props) {
  const { kategorie } = await props.params;
  const kennung = decodeURIComponent(kategorie);

  if (!/^[0-9a-f-]{36}$/i.test(kennung)) notFound();

  const e = await eventLaden(kennung);
  if (!e) notFound();

  redirect(eventPfad(e));
}
