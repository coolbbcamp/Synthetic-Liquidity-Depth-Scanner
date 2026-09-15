import type { Metadata } from "next";
import type { Locale } from "@/i18n/config";
import { locales } from "@/i18n/config";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://liquidity-scanner.example";

export function localeAlternates(path: string = "") {
  const languages: Record<string, string> = {};
  for (const locale of locales) {
    languages[locale] = `${siteUrl}/${locale}${path}`;
  }
  return { languages };
}

export function buildPageMetadata(
  locale: Locale,
  title: string,
  description: string,
  path: string = "",
  agencyName: string = "CoolBB",
): Metadata {
  const fullTitle = title.startsWith(`${agencyName} ·`)
    ? title
    : `${agencyName} · ${title}`;

  return {
    title: fullTitle,
    description,
    alternates: {
      canonical: `${siteUrl}/${locale}${path}`,
      languages: localeAlternates(path).languages,
    },
    icons: {
      icon: [
        { url: "/favicon.ico", sizes: "32x32" },
        { url: "/coolbb-logo.png", type: "image/png", sizes: "512x512" },
      ],
      apple: "/coolbb-logo.png",
      shortcut: "/favicon.ico",
    },
    openGraph: {
      title: fullTitle,
      description,
      locale: locale === "zh" ? "zh_CN" : "en_US",
    },
  };
}
