import { notFound } from "next/navigation";
import { PageShell } from "@/components/layout/page-shell";
import { hasLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/get-dictionary";
import { buildPageMetadata } from "@/lib/metadata";
import { CalculatorClient } from "./calculator-client";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ lang: string }>;
}) {
  const { lang } = await params;
  if (!hasLocale(lang)) return {};
  const dict = await getDictionary(lang);
  return buildPageMetadata(
    lang,
    dict.scanner.calculatorTitle,
    dict.scanner.calculatorSubtitle,
    "/scanner/calculator",
  );
}

export default async function CalculatorPage({
  params,
}: {
  params: Promise<{ lang: string }>;
}) {
  const { lang } = await params;
  if (!hasLocale(lang)) notFound();
  const dict = await getDictionary(lang);

  return (
    <PageShell wide prose={false}>
      <CalculatorClient dict={dict.scanner} />
    </PageShell>
  );
}
