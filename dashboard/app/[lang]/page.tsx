import { notFound } from "next/navigation";
import { LiquidityHeroBackground } from "@/components/hero/liquidity-hero-background";
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
  return buildPageMetadata(lang, dict.product.name, dict.home.subtitle, "", dict.agency.name);
}

export default async function HomePage({
  params,
}: {
  params: Promise<{ lang: string }>;
}) {
  const { lang } = await params;
  if (!hasLocale(lang)) notFound();
  const dict = await getDictionary(lang);
  const prefix = `/${lang}`;

  return (
    <div className="page-shell page-shell--immersive home-page">
      <LiquidityHeroBackground />
      <div className="home-page-scrim" aria-hidden="true" />

      <section className="home-hero">
        <div className="home-hero-content prose">
          <p className="agency-kicker">{dict.home.kicker}</p>
          <h1>{dict.home.title}</h1>
          <p className="muted">{dict.home.subtitle}</p>
          <p className="home-product-line muted">{dict.home.productLine}</p>
        </div>
      </section>

      <div className="page-content container prose home-body">
        <div className="stat-grid">
          <div className="stat-item">
            <span className="stat-value">{dict.home.stat1Value}</span>
            <span className="stat-label">{dict.home.stat1Label}</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{dict.home.stat2Value}</span>
            <span className="stat-label">{dict.home.stat2Label}</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{dict.home.stat3Value}</span>
            <span className="stat-label">{dict.home.stat3Label}</span>
          </div>
        </div>

        <hr className="hairline" />

        <h2>{dict.home.whatTitle}</h2>
        <p>{dict.home.whatBody}</p>

        <div className="cta-row">
          <a className="btn btn--brand" href={`${prefix}/scanner`}>{dict.home.ctaScanner}</a>
          <a className="btn btn--secondary" href={`${prefix}/why`}>{dict.home.ctaWhy}</a>
        </div>

        <p className="muted">{dict.common.provenance}</p>
      </div>
    </div>
  );
}
