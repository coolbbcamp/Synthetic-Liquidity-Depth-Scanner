import { notFound } from "next/navigation";
import { PageShell } from "@/components/layout/page-shell";
import { hasLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/get-dictionary";
import { buildPageMetadata } from "@/lib/metadata";
import { AssetClient } from "./asset-client";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ lang: string; mint: string }>;
}) {
  const { lang, mint } = await params;
  if (!hasLocale(lang)) return {};
  const dict = await getDictionary(lang);
  return buildPageMetadata(
    lang,
    `${dict.scanner.assetTitle} — ${mint.slice(0, 8)}…`,
    dict.scanner.leaderboardSubtitle,
    `/scanner/asset/${mint}`,
  );
}

export default async function AssetPage({
  params,
}: {
  params: Promise<{ lang: string; mint: string }>;
}) {
  const { lang, mint } = await params;
  if (!hasLocale(lang)) notFound();
  const dict = await getDictionary(lang);

  return (
    <PageShell wide prose={false}>
      <AssetClient mint={mint} dict={dict.scanner} common={dict.common} />
    </PageShell>
  );
}
