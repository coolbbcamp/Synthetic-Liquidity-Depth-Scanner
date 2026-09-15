"use client";

import { usePathname, useSearchParams } from "next/navigation";
import type { Locale } from "@/i18n/config";

export function LangSwitcher({ current }: { current: Locale }) {
  const pathname = usePathname() || "/";
  const searchParams = useSearchParams();
  const query = searchParams.toString();

  function hrefFor(locale: Locale) {
    const segments = pathname.split("/").filter(Boolean);
    if (segments.length === 0) {
      return query ? `/${locale}?${query}` : `/${locale}`;
    }
    segments[0] = locale;
    const path = `/${segments.join("/")}`;
    return query ? `${path}?${query}` : path;
  }

  return (
    <div className="lang-switcher" role="group" aria-label="Language">
      <a href={hrefFor("en")} className={current === "en" ? "active" : ""} lang="en">
        EN
      </a>
      <span className="lang-divider">/</span>
      <a href={hrefFor("zh")} className={current === "zh" ? "active" : ""} lang="zh-Hans">
        中文
      </a>
    </div>
  );
}
