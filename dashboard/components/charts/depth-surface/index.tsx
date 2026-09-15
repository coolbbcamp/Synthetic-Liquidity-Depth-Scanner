"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import { ExitImpactBars } from "@/components/charts/exit-impact-bars";

const DepthSurfaceScene = dynamic(() => import("./scene"), {
  ssr: false,
  loading: () => <div className="depth-surface-skeleton" aria-hidden="true" />,
});

type AxisLabels = {
  x: string;
  y: string;
  z: string;
};

type TooltipLabels = {
  symbol: string;
  notional: string;
  impact: string;
  noRoute: string;
};

type Props = {
  title: string;
  caption: string;
  axes: AxisLabels;
  hint: string;
  fallbackNotice: string;
  fallbackTitle: string;
  fallbackCaption: string;
  tooltipLabels: TooltipLabels;
};

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

export function DepthSurface({
  title,
  caption,
  axes,
  hint,
  fallbackNotice,
  fallbackTitle,
  fallbackCaption,
  tooltipLabels,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  const [webglOk, setWebglOk] = useState(true);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    setWebglOk(probeWebGL());
    setReducedMotion(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el || !webglOk) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [webglOk]);

  if (!webglOk) {
    return (
      <figure className="chart-block">
        <h3>{title}</h3>
        <p className="depth-surface-fallback-notice muted">{fallbackNotice}</p>
        <ExitImpactBars title={fallbackTitle} caption={fallbackCaption} />
        <figcaption className="chart-caption">{caption}</figcaption>
      </figure>
    );
  }

  return (
    <figure className="chart-block depth-surface">
      <h3>{title}</h3>
      <div ref={containerRef} className="depth-surface-viewport">
        <div className="depth-surface-axis depth-surface-axis--x">{axes.x}</div>
        <div className="depth-surface-axis depth-surface-axis--y">{axes.y}</div>
        <div className="depth-surface-axis depth-surface-axis--z">{axes.z}</div>
        {visible ? (
          <DepthSurfaceScene tooltipLabels={tooltipLabels} reducedMotion={reducedMotion} />
        ) : (
          <div className="depth-surface-skeleton" aria-hidden="true" />
        )}
        <p className="depth-surface-hint muted">{hint}</p>
      </div>
      <figcaption className="chart-caption">{caption}</figcaption>
    </figure>
  );
}
