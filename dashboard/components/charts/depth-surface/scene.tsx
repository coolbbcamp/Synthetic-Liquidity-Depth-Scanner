"use client";

import { Html, OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useState } from "react";
import { type DepthCell } from "@/data/findings";
import { DepthBars, MAX_BAR_HEIGHT } from "@/components/three/depth-bars";
import { useThemeColors } from "./use-theme-colors";

type TooltipLabels = {
  symbol: string;
  notional: string;
  impact: string;
  noRoute: string;
};

type SceneProps = {
  tooltipLabels: TooltipLabels;
  reducedMotion: boolean;
};

function DepthScene({ tooltipLabels, reducedMotion }: SceneProps) {
  const colors = useThemeColors();
  const [hovered, setHovered] = useState<DepthCell | null>(null);

  return (
    <>
      <color attach="background" args={["transparent"]} />
      <ambientLight intensity={0.6} />
      <directionalLight position={[5, 8, 5]} intensity={0.35} />
      <DepthBars
        colors={colors}
        interactive
        opacityScale={1}
        hovered={hovered}
        onHover={setHovered}
      />
      {hovered && (
        <Html position={[0, MAX_BAR_HEIGHT + 1.2, 0]} center style={{ pointerEvents: "none" }}>
          <div className="depth-surface-tooltip">
            <strong>{hovered.symbol}</strong>
            <span>
              {tooltipLabels.notional}: ${(hovered.notional / 1000).toFixed(0)}k
            </span>
            <span>
              {tooltipLabels.impact}:{" "}
              {hovered.noRoute
                ? tooltipLabels.noRoute
                : `${hovered.impactPct?.toFixed(2)}%`}
            </span>
          </div>
        </Html>
      )}
      <OrbitControls
        enablePan={false}
        enableDamping
        dampingFactor={0.08}
        minDistance={8}
        maxDistance={28}
        minPolarAngle={Math.PI / 6}
        maxPolarAngle={Math.PI / 2.2}
        autoRotate={!reducedMotion}
        autoRotateSpeed={0.35}
      />
    </>
  );
}

export default function DepthSurfaceScene({
  tooltipLabels,
  reducedMotion,
}: SceneProps) {
  return (
    <Canvas
      className="depth-surface-canvas"
      gl={{ alpha: true, antialias: true }}
      orthographic
      camera={{ position: [12, 10, 12], zoom: 42, near: 0.1, far: 200 }}
    >
      <DepthScene tooltipLabels={tooltipLabels} reducedMotion={reducedMotion} />
    </Canvas>
  );
}
