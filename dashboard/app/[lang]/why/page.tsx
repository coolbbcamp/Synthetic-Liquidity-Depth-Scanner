import { notFound } from "next/navigation";
import { CliffChart } from "@/components/charts/cliff-chart";
import { PageShell } from "@/components/layout/page-shell";
import { DepthSurface } from "@/components/charts/depth-surface";
import { ExitImpactBars } from "@/components/charts/exit-impact-bars";
import { TvlVsExitScatter } from "@/components/charts/tvl-vs-exit-scatter";
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
  return buildPageMetadata(lang, dict.why.title, dict.why.subtitle, "/why");
}

export default async function WhyPage({
  params,
}: {
  params: Promise<{ lang: string }>;
}) {
  const { lang } = await params;
  if (!hasLocale(lang)) notFound();
  const dict = await getDictionary(lang);

  return (
    <PageShell wide>
      <p className="section-label">{dict.nav.why}</p>
      <h1>{dict.why.title}</h1>
      <p className="muted">{dict.why.subtitle}</p>

      {dict.why.sections.map((section) => (
        <section key={section.title} className="why-section prose">
          <h2>{section.title}</h2>
          <p>{section.body}</p>
        </section>
      ))}

      <hr className="hairline" />

      <DepthSurface
        title={dict.charts.depthSurfaceTitle}
        caption={dict.charts.depthSurfaceCaption}
        axes={dict.charts.depthSurfaceAxes}
        hint={dict.charts.depthSurfaceHint}
        fallbackNotice={dict.charts.depthSurfaceFallbackNotice}
        fallbackTitle={dict.charts.depthSurfaceFallbackTitle}
        fallbackCaption={dict.charts.depthSurfaceFallbackCaption}
        tooltipLabels={dict.charts.depthSurfaceTooltip}
      />
      <ExitImpactBars title={dict.charts.exitImpactTitle} caption={dict.charts.exitImpactCaption} />
      <TvlVsExitScatter
        title={dict.charts.tvlScatterTitle}
        caption={dict.charts.tvlScatterCaption}
        tvlAxis={dict.charts.tvlAxis}
        impactAxis={dict.charts.impactAxis}
      />
      <CliffChart
        title={dict.charts.cliffTitle}
        caption={dict.charts.cliffCaption}
        notionalAxis={dict.charts.notionalAxis}
        priceAxis={dict.charts.priceAxis}
      />

      <p className="muted">{dict.common.provenance}</p>
    </PageShell>
  );
}
