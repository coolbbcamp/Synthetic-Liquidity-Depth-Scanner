"use client";

import { Edges, Line, OrbitControls } from "@react-three/drei";
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
  brandColor,
}: {
  position: [number, number, number];
  index: number;
  status: RoadmapStageStatus;
  colors: ReturnType<typeof useThemeColors>;
  brandColor: THREE.Color;
}) {
  const [x, y, z] = position;
  const blockH = monolithHeight(index);
  const groupY = y + PEDESTAL_H / 2;

  const accent = status === "complete" ? brandColor : colors.accent;
  const isPlanned = status === "planned";

  return (
    <group position={[x, groupY, z]}>
      {/* Pedestal */}
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[PEDESTAL_W + 0.2, PEDESTAL_H, PEDESTAL_D + 0.2]} />
        <meshStandardMaterial
          color={colors.panel}
          metalness={0.35}
          roughness={0.65}
          transparent
          opacity={isPlanned ? 0.35 : 0.7}
        />
        <Edges threshold={15} color={colors.grid} />
      </mesh>

      {/* Monolith */}
      <group position={[0, PEDESTAL_H / 2 + blockH / 2, 0]}>
        <mesh>
          <boxGeometry args={[PEDESTAL_W, blockH, PEDESTAL_D]} />
          <meshStandardMaterial
            color={isPlanned ? colors.muted : accent}
            metalness={isPlanned ? 0.1 : 0.55}
            roughness={isPlanned ? 0.85 : 0.28}
            transparent
            opacity={isPlanned ? 0.22 : status === "complete" ? 0.95 : 0.85}
            emissive={isPlanned ? colors.muted : accent}
            emissiveIntensity={isPlanned ? 0.08 : status === "complete" ? 0.45 : 0.3}
          />
          <Edges threshold={12} color={isPlanned ? colors.muted : colors.text} />
        </mesh>

        {/* Top highlight cap */}
        {!isPlanned && (
          <mesh position={[0, blockH / 2 + 0.02, 0]}>
            <boxGeometry args={[PEDESTAL_W * 0.92, 0.06, PEDESTAL_D * 0.92]} />
            <meshStandardMaterial
              color={accent}
              emissive={accent}
              emissiveIntensity={0.5}
              metalness={0.8}
              roughness={0.15}
            />
          </mesh>
        )}
      </group>

      {/* Base glow ring */}
      {!isPlanned && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, PEDESTAL_H / 2 + 0.01, 0]}>
          <ringGeometry args={[PEDESTAL_W * 0.45, PEDESTAL_W * 0.62, 32]} />
          <meshBasicMaterial
            color={accent}
            transparent
            opacity={status === "complete" ? 0.45 : 0.3}
            side={THREE.DoubleSide}
          />
        </mesh>
      )}

      {/* Active pulse pillar */}
      {status === "active" && (
        <pointLight position={[0, blockH * 0.6, 0]} intensity={0.8} color={accent} distance={5} />
      )}
    </group>
  );
}

function ConnectingRamps({
  positions,
  colors,
  brandColor,
}: {
  positions: [number, number, number][];
  colors: ReturnType<typeof useThemeColors>;
  brandColor: THREE.Color;
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
        color: i === 0 ? brandColor : colors.accent,
        opacity: 0.35 + i * 0.05,
      });
    }
    return items;
  }, [positions, colors.accent, brandColor]);

  return (
    <>
      {ramps.map((ramp, i) => (
        <mesh key={i} position={ramp.position} rotation={ramp.rotation}>
          <boxGeometry args={[0.14, ramp.length, 0.5]} />
          <meshStandardMaterial
            color={ramp.color}
            metalness={0.6}
            roughness={0.35}
            transparent
            opacity={ramp.opacity}
            emissive={ramp.color}
            emissiveIntensity={0.15}
          />
        </mesh>
      ))}
    </>
  );
}

function PathLine({
  positions,
  brandColor,
}: {
  positions: [number, number, number][];
  brandColor: THREE.Color;
}) {
  const points = useMemo(() => {
    return positions.map((pos, i) => platformTop(pos, monolithHeight(i)));
  }, [positions]);

  return (
    <Line
      points={points}
      color={brandColor}
      lineWidth={1.5}
      transparent
      opacity={0.5}
      dashed={false}
    />
  );
}

function RoadmapSceneContent({ stages, animate }: SceneProps) {
  const colors = useThemeColors();
  const { scene } = useThree();
  const [tabHidden, setTabHidden] = useState(false);
  const brandColor = useMemo(
    () => new THREE.Color(readCssVar("--brand")),
    [colors.bg, colors.accent, colors.text],
  );

  const positions = useMemo(
    () => stages.map((_, index) => stagePosition(index)),
    [stages],
  );

  useEffect(() => {
    scene.fog = new THREE.FogExp2(colors.bg.getHex(), 0.018);
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
      <ambientLight intensity={0.5} />
      <directionalLight position={[8, 14, 6]} intensity={1} castShadow={false} />
      <directionalLight position={[-6, 8, -4]} intensity={0.4} color={colors.accent} />
      <pointLight position={[0, 8, 4]} intensity={0.65} color={brandColor} />

      <group position={[0, -0.2, -1]} scale={1.15}>
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]}>
          <planeGeometry args={[24, 18]} />
          <meshStandardMaterial
            color={colors.bg}
            metalness={0.7}
            roughness={0.85}
            transparent
            opacity={0.25}
          />
        </mesh>
        <gridHelper
          args={[20, 24, colors.grid, colors.grid]}
          position={[0, 0.001, 0]}
        />

        <PathLine positions={positions} brandColor={brandColor} />
        <ConnectingRamps positions={positions} colors={colors} brandColor={brandColor} />

        {stages.map((stage, index) => (
          <RoadmapMonolith
            key={stage.id}
            position={positions[index]}
            index={index}
            status={resolveStageStatus(stage)}
            colors={colors}
            brandColor={brandColor}
          />
        ))}
      </group>

      <OrbitControls
        enablePan={false}
        enableZoom={false}
        enableRotate={false}
        autoRotate={animate && !tabHidden}
        autoRotateSpeed={0.1}
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
      camera={{ position: [10, 7, 16], fov: 40, near: 0.1, far: 80 }}
    >
      <RoadmapSceneContent stages={stages} animate={animate} />
    </Canvas>
  );
}
