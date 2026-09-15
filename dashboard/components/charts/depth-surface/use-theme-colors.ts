"use client";

import { useMemo } from "react";
import * as THREE from "three";
import { useTheme } from "@/components/theme-provider";

function readCssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

export type ThemeColors = {
  text: THREE.Color;
  panel: THREE.Color;
  muted: THREE.Color;
  danger: THREE.Color;
  accent: THREE.Color;
  grid: THREE.Color;
  bg: THREE.Color;
};

export function useThemeColors(): ThemeColors {
  const { resolved } = useTheme();

  return useMemo(() => {
    const pick = (v: string) => new THREE.Color(v);
    return {
      text: pick(readCssVar("--text")),
      panel: pick(readCssVar("--panel")),
      muted: pick(readCssVar("--muted")),
      danger: pick(readCssVar("--danger")),
      accent: pick(readCssVar("--accent")),
      grid: pick(readCssVar("--chart-grid")),
      bg: pick(readCssVar("--bg")),
    };
  }, [resolved]);
}
