import type { Metadata } from "next";

import { DM_Sans, Instrument_Serif } from "next/font/google";

import { notFound } from "next/navigation";

import { Suspense } from "react";

import { AgencyFooter } from "@/components/brand/agency-footer";

import { CoolBBWordmark } from "@/components/brand/coolbb-wordmark";

import { LangSwitcher } from "@/components/lang-switcher";

import { ThemeProvider } from "@/components/theme-provider";

import { SoundToggle } from "@/components/sound-toggle";

import { ThemeToggle } from "@/components/theme-toggle";

import { hasLocale, locales, type Locale } from "@/i18n/config";

import { getDictionary } from "@/i18n/get-dictionary";

import { buildPageMetadata } from "@/lib/metadata";

import "../globals.css";



const display = Instrument_Serif({

  subsets: ["latin"],

  weight: ["400"],

  variable: "--font-display",

});



const body = DM_Sans({

  subsets: ["latin"],

  weight: ["400", "500", "600"],

  variable: "--font-body",

});



const themeScript = `(function(){try{var m=localStorage.getItem('lds-theme');var t=m==='light'||m==='dark'?m:(window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');document.documentElement.setAttribute('data-theme',t);}catch(e){document.documentElement.setAttribute('data-theme','light');}})();`;



export async function generateStaticParams() {

  return locales.map((lang) => ({ lang }));

}



export async function generateMetadata({

  params,

}: {

  params: Promise<{ lang: string }>;

}): Promise<Metadata> {

  const { lang } = await params;

  if (!hasLocale(lang)) return {};

  const dict = await getDictionary(lang);

  return buildPageMetadata(

    lang,

    dict.product.name,

    dict.home.subtitle,

    "",

    dict.agency.name,

  );

}



export default async function LangLayout({

  children,

  params,

}: {

  children: React.ReactNode;

  params: Promise<{ lang: string }>;

}) {

  const { lang } = await params;

  if (!hasLocale(lang)) notFound();

  const dict = await getDictionary(lang);

  const locale = lang as Locale;

  const prefix = `/${locale}`;



  return (

    <html

      lang={locale}

      suppressHydrationWarning

      className={`${display.variable} ${body.variable}`}

    >

      <head>

        <script dangerouslySetInnerHTML={{ __html: themeScript }} />

      </head>

      <body>

        <ThemeProvider>

          <div className="site-shell">

            <div className="site-grid-bg" aria-hidden="true" />

            <header className="site-header">

              <div className="container container--wide">

                <CoolBBWordmark />

                <div className="header-controls">

                  <nav className="site-nav" aria-label="Main">

                    <a href={prefix}>{dict.nav.home}</a>

                    <a href={`${prefix}/why`}>{dict.nav.why}</a>

                    <a href={`${prefix}/roadmap`}>{dict.nav.roadmap}</a>

                    <a href={`${prefix}/methodology`}>{dict.nav.methodology}</a>

                    <a href={`${prefix}/scanner`}>{dict.nav.scanner}</a>

                    <a href={`${prefix}/scanner/calculator`}>{dict.nav.calculator}</a>

                  </nav>

                  <SoundToggle />

                  <ThemeToggle />

                  <Suspense fallback={null}>

                    <LangSwitcher current={locale} />

                  </Suspense>

                </div>

              </div>

            </header>

            <main className="site-main">{children}</main>

            <AgencyFooter

              builtBy={dict.agency.builtBy}

              tagline={dict.agency.tagline}

              contactX={dict.agency.contactX}

              website={dict.agency.website}

              provenance={dict.common.provenance}

              disclaimer={dict.common.disclaimer}

            />

          </div>

        </ThemeProvider>

      </body>

    </html>

  );

}


