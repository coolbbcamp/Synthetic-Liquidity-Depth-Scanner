import type { MetadataRoute } from "next";
import { locales } from "@/i18n/config";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://liquidity-scanner.example";

const routes = ["", "/why", "/roadmap", "/methodology", "/scanner", "/scanner/calculator"];

export default function sitemap(): MetadataRoute.Sitemap {
  const entries: MetadataRoute.Sitemap = [];

  for (const locale of locales) {
    for (const route of routes) {
      entries.push({
        url: `${siteUrl}/${locale}${route}`,
        lastModified: new Date("2026-09-13"),
        changeFrequency: route === "" || route === "/scanner" ? "weekly" : "monthly",
        priority: route === "" ? 1 : route === "/scanner" ? 0.9 : 0.7,
      });
    }
  }

  return entries;
}
