export type SweepAsset = {
  symbol: string;
  mcapM: number;
  tvlK: number;
  tvlPct: number;
  impact25k: number | null;
  impact100k: number | null;
  impact250k: number | null;
};

export type CliffPoint = {
  notional: number;
  executionPrice: number;
  route: string;
};

export const PROVENANCE = "2026-09-13T14:15:00Z";

export const sweepAssets: SweepAsset[] = [
  { symbol: "SPYx", mcapM: 72.7, tvlK: 3884, tvlPct: 5.34, impact25k: -0.03, impact100k: -0.09, impact250k: -0.4 },
  { symbol: "NVDAx", mcapM: 68.9, tvlK: 1850, tvlPct: 2.69, impact25k: -0.02, impact100k: -0.09, impact250k: -0.35 },
  { symbol: "TSLAx", mcapM: 83.5, tvlK: 1349, tvlPct: 1.62, impact25k: -0.02, impact100k: -0.16, impact250k: -0.92 },
  { symbol: "QQQx", mcapM: 59.6, tvlK: 1767, tvlPct: 2.96, impact25k: -0.03, impact100k: -0.15, impact250k: -1.02 },
  { symbol: "SPCXx", mcapM: 83.3, tvlK: 914, tvlPct: 1.1, impact25k: -0.08, impact100k: -0.24, impact250k: -2.27 },
  { symbol: "AAPLx", mcapM: 51.1, tvlK: 835, tvlPct: 1.63, impact25k: -0.25, impact100k: -0.81, impact250k: -2.58 },
  { symbol: "CRCLx", mcapM: 73.6, tvlK: 1934, tvlPct: 2.63, impact25k: -0.04, impact100k: -0.18, impact250k: -0.95 },
  { symbol: "MSFTx", mcapM: 51.9, tvlK: 418, tvlPct: 0.81, impact25k: -0.45, impact100k: -2.01, impact250k: -7.71 },
  { symbol: "GMEx", mcapM: 15.5, tvlK: 316, tvlPct: 2.03, impact25k: -0.72, impact100k: -1.98, impact250k: null },
  { symbol: "GOOGLx", mcapM: 54.3, tvlK: 305, tvlPct: 0.56, impact25k: -0.4, impact100k: -1.88, impact250k: -23.06 },
  { symbol: "GLDx", mcapM: 46.4, tvlK: 300, tvlPct: 0.65, impact25k: -0.3, impact100k: -2.07, impact250k: null },
  { symbol: "METAx", mcapM: 46.5, tvlK: 204, tvlPct: 0.44, impact25k: -0.98, impact100k: -5.14, impact250k: -49.9 },
  { symbol: "MCDx", mcapM: 14.1, tvlK: 341, tvlPct: 2.42, impact25k: -0.48, impact100k: -2.77, impact250k: null },
  { symbol: "PLTRx", mcapM: 24.3, tvlK: 190, tvlPct: 0.78, impact25k: -0.6, impact100k: -8.01, impact250k: null },
  { symbol: "HOODx", mcapM: 64.5, tvlK: 358, tvlPct: 0.56, impact25k: -0.41, impact100k: -1.66, impact250k: -6.67 },
  { symbol: "MSTRx", mcapM: 61.3, tvlK: 713, tvlPct: 1.16, impact25k: -0.09, impact100k: -0.59, impact250k: -2.93 },
  { symbol: "STRCx", mcapM: 49.9, tvlK: 395, tvlPct: 0.79, impact25k: -0.03, impact100k: -0.29, impact250k: -99.97 },
];

export const correlations = {
  absoluteTvlRho: -0.92,
  tvlMcapRho: -0.66,
};

export const strcxCliffSeries: CliffPoint[] = [
  { notional: 25000, executionPrice: 0.993, route: "Byreal+Raydium CLMM" },
  { notional: 50000, executionPrice: 0.992, route: "Byreal+Raydium CLMM" },
  { notional: 100000, executionPrice: 0.997, route: "Byreal+Raydium CLMM" },
  { notional: 150000, executionPrice: 0.993, route: "Byreal+Raydium CLMM" },
  { notional: 200000, executionPrice: 0.04, route: "Raydium CP+Meteora DAMM v2+HumidiFi" },
];

export const stonkCapVsRecovery = {
  symbol: "STONK",
  printedMcapUsd: 214_693_012,
  exit1MRecoveryPct: 85.27,
  exit100kRecoveryPct: 98.29,
};

export const noRouteWalls = {
  noRouteAt250kCount: 6,
  sweepTotal: 18,
  ftrNoRouteAboveUsd: 25_000,
};

export const impersonation = {
  hoodxFakeCount: 20,
  note: "One token embeds the genuine mint address inside its own name field to defeat string matching.",
};

export function exitImpactAt100kWorstFirst() {
  return sweepAssets
    .filter((a) => a.impact100k != null)
    .map((a) => ({
      symbol: a.symbol,
      impact: Math.abs(a.impact100k!),
    }))
    .sort((a, b) => b.impact - a.impact);
}

export function tvlScatterData() {
  return sweepAssets
    .filter((a) => a.impact100k != null)
    .map((a) => ({
      symbol: a.symbol,
      tvlPct: a.tvlPct,
      impact: Math.abs(a.impact100k!),
    }));
}

export type DepthNotional = 25000 | 100000 | 250000;

export type DepthCell = {
  symbol: string;
  notional: DepthNotional;
  impactPct: number | null;
  noRoute: boolean;
  assetIndex: number;
};

const DEPTH_NOTIONALS: DepthNotional[] = [25000, 100000, 250000];

function impactForNotional(asset: SweepAsset, notional: DepthNotional): number | null {
  if (notional === 25000) return asset.impact25k;
  if (notional === 100000) return asset.impact100k;
  return asset.impact250k;
}

/** Flatten sweep into 51 cells, assets ordered best-to-worst by |impact@100k|. */
export function depthSurfaceGrid(): DepthCell[] {
  const ordered = [...sweepAssets].sort(
    (a, b) => Math.abs(a.impact100k ?? 0) - Math.abs(b.impact100k ?? 0),
  );

  const cells: DepthCell[] = [];
  ordered.forEach((asset, assetIndex) => {
    for (const notional of DEPTH_NOTIONALS) {
      const raw = impactForNotional(asset, notional);
      cells.push({
        symbol: asset.symbol,
        notional,
        impactPct: raw == null ? null : Math.abs(raw),
        noRoute: raw == null,
        assetIndex,
      });
    }
  });
  return cells;
}

/** Log-scaled height 0–1 for bar geometry. */
export function depthHeightNormalized(impactPct: number): number {
  const maxLog = Math.log10(1 + 100);
  return Math.log10(1 + impactPct) / maxLog;
}

export function depthSurfaceAssetLabels(): string[] {
  return [...sweepAssets]
    .sort((a, b) => Math.abs(a.impact100k ?? 0) - Math.abs(b.impact100k ?? 0))
    .map((a) => a.symbol);
}
