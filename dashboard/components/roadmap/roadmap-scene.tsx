"use client";

import { Line, OrbitControls } from "@react-three/drei";
import { Canvas, useThree } from "@react-three/fiber";
import { useEffect, useMemo, useState } from "react";
import * as THREE from "three";
import { useThemeColors } from "@/components/charts/depth-surface/use-theme-colors";
import {
  monolithHeight,
  resolveStageStatus,
  stagePosition,
  type RoadmapStage,
  type RoadmapStageStatus,
} from "./types";

type SceneProps = {
  stages: RoadmapStage[];
  animate: boolean;
};

const PEDESTAL_W = 2.4;
const PEDESTAL_H = 0.18;
const PEDESTAL_D = 1.5;

function readCssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function platformTop(position: [number, number, number], blockH: number): THREE.Vector3 {
  const [x, y, z] = position;
  return new THREE.Vector3(x, y + PEDESTAL_H + blockH, z);
}

function RoadmapMonolith({
  position,
  index,
  status,
  colors,
  brandMuted,
}: {
  position: [number, number, number];
  index: number;
  status: RoadmapStageStatus;
  colors: ReturnType<typeof useThemeColors>;
  brandMuted: THREE.Color;
}) {
  const [x, y, z] = position;
  const blockH = monolithHeight(index);
  const groupY = y + PEDESTAL_H / 2;

  const accent = status === "complete" ? brandMuted : colors.accent;
  const isPlanned = status === "planned";
  const emissiveIntensity =
    status === "complete" ? 0.12 : status === "active" ? 0.08 : 0.03;

  return (
    <group position={[x, groupY, z]}>
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[PEDESTAL_W + 0.2, PEDESTAL_H, PEDESTAL_D + 0.2]} />
        <meshStandardMaterial
          color={colors.panel}
          metalness={0.2}
          roughness={0.75}
          transparent
          opacity={isPlanned ? 0.25 : 0.55}
        />
      </mesh>

      <group position={[0, PEDESTAL_H / 2 + blockH / 2, 0]}>
        <mesh>
          <boxGeometry args={[PEDESTAL_W, blockH, PEDESTAL_D]} />
          <meshStandardMaterial
            color={isPlanned ? colors.muted : colors.panel}
            metalness={isPlanned ? 0.1 : 0.22}
            roughness={isPlanned ? 0.9 : 0.68}
            transparent
            opacity={isPlanned ? 0.18 : status === "complete" ? 0.72 : 0.65}
            emissive={isPlanned ? colors.muted : accent}
            emissiveIntensity={emissiveIntensity}
          />
        </mesh>

        {!isPlanned && (
          <mesh position={[0, blockH / 2 + 0.02, 0]}>
            <boxGeometry args={[PEDESTAL_W * 0.92, 0.05, PEDESTAL_D * 0.92]} />
            <meshStandardMaterial
              color={accent}
              emissive={accent}
              emissiveIntensity={0.12}
              metalness={0.35}
              roughness={0.55}
              transparent
              opacity={0.85}
            />
          </mesh>
        )}
      </group>

      {!isPlanned && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, PEDESTAL_H / 2 + 0.01, 0]}>
          <ringGeometry args={[PEDESTAL_W * 0.45, PEDESTAL_W * 0.58, 32]} />
          <meshBasicMaterial
            color={accent}
            transparent
            opacity={status === "complete" ? 0.18 : 0.12}
            side={THREE.DoubleSide}
          />
        </mesh>
      )}
    </group>
  );
}

function ConnectingRamps({
  positions,
  colors,
  brandMuted,
}: {
  positions: [number, number, number][];
  colors: ReturnType<typeof useThemeColors>;
  brandMuted: THREE.Color;
}) {
  const ramps = useMemo(() => {
    const items: {
      position: THREE.Vector3;
      rotation: THREE.Euler;
      length: number;
      color: THREE.Color;
      opacity: number;
    }[] = [];

    for (let i = 0; i < positions.length - 1; i++) {
      const h1 = monolithHeight(i);
      const h2 = monolithHeight(i + 1);
      const start = platformTop(positions[i], h1);
      const end = platformTop(positions[i + 1], h2);
      const mid = start.clone().add(end).multiplyScalar(0.5);
      const dir = end.clone().sub(start);
      const length = dir.length();
      const rotation = new THREE.Euler();
      const quaternion = new THREE.Quaternion().setFromUnitVectors(
        new THREE.Vector3(0, 1, 0),
        dir.clone().normalize(),
      );
      rotation.setFromQuaternion(quaternion);
      items.push({
        position: mid,
        rotation,
        length,
        color: i === 0 ? brandMuted : colors.accent,
        opacity: 0.12 + i * 0.03,
      });
    }
    return items;
  }, [positions, colors.accent, brandMuted]);

  return (
    <>
      {ramps.map((ramp, i) => (
        <mesh key={i} position={ramp.position} rotation={ramp.rotation}>
          <boxGeometry args={[0.12, ramp.length, 0.4]} />
          <meshBasicMaterial color={ramp.color} transparent opacity={ramp.opacity} />
        </mesh>
      ))}
    </>
  );
}

function PathLine({
  positions,
  brandMuted,
}: {
  positions: [number, number, number][];
  brandMuted: THREE.Color;
}) {
  const points = useMemo(() => {
    return positions.map((pos, i) => platformTop(pos, monolithHeight(i)));
  }, [positions]);

  return (
    <Line
      points={points}
      color={brandMuted}
      lineWidth={1}
      transparent
      opacity={0.25}
      dashed={false}
    />
  );
}

function RoadmapSceneContent({ stages, animate }: SceneProps) {
  const colors = useThemeColors();
  const { scene } = useThree();
  const [tabHidden, setTabHidden] = useState(false);
  const brandMuted = useMemo(
    () => new THREE.Color(readCssVar("--brand-muted") || readCssVar("--brand")),
    [colors.bg, colors.accent, colors.text],
  );

  const positions = useMemo(
    () => stages.map((_, index) => stagePosition(index)),
    [stages],
  );

  useEffect(() => {
    scene.fog = new THREE.Fog(colors.bg.getHex(), 18, 42);
    return () => {
      scene.fog = null;
    };
  }, [colors.bg, scene]);

  useEffect(() => {
    const onVisibility = () => setTabHidden(document.hidden);
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, []);

  return (
    <>
      <ambientLight intensity={0.55} />
      <directionalLight position={[6, 12, 4]} intensity={0.6} castShadow={false} />
      <directionalLight position={[-4, 6, -8]} intensity={0.2} color={colors.accent} />

      <group position={[0, -0.2, -1]} scale={1}>
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]}>
          <planeGeometry args={[32, 24]} />
          <meshBasicMaterial color={colors.bg} transparent opacity={0.06} />
        </mesh>

        <PathLine positions={positions} brandMuted={brandMuted} />
        <ConnectingRamps positions={positions} colors={colors} brandMuted={brandMuted} />

        {stages.map((stage, index) => (
          <RoadmapMonolith
            key={stage.id}
            position={positions[index]}
            index={index}
            status={resolveStageStatus(stage)}
            colors={colors}
            brandMuted={brandMuted}
          />
        ))}
      </group>

      <OrbitControls
        enablePan={false}
        enableZoom={false}
        enableRotate={false}
        autoRotate={animate && !tabHidden}
        autoRotateSpeed={0.05}
        target={[0, 2, -2]}
      />
    </>
  );
}

export default function RoadmapScene({ stages, animate }: SceneProps) {
  return (
    <Canvas
      className="roadmap-backdrop-canvas"
      style={{ background: "transparent" }}
      gl={{ alpha: true, antialias: true, powerPreference: "high-performance" }}
      dpr={[1, 1.5]}
      camera={{ position: [12, 8, 18], fov: 40, near: 0.1, far: 80 }}
    >
      <RoadmapSceneContent stages={stages} animate={animate} />
    </Canvas>
  );
}
