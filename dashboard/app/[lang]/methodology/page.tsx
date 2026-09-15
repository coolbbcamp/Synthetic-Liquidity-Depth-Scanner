import { notFound } from "next/navigation";
import { PageShell } from "@/components/layout/page-shell";
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
  return buildPageMetadata(lang, dict.methodology.title, dict.methodology.subtitle, "/methodology");
}

export default async function MethodologyPage({
  params,
}: {
  params: Promise<{ lang: string }>;
}) {
  const { lang } = await params;
  if (!hasLocale(lang)) notFound();
  const dict = await getDictionary(lang);

  return (
    <PageShell>
      <p className="section-label">{dict.nav.methodology}</p>
      <h1>{dict.methodology.title}</h1>
      <p className="muted">{dict.methodology.subtitle}</p>

      {dict.methodology.steps.map((step) => (
        <section key={step.title} className="method-step">
          <h2>{step.title}</h2>
          <p>{step.body}</p>
        </section>
      ))}

      <hr className="hairline" />

      <p><strong>{dict.common.disclaimer}</strong></p>
      <p className="muted">{dict.methodology.disclaimer}</p>
      <p className="muted">{dict.common.provenance}</p>
    </PageShell>
  );
}
