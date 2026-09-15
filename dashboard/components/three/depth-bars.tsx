"use client";

import { Edges } from "@react-three/drei";
import { useMemo } from "react";
import {
  depthHeightNormalized,
  depthSurfaceAssetLabels,
  depthSurfaceGrid,
  type DepthCell,
} from "@/data/findings";
import type { ThemeColors } from "@/components/charts/depth-surface/use-theme-colors";

const NOTIONAL_INDEX: Record<number, number> = {
  25000: 0,
  100000: 1,
  250000: 2,
};

export const BAR_WIDTH = 0.7;
export const BAR_DEPTH = 0.7;
export const X_GAP = 1.1;
export const Z_GAP = 1.2;
export const MAX_BAR_HEIGHT = 4;

type DepthBarProps = {
  cell: DepthCell;
  colors: ThemeColors;
  assetCount: number;
  interactive: boolean;
  opacityScale: number;
  hovered: boolean;
  onHover: (cell: DepthCell | null) => void;
};

function DepthBar({
  cell,
  colors,
  assetCount,
  interactive,
  opacityScale,
  hovered,
  onHover,
}: DepthBarProps) {
  const x = cell.assetIndex * X_GAP - (assetCount * X_GAP) / 2;
  const z = NOTIONAL_INDEX[cell.notional] * Z_GAP - Z_GAP;

  const pointerHandlers = interactive
    ? {
        onPointerOver: (e: { stopPropagation: () => void }) => {
          e.stopPropagation();
          onHover(cell);
        },
        onPointerOut: () => onHover(null),
      }
    : {};

  if (cell.noRoute) {
    const cageH = 0.6;
    const cageOpacity = (hovered ? 0.9 : 0.55) * opacityScale;
    return (
      <group position={[x, cageH / 2, z]}>
        <mesh {...pointerHandlers}>
          <boxGeometry args={[BAR_WIDTH, cageH, BAR_DEPTH]} />
          <meshBasicMaterial color={colors.text} wireframe transparent opacity={cageOpacity} />
        </mesh>
      </group>
    );
  }

  const h = Math.max(0.08, depthHeightNormalized(cell.impactPct ?? 0) * MAX_BAR_HEIGHT);
  const severity = cell.impactPct ?? 0;
  const baseOpacity = hovered ? 0.85 : 0.35 + Math.min(severity / 100, 1) * 0.4;
  const fillOpacity = baseOpacity * opacityScale;
  const fillColor = severity >= 20 ? colors.danger : colors.accent;

  return (
    <group position={[x, h / 2, z]}>
      <mesh {...pointerHandlers}>
        <boxGeometry args={[BAR_WIDTH, h, BAR_DEPTH]} />
        <meshBasicMaterial color={fillColor} transparent opacity={fillOpacity} />
        <Edges threshold={15} color={colors.text} />
      </mesh>
    </group>
  );
}

export function GroundGrid({ colors, assetCount }: { colors: ThemeColors; assetCount: number }) {
  const width = assetCount * X_GAP + 1;
  const depth = 3 * Z_GAP + 1;
  return (
    <gridHelper
      args={[Math.max(width, depth), Math.max(Math.round(assetCount), 4), colors.grid, colors.grid]}
      position={[0, 0.001, 0]}
    />
  );
}

type DepthBarsProps = {
  colors: ThemeColors;
  interactive?: boolean;
  opacityScale?: number;
  hovered?: DepthCell | null;
  onHover?: (cell: DepthCell | null) => void;
};

export function DepthBars({
  colors,
  interactive = false,
  opacityScale = 1,
  hovered = null,
  onHover = () => {},
}: DepthBarsProps) {
  const cells = useMemo(() => depthSurfaceGrid(), []);
  const assetCount = useMemo(() => depthSurfaceAssetLabels().length, []);

  return (
    <>
      <GroundGrid colors={colors} assetCount={assetCount} />
      {cells.map((cell) => (
        <DepthBar
          key={`${cell.symbol}-${cell.notional}`}
          cell={cell}
          colors={colors}
          assetCount={assetCount}
          interactive={interactive}
          opacityScale={opacityScale}
          hovered={hovered?.symbol === cell.symbol && hovered?.notional === cell.notional}
          onHover={onHover}
        />
      ))}
    </>
  );
}
