import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { Tagesplaner, TagesplanerSkeleton } from "@/components/tagesplaner";
import { istGueltigerTag, tagLang } from "@/lib/datum";

export async function generateMetadata(props: PageProps<"/tag/[datum]">): Promise<Metadata> {
  const { datum } = await props.params;
  if (!istGueltigerTag(datum)) return { title: "Tag nicht gefunden" };
  return { title: `Events am ${tagLang(datum)}`, description: `Alle Events in Düsseldorf am ${tagLang(datum)}.` };
}

export default function Tag(props: PageProps<"/tag/[datum]">) {
  return (
    <Suspense fallback={<TagesplanerSkeleton />}>
      <TagInhalt params={props.params} />
    </Suspense>
  );
}

async function TagInhalt({ params }: Pick<PageProps<"/tag/[datum]">, "params">) {
  const { datum } = await params;
  if (!istGueltigerTag(datum)) notFound();
  return <Tagesplaner tag={datum} />;
}
