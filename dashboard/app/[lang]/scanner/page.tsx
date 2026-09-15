import { notFound } from "next/navigation";
import { PageShell } from "@/components/layout/page-shell";
import { hasLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/get-dictionary";
import { buildPageMetadata } from "@/lib/metadata";
import { LeaderboardClient } from "./leaderboard-client";

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
    dict.scanner.leaderboardTitle,
    dict.scanner.leaderboardSubtitle,
    "/scanner",
  );
}

export default async function ScannerPage({
  params,
}: {
  params: Promise<{ lang: string }>;
}) {
  const { lang } = await params;
  if (!hasLocale(lang)) notFound();
  const dict = await getDictionary(lang);

  return (
    <PageShell wide prose={false}>
      <LeaderboardClient dict={dict.scanner} common={dict.common} locale={lang} />
    </PageShell>
  );
}
