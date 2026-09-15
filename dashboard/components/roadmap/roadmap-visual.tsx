"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { RoadmapFallback } from "./roadmap-fallback";
import type { RoadmapLegend, RoadmapStage } from "./types";

const RoadmapScene = dynamic(() => import("./roadmap-scene"), {
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

type Props = {
  stages: RoadmapStage[];
  legend: RoadmapLegend;
};

export function RoadmapVisual({ stages, legend }: Props) {
  const [ready, setReady] = useState(false);
  const [webglOk, setWebglOk] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    setWebglOk(probeWebGL());
    setReducedMotion(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    setReady(true);
  }, []);

  const useFallback = !ready || !webglOk;

  return (
    <div className="roadmap-backdrop" aria-hidden={useFallback ? undefined : true}>
      {useFallback ? (
        <RoadmapFallback stages={stages} legend={legend} />
      ) : (
        <RoadmapScene stages={stages} animate={!reducedMotion} />
      )}
    </div>
  );
}

export function RoadmapLegend({ legend }: { legend: RoadmapLegend }) {
  return (
    <div className="roadmap-legend">
      <span className="roadmap-legend__item roadmap-legend__item--complete">{legend.complete}</span>
      <span className="roadmap-legend__item roadmap-legend__item--active">{legend.active}</span>
      <span className="roadmap-legend__item roadmap-legend__item--planned">{legend.planned}</span>
    </div>
  );
}
