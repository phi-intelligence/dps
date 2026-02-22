"use client";

import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { Environment, useGLTF } from "@react-three/drei";
import * as THREE from "three";

function HeroLogo({ url }: { url: string }) {
  const { scene } = useGLTF(url);
  const clone = scene.clone();
  clone.traverse((child) => {
    if (child instanceof THREE.Mesh) {
      child.castShadow = false;
      child.receiveShadow = false;
    }
  });
  return (
    <primitive
      object={clone}
      scale={[2.2, 2.2, 2.2]}
      rotation={[0, Math.PI, 0]}
    />
  );
}

function SceneContent({ modelPath }: { modelPath: string | null }) {
  if (!modelPath) return null;
  return (
    <>
      <ambientLight intensity={0.85} />
      <directionalLight position={[4, 5, 5]} intensity={1.4} />
      <directionalLight position={[-3, 3, 4]} intensity={0.6} />
      <pointLight position={[2, 2, 4]} intensity={0.9} color="#ffffff" />
      <pointLight position={[-2, 1, 3]} intensity={0.5} color="#fef3c7" />
      <Suspense fallback={null}>
        <HeroLogo url={modelPath} />
      </Suspense>
      <Environment preset="studio" background={false} />
    </>
  );
}

interface Hero3DSceneProps {
  /** Path to GLB logo in public folder, e.g. /dps.glb */
  modelPath?: string | null;
  className?: string;
}

export default function Hero3DScene({ modelPath = null, className = "" }: Hero3DSceneProps) {
  return (
    <div
      className={`w-full aspect-square max-h-[min(70vh,520px)] overflow-hidden ${className}`}
      style={{ background: "transparent" }}
    >
      <Canvas
        camera={{ position: [0, 0, 5.5], fov: 40 }}
        gl={{
          antialias: true,
          alpha: true,
          premultipliedAlpha: false,
        }}
        style={{ background: "transparent" }}
        onCreated={({ gl, scene }) => {
          gl.setClearColor(0x000000, 0);
          scene.background = null;
        }}
      >
        <SceneContent modelPath={modelPath ?? null} />
      </Canvas>
    </div>
  );
}
