"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

const LiquidityHeroScene = dynamic(() => import("./liquidity-hero-scene"), {
  ssr: false,
});

function probeWebGL(): boolean {
  if (typeof document === "undefined") return false;
  try {
    const canvas = document.createElement("canvas");
    return !!(
      canvas.getContext("webgl2") ||
      canvas.getContext("webgl") ||
      canvas.getContext("experimental-webgl")
    );
  } catch {
    return false;
  }
}

export function LiquidityHeroBackground() {
  const [ready, setReady] = useState(false);
  const [webglOk, setWebglOk] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    setWebglOk(probeWebGL());
    setReducedMotion(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    setReady(true);
  }, []);

  return (
    <div className="home-page-backdrop" aria-hidden="true">
      {ready && webglOk && <LiquidityHeroScene animate={!reducedMotion} />}
    </div>
  );
}
