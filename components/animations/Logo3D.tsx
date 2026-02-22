"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, PresentationControls, Environment, ContactShadows } from "@react-three/drei";
import * as THREE from "three";

// ═══ Gradient endpoint colors ═══
const FLAME_TOP = new THREE.Color("#FF3B1D");
const FLAME_BOTTOM = new THREE.Color("#8B1A6D");
const BASE_TOP = new THREE.Color("#2563EB");
const BASE_BOTTOM = new THREE.Color("#0A1128");

// ═══ Extrude settings ═══
const EXTRUDE: THREE.ExtrudeGeometryOptions = {
  steps: 1,
  depth: 0.35,
  bevelEnabled: true,
  bevelThickness: 0.05,
  bevelSize: 0.04,
  bevelSegments: 4,
};

// ═══ Shape builders ═══

/** Red flame — the right-side teardrop/flame shape */
function createFlameShape(): THREE.Shape {
  const s = new THREE.Shape();

  // Bottom meeting point (where flame meets the D base)
  s.moveTo(0.02, -0.35);

  // Outer (right) edge sweeping up in a smooth S-curve
  s.bezierCurveTo(0.3, -0.3, 0.55, -0.05, 0.63, 0.2);
  s.bezierCurveTo(0.67, 0.45, 0.55, 0.72, 0.38, 0.88);
  s.bezierCurveTo(0.27, 0.97, 0.17, 1.02, 0.1, 0.97);

  // Inner (left) edge — concave curve back down
  s.bezierCurveTo(-0.02, 0.85, -0.13, 0.58, -0.1, 0.28);
  s.bezierCurveTo(-0.07, 0.02, -0.02, -0.2, 0.02, -0.35);

  return s;
}

/** Blue D-shape — the left crescent base with triangular cutout */
function createBaseShape(): THREE.Shape {
  const s = new THREE.Shape();

  // Start at right where it meets the flame
  s.moveTo(0.02, -0.35);

  // Bottom-right: swoops right then curves down
  s.bezierCurveTo(0.15, -0.45, 0.35, -0.55, 0.42, -0.55);
  s.bezierCurveTo(0.48, -0.55, 0.45, -0.62, 0.3, -0.68);

  // Bottom edge going left
  s.bezierCurveTo(0.1, -0.74, -0.15, -0.77, -0.3, -0.74);

  // Angular bottom-left corner
  s.lineTo(-0.48, -0.72);

  // Left edge — convex curve going up
  s.bezierCurveTo(-0.6, -0.55, -0.63, -0.2, -0.58, 0.05);
  s.bezierCurveTo(-0.52, 0.3, -0.38, 0.48, -0.2, 0.52);

  // Upper curve right to meet flame's inner edge
  s.bezierCurveTo(-0.1, 0.54, -0.05, 0.42, -0.08, 0.25);

  // Inner right edge back down to start
  s.bezierCurveTo(-0.07, 0.05, -0.02, -0.18, 0.02, -0.35);

  // Triangular cutout (negative space inside the D)
  const hole = new THREE.Path();
  hole.moveTo(-0.08, 0.18);
  hole.lineTo(0.08, -0.18);
  hole.lineTo(-0.32, -0.42);
  hole.closePath();
  s.holes.push(hole);

  return s;
}

/** Apply a Y-based vertex colour gradient to an extruded geometry */
function applyGradient(
  geo: THREE.BufferGeometry,
  top: THREE.Color,
  bottom: THREE.Color,
) {
  const pos = geo.attributes.position;
  let minY = Infinity;
  let maxY = -Infinity;

  for (let i = 0; i < pos.count; i++) {
    const y = pos.getY(i);
    if (y < minY) minY = y;
    if (y > maxY) maxY = y;
  }

  const colors = new Float32Array(pos.count * 3);
  const range = maxY - minY || 1;
  const tmp = new THREE.Color();

  for (let i = 0; i < pos.count; i++) {
    const t = (pos.getY(i) - minY) / range;
    tmp.copy(bottom).lerp(top, t);
    colors[i * 3] = tmp.r;
    colors[i * 3 + 1] = tmp.g;
    colors[i * 3 + 2] = tmp.b;
  }

  geo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
}

// ═══ Mesh sub-components ═══

function LogoFlame() {
  const geo = useMemo(() => {
    const g = new THREE.ExtrudeGeometry(createFlameShape(), EXTRUDE);
    applyGradient(g, FLAME_TOP, FLAME_BOTTOM);
    return g;
  }, []);

  return (
    <mesh geometry={geo} position={[0, 0, 0.03]}>
      <meshStandardMaterial
        vertexColors
        metalness={0.85}
        roughness={0.15}
        emissive="#DC2626"
        emissiveIntensity={0.12}
      />
    </mesh>
  );
}

function LogoBase() {
  const geo = useMemo(() => {
    const g = new THREE.ExtrudeGeometry(createBaseShape(), EXTRUDE);
    applyGradient(g, BASE_TOP, BASE_BOTTOM);
    return g;
  }, []);

  return (
    <mesh geometry={geo} position={[0, 0, -0.03]}>
      <meshStandardMaterial
        vertexColors
        metalness={0.85}
        roughness={0.15}
        emissive="#1C448E"
        emissiveIntensity={0.08}
      />
    </mesh>
  );
}

function LogoGroup() {
  const ref = useRef<THREE.Group>(null);

  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.y = Math.sin(clock.getElapsedTime() * 0.5) * 0.15;
    }
  });

  return (
    <group ref={ref} scale={1.6} position={[0, -0.1, 0]}>
      <LogoFlame />
      <LogoBase />
    </group>
  );
}

// ═══ Export ═══

export default function Logo3D() {
  return (
    <div className="w-full h-full">
      <Canvas shadows camera={{ position: [0, 0, 4.5], fov: 45 }}>
        <ambientLight intensity={0.4} />
        <spotLight
          position={[8, 8, 6]}
          angle={0.2}
          penumbra={1}
          intensity={1.5}
          castShadow
        />
        <pointLight position={[-3, 2, 4]} intensity={0.5} color="#DC2626" />
        <pointLight position={[3, -2, 4]} intensity={0.3} color="#1C448E" />

        <PresentationControls
          global
          rotation={[0, 0.3, 0]}
          polar={[-Math.PI / 3, Math.PI / 3]}
          azimuth={[-Math.PI / 1.4, Math.PI / 1.4]}
        >
          <Float speed={2} rotationIntensity={0.8} floatIntensity={0.6}>
            <LogoGroup />
          </Float>
        </PresentationControls>

        <ContactShadows
          position={[0, -1.8, 0]}
          opacity={0.3}
          scale={8}
          blur={2.5}
          far={4.5}
        />
        <Environment preset="city" background={false} />
      </Canvas>
    </div>
  );
}
