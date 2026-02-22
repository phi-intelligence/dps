"use client";

import { useRef, useMemo, Suspense } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment } from "@react-three/drei";
import * as THREE from "three";

// ═══ Material Colors ═══
const COPPER = "#B87333";
const COPPER_DARK = "#7A5230";
const BRASS = "#C9B037";
const RED = "#DC2626";
const BLUE = "#1C448E";

// ═══════════════════════════════════════
// PipeRun – tube along a CatmullRom spline
// ═══════════════════════════════════════
function PipeRun({
  points,
  radius = 0.06,
  color = COPPER,
  metalness = 0.9,
  roughness = 0.15,
}: {
  points: [number, number, number][];
  radius?: number;
  color?: string;
  metalness?: number;
  roughness?: number;
}) {
  const geometry = useMemo(() => {
    const vecs = points.map(([x, y, z]) => new THREE.Vector3(x, y, z));
    const curve = new THREE.CatmullRomCurve3(vecs, false, "centripetal");
    return new THREE.TubeGeometry(curve, Math.max(points.length * 20, 48), radius, 12, false);
  }, [points, radius]);

  return (
    <mesh geometry={geometry}>
      <meshStandardMaterial color={color} metalness={metalness} roughness={roughness} />
    </mesh>
  );
}

// ═══════════════════════════════════════
// Flange – brass ring at pipe junctions
// ═══════════════════════════════════════
function Flange({
  position,
  axis,
  pipeRadius,
}: {
  position: [number, number, number];
  axis: "x" | "y" | "z";
  pipeRadius: number;
}) {
  const rotation: [number, number, number] =
    axis === "x"
      ? [0, 0, Math.PI / 2]
      : axis === "z"
        ? [Math.PI / 2, 0, 0]
        : [0, 0, 0];

  return (
    <mesh position={position} rotation={rotation}>
      <torusGeometry args={[pipeRadius * 1.5, pipeRadius * 0.35, 8, 24]} />
      <meshStandardMaterial color={BRASS} metalness={0.85} roughness={0.25} />
    </mesh>
  );
}

// ═══════════════════════════════════════
// Valve – red wheel valve decoration
// ═══════════════════════════════════════
function Valve({
  position,
  rotation,
  scale = 1,
}: {
  position: [number, number, number];
  rotation: [number, number, number];
  scale?: number;
}) {
  const wheelRef = useRef<THREE.Group>(null);

  useFrame(({ clock }) => {
    if (wheelRef.current) {
      wheelRef.current.rotation.z = Math.sin(clock.getElapsedTime() * 0.3) * 0.5;
    }
  });

  return (
    <group position={position} rotation={rotation} scale={scale}>
      {/* Stem */}
      <mesh>
        <cylinderGeometry args={[0.025, 0.025, 0.12, 8]} />
        <meshStandardMaterial color={BRASS} metalness={0.85} roughness={0.25} />
      </mesh>
      {/* Wheel (rotates) */}
      <group ref={wheelRef} position={[0, 0.1, 0]}>
        <mesh>
          <torusGeometry args={[0.07, 0.01, 6, 20]} />
          <meshStandardMaterial color={RED} metalness={0.7} roughness={0.3} />
        </mesh>
        {[0, Math.PI / 3, (Math.PI * 2) / 3].map((angle, i) => (
          <mesh key={i} rotation={[0, 0, angle]}>
            <boxGeometry args={[0.14, 0.006, 0.006]} />
            <meshStandardMaterial color={RED} metalness={0.7} roughness={0.3} />
          </mesh>
        ))}
      </group>
    </group>
  );
}

// ═══════════════════════════════════════
// PressureGauge – small gauge at junctions
// ═══════════════════════════════════════
function PressureGauge({
  position,
  rotation,
}: {
  position: [number, number, number];
  rotation: [number, number, number];
}) {
  return (
    <group position={position} rotation={rotation}>
      <mesh>
        <cylinderGeometry args={[0.06, 0.06, 0.025, 16]} />
        <meshStandardMaterial color="#333333" metalness={0.9} roughness={0.1} />
      </mesh>
      <mesh position={[0, 0.014, 0]}>
        <circleGeometry args={[0.05, 16]} />
        <meshStandardMaterial color="#EEEEEE" metalness={0} roughness={0.8} />
      </mesh>
      <mesh position={[0, 0.015, 0]} rotation={[0, 0, -Math.PI / 4]}>
        <boxGeometry args={[0.04, 0.003, 0.003]} />
        <meshStandardMaterial color={RED} />
      </mesh>
    </group>
  );
}

// ═══════════════════════════════════════
// FlowParticle – glowing sphere along path
// ═══════════════════════════════════════
function FlowParticle({
  points,
  color,
  speed,
  delay,
  size = 0.035,
}: {
  points: [number, number, number][];
  color: string;
  speed: number;
  delay: number;
  size?: number;
}) {
  const ref = useRef<THREE.Mesh>(null);
  const curve = useMemo(
    () =>
      new THREE.CatmullRomCurve3(
        points.map(([x, y, z]) => new THREE.Vector3(x, y, z)),
        false,
        "centripetal"
      ),
    [points]
  );

  useFrame(({ clock }) => {
    if (!ref.current) return;
    const t = (((clock.getElapsedTime() * speed + delay) % 1) + 1) % 1;
    ref.current.position.copy(curve.getPointAt(t));
  });

  return (
    <mesh ref={ref}>
      <sphereGeometry args={[size, 8, 8]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={5}
        toneMapped={false}
      />
    </mesh>
  );
}

// ═══════════════════════════════════════
// CameraRig – subtle drift animation
// ═══════════════════════════════════════
function CameraRig() {
  useFrame(({ clock, camera }) => {
    const t = clock.getElapsedTime();
    camera.position.x = Math.sin(t * 0.05) * 0.4;
    camera.position.y = Math.cos(t * 0.04) * 0.25;
    camera.lookAt(0, 0, -2);
  });
  return null;
}

// ═══════════════════════════════════════
// PipeScene – full 3D pipe network
// ═══════════════════════════════════════
function PipeScene() {
  return (
    <>
      {/* ── BACKGROUND LAYER (z ≈ -4) ── */}
      <PipeRun points={[[-12, 2.5, -4], [12, 2.5, -4]]} radius={0.14} color={COPPER_DARK} roughness={0.25} />
      <PipeRun points={[[-12, -1.5, -4], [12, -1.5, -4]]} radius={0.14} color={COPPER_DARK} roughness={0.25} />
      <PipeRun points={[[-6, -6, -4], [-6, 6, -4]]} radius={0.12} color={COPPER_DARK} roughness={0.25} />
      <PipeRun points={[[6, -6, -4], [6, 6, -4]]} radius={0.12} color={COPPER_DARK} roughness={0.25} />
      <PipeRun points={[[0, -6, -3.5], [0, 6, -3.5]]} radius={0.1} color={COPPER_DARK} roughness={0.3} />

      {/* ── MID LAYER: HORIZONTAL TRUNKS (z ≈ -2) ── */}
      <PipeRun
        points={[
          [-10, 3.5, -2], [-4.3, 3.5, -2], [-4, 3.5, -2],
          [-3.8, 3.5, -0.5], [3.8, 3.5, -0.5],
          [4, 3.5, -2], [4.3, 3.5, -2], [10, 3.5, -2],
        ]}
        radius={0.09}
      />
      <PipeRun points={[[-10, 0, -1.5], [10, 0, -1.5]]} radius={0.1} />
      <PipeRun points={[[-10, -3, -2], [10, -3, -2]]} radius={0.08} />
      <PipeRun points={[[-10, -1, -2.5], [10, -0.5, -2.5]]} radius={0.06} roughness={0.2} />

      {/* ── MID LAYER: VERTICAL RISERS ── */}
      <PipeRun points={[[-5, -5, -1.8], [-5, 5, -1.8]]} radius={0.07} />
      <PipeRun points={[[0, -5, -1.5], [0, 5, -1.5]]} radius={0.08} />
      <PipeRun points={[[5, -5, -1.8], [5, 5, -1.8]]} radius={0.07} />
      <PipeRun points={[[-2.5, -4, -2], [-2.5, 4, -2]]} radius={0.05} />
      <PipeRun points={[[2.5, -4, -1.8], [2.5, 4, -1.8]]} radius={0.05} />

      {/* ── CROSS-CONNECTIONS (bends into foreground) ── */}
      <PipeRun
        points={[
          [-5, 1.8, -1.8], [-4.8, 1.8, -1.8], [-4.5, 1.8, 0],
          [-2.5, 1.8, 0], [-2.2, 1.8, -1.5], [-2, 1.8, -1.5],
        ]}
        radius={0.045}
      />
      <PipeRun
        points={[
          [5, 1.8, -1.8], [4.8, 1.8, -1.8], [4.5, 1.8, 0],
          [2.5, 1.8, 0], [2.2, 1.8, -1.5], [2, 1.8, -1.5],
        ]}
        radius={0.045}
      />
      <PipeRun
        points={[
          [-3, -1.5, -1.5], [-2.8, -1.5, -1.5], [-2.5, -1.5, 0.5],
          [2.5, -1.5, 0.5], [2.8, -1.5, -1.5], [3, -1.5, -1.5],
        ]}
        radius={0.045}
      />

      {/* ── FOREGROUND ACCENT PIPES (z ≈ 1) ── */}
      <PipeRun points={[[-7.5, -3.5, 1], [-7.5, 3.5, 1]]} radius={0.03} roughness={0.1} />
      <PipeRun points={[[8, -3, 1.5], [8, 3.5, 1.5]]} radius={0.025} roughness={0.1} />
      <PipeRun
        points={[
          [-7.5, 0, 1], [-7.3, 0, 1], [-7, 0, 0],
          [-5.3, 0, -1.5], [-5, 0, -1.8],
        ]}
        radius={0.035}
      />

      {/* ── FLANGES ── */}
      <Flange position={[-3, 0, -1.5]} axis="x" pipeRadius={0.1} />
      <Flange position={[3, 0, -1.5]} axis="x" pipeRadius={0.1} />
      <Flange position={[0, 2, -1.5]} axis="y" pipeRadius={0.08} />
      <Flange position={[0, -2, -1.5]} axis="y" pipeRadius={0.08} />
      <Flange position={[-5, 3.5, -1.8]} axis="y" pipeRadius={0.07} />
      <Flange position={[5, 3.5, -1.8]} axis="y" pipeRadius={0.07} />
      <Flange position={[-5, -3, -1.8]} axis="y" pipeRadius={0.07} />
      <Flange position={[5, -3, -1.8]} axis="y" pipeRadius={0.07} />
      <Flange position={[-5, 0, -1.8]} axis="y" pipeRadius={0.07} />
      <Flange position={[5, 0, -1.8]} axis="y" pipeRadius={0.07} />
      <Flange position={[-6, 2.5, -4]} axis="y" pipeRadius={0.12} />
      <Flange position={[6, -1.5, -4]} axis="y" pipeRadius={0.12} />

      {/* ── VALVES ── */}
      <Valve position={[-5, 0, -1.65]} rotation={[Math.PI / 2, 0, 0]} />
      <Valve position={[5, 0, -1.65]} rotation={[Math.PI / 2, 0, 0]} />
      <Valve position={[0, 3.5, -0.35]} rotation={[0, 0, 0]} scale={0.8} />
      <Valve position={[0, -1.5, 0.65]} rotation={[0, 0, 0]} scale={0.7} />
      <Valve position={[-3.5, 1.8, 0.15]} rotation={[0, 0, 0]} scale={0.65} />

      {/* ── PRESSURE GAUGES ── */}
      <PressureGauge position={[-2.5, 0.12, -1.5]} rotation={[Math.PI / 2, 0, 0.3]} />
      <PressureGauge position={[2.5, 0.12, -1.5]} rotation={[Math.PI / 2, 0, -0.2]} />

      {/* ── FLOW PARTICLES (heat = red/orange, cold = blue) ── */}
      <FlowParticle points={[[-10, 0, -1.5], [10, 0, -1.5]]} color="#DC2626" speed={0.12} delay={0} />
      <FlowParticle points={[[-10, 0, -1.5], [10, 0, -1.5]]} color="#DC2626" speed={0.12} delay={4.5} />
      <FlowParticle points={[[-10, 3.5, -2], [10, 3.5, -2]]} color="#F97316" speed={0.1} delay={1} />
      <FlowParticle points={[[-10, -3, -2], [10, -3, -2]]} color="#F97316" speed={0.1} delay={2} />
      <FlowParticle points={[[0, -5, -1.5], [0, 5, -1.5]]} color="#3B82F6" speed={0.08} delay={0.5} />
      <FlowParticle points={[[-5, -5, -1.8], [-5, 5, -1.8]]} color="#3B82F6" speed={0.08} delay={2} />
      <FlowParticle points={[[5, -5, -1.8], [5, 5, -1.8]]} color="#DC2626" speed={0.08} delay={1.5} />
      <FlowParticle points={[[-12, 2.5, -4], [12, 2.5, -4]]} color="#F97316" speed={0.06} delay={0} size={0.05} />
      <FlowParticle points={[[-12, -1.5, -4], [12, -1.5, -4]]} color="#3B82F6" speed={0.06} delay={3} size={0.05} />
      <FlowParticle
        points={[
          [-3, -1.5, -1.5], [-2.8, -1.5, -1.5], [-2.5, -1.5, 0.5],
          [2.5, -1.5, 0.5], [2.8, -1.5, -1.5], [3, -1.5, -1.5],
        ]}
        color="#F97316"
        speed={0.08}
        delay={0}
      />
    </>
  );
}

// ═══════════════════════════════════════
// Export – Canvas wrapper
// ═══════════════════════════════════════
export default function PipeNetwork() {
  return (
    <div className="absolute inset-0 z-0 pointer-events-none">
      <Canvas
        camera={{ position: [0, 0, 8], fov: 50 }}
        gl={{ antialias: true, alpha: true }}
        dpr={[1, 1.5]}
      >
        <fog attach="fog" args={["#070707", 5, 20]} />

        {/* Warm lighting for copper */}
        <ambientLight intensity={0.3} color="#FFF5E6" />
        <directionalLight position={[5, 8, 4]} intensity={1.5} color="#FFF0D4" />
        <pointLight position={[-4, 2, 3]} intensity={0.8} color="#DC2626" distance={10} />
        <pointLight position={[4, -2, 3]} intensity={0.4} color="#1C448E" distance={8} />

        <Suspense fallback={null}>
          <PipeScene />
          <Environment preset="warehouse" background={false} />
        </Suspense>

        <CameraRig />
      </Canvas>
    </div>
  );
}
