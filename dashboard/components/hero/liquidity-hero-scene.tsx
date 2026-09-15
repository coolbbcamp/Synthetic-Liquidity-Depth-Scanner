"use client";

import { OrbitControls } from "@react-three/drei";
import { Canvas, useThree } from "@react-three/fiber";
import { useEffect, useState } from "react";
import * as THREE from "three";
import { DepthBars } from "@/components/three/depth-bars";
import { useThemeColors } from "@/components/charts/depth-surface/use-theme-colors";

type SceneProps = {
  animate: boolean;
};

function HeroDepthScene({ animate }: SceneProps) {
  const colors = useThemeColors();
  const { scene } = useThree();
  const [tabHidden, setTabHidden] = useState(false);

  useEffect(() => {
    scene.fog = new THREE.Fog(colors.bg.getHex(), 28, 55);
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
      <directionalLight position={[6, 12, 4]} intensity={0.7} />
      <directionalLight position={[-4, 6, -8]} intensity={0.35} color={colors.accent} />
      <group position={[0, -0.5, 0]} scale={1.8}>
        <DepthBars colors={colors} interactive={false} opacityScale={0.92} />
      </group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]}>
        <planeGeometry args={[80, 80]} />
        <meshBasicMaterial color={colors.bg} transparent opacity={0.05} />
      </mesh>
      <OrbitControls
        enablePan={false}
        enableZoom={false}
        enableRotate={false}
        autoRotate={animate && !tabHidden}
        autoRotateSpeed={0.15}
        target={[0, 1.2, 0]}
      />
    </>
  );
}

export default function LiquidityHeroScene({ animate }: SceneProps) {
  return (
    <Canvas
      className="home-hero-canvas"
      style={{ background: "transparent" }}
      gl={{ alpha: true, antialias: true, powerPreference: "high-performance" }}
      dpr={[1, 1.5]}
      camera={{ position: [0, 7, 16], fov: 42, near: 0.1, far: 100 }}
    >
      <HeroDepthScene animate={animate} />
    </Canvas>
  );
}
