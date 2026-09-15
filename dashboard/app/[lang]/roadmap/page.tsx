import { notFound } from "next/navigation";
import { RoadmapLegend, RoadmapVisual } from "@/components/roadmap/roadmap-visual";
import { RoadmapStages } from "@/components/roadmap/roadmap-stages";
import { hasLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/get-dictionary";
import { buildPageMetadata } from "@/lib/metadata";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ lang: string }>;
}) {
  const { lang } = await params;
  if (!hasLocale(lang)) return {};
  const dict = await getDictionary(lang);
  return buildPageMetadata(lang, dict.roadmap.title, dict.roadmap.subtitle, "/roadmap");
}

export default async function RoadmapPage({
  params,
}: {
  params: Promise<{ lang: string }>;
}) {
  const { lang } = await params;
  if (!hasLocale(lang)) notFound();
  const dict = await getDictionary(lang);

  return (
    <section className="page-shell page-shell--immersive roadmap-page">
      <RoadmapVisual stages={dict.roadmap.stages} legend={dict.roadmap.legend} />
      <div className="roadmap-scrim" aria-hidden="true" />

      <div className="page-content container container--wide">
        <div className="prose roadmap-header">
          <p className="section-label">{dict.nav.roadmap}</p>
          <h1>{dict.roadmap.title}</h1>
          <p className="muted">{dict.roadmap.subtitle}</p>
          <RoadmapLegend legend={dict.roadmap.legend} />
        </div>

        <RoadmapStages stages={dict.roadmap.stages} />
      </div>
    </section>
  );
}
