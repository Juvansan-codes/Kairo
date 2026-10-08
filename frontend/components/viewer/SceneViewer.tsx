"use client";

import { Canvas, useThree } from "@react-three/fiber";
import type { ThreeEvent } from "@react-three/fiber";
import { OrbitControls, useGLTF, Center, ContactShadows } from "@react-three/drei";
import { Suspense, useEffect, useRef, useState, useCallback } from "react";
import * as THREE from "three";
import type { SceneLayer } from "@/lib/types";

// ── GLB Model Component ──

interface ModelProps {
  url: string;
  layers: SceneLayer[];
  onObjectClick?: (name: string) => void;
  onLoaded?: () => void;
}

function Model({ url, layers, onObjectClick, onLoaded }: ModelProps) {
  const { scene } = useGLTF(url);
  const groupRef = useRef<THREE.Group>(null);

  useEffect(() => {
    if (scene) {
      onLoaded?.();
    }
  }, [scene, onLoaded]);

  // Apply layer visibility
  useEffect(() => {
    if (!scene) return;
    scene.traverse((child: THREE.Object3D) => {
      for (const layer of layers) {
        if (child.name.toLowerCase().startsWith(layer.prefix)) {
          child.visible = layer.visible;
        }
      }
    });
  }, [scene, layers]);

  const handleClick = useCallback(
    (e: ThreeEvent<MouseEvent>) => {
      e.stopPropagation();
      if (e.object?.name && onObjectClick) {
        onObjectClick(e.object.name);
      }
    },
    [onObjectClick]
  );

  return (
    <Center>
      <primitive ref={groupRef} object={scene} onClick={handleClick} />
    </Center>
  );
}

// ── Placeholder when no model ──

function PlaceholderModel() {
  return (
    <Center>
      <group>
        {/* Floor */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
          <planeGeometry args={[6, 4]} />
          <meshStandardMaterial color="#1a1a1a" />
        </mesh>
        {/* Walls */}
        <mesh position={[0, 1, -2]}>
          <boxGeometry args={[6, 2, 0.1]} />
          <meshStandardMaterial color="#333" wireframe />
        </mesh>
        <mesh position={[-3, 1, 0]}>
          <boxGeometry args={[0.1, 2, 4]} />
          <meshStandardMaterial color="#333" wireframe />
        </mesh>
        <mesh position={[3, 1, 0]}>
          <boxGeometry args={[0.1, 2, 4]} />
          <meshStandardMaterial color="#333" wireframe />
        </mesh>
        {/* Orange accent line */}
        <mesh position={[0, 0.01, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[1.8, 2, 4]} />
          <meshBasicMaterial color="#F15A24" wireframe />
        </mesh>
      </group>
    </Center>
  );
}

// ── Camera Setter ──

interface CameraSetterProps {
  preset: "default" | "top" | "front" | "side" | null;
  onDone: () => void;
}

function CameraSetter({ preset, onDone }: CameraSetterProps) {
  const { camera } = useThree();

  useEffect(() => {
    if (!preset) return;
    const positions: Record<string, [number, number, number]> = {
      default: [8, 8, 8],
      top: [0, 15, 0],
      front: [0, 5, 12],
      side: [12, 5, 0],
    };
    const pos = positions[preset] || positions.default;
    camera.position.set(...pos);
    camera.lookAt(0, 0, 0);
    camera.updateProjectionMatrix();
    onDone();
  }, [preset, camera, onDone]);

  return null;
}

// ── Loading State ──

function LoadingOverlay() {
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-kairo-gray-950/90 z-10">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-kairo-gray-700 border-t-kairo-orange rounded-full animate-spin mx-auto mb-4" />
        <p className="text-sm font-medium text-kairo-gray-400 tracking-wider uppercase">
          Loading Spatial Model
        </p>
      </div>
    </div>
  );
}

// ── Error State ──

function ErrorOverlay({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-kairo-gray-950/90 z-10">
      <div className="text-center max-w-xs">
        <p className="text-sm font-medium text-kairo-gray-300 mb-2 tracking-wider uppercase">
          Unable to Load Scene
        </p>
        <p className="text-xs text-kairo-gray-500 mb-6">
          The generated GLB could not be loaded.
        </p>
        <button onClick={onRetry} className="btn-primary text-sm px-6 py-2.5">
          Retry
        </button>
      </div>
    </div>
  );
}

// ── Main Viewer ──

interface SceneViewerProps {
  modelUrl?: string | null;
  layers?: SceneLayer[];
  onObjectClick?: (name: string) => void;
  className?: string;
}

export function SceneViewer({
  modelUrl,
  layers = [],
  onObjectClick,
  className = "",
}: SceneViewerProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [cameraPreset, setCameraPreset] = useState<"default" | "top" | "front" | "side" | null>(null);

  const handleLoaded = useCallback(() => {
    setLoading(false);
  }, []);

  return (
    <div
      className={`relative w-full h-full rounded-kairo overflow-hidden bg-kairo-gray-950 ${className}`}
      style={{ minHeight: 400 }}
    >
      {loading && modelUrl && <LoadingOverlay />}
      {error && <ErrorOverlay onRetry={() => { setError(false); setLoading(true); }} />}

      {/* Toolbar */}
      <div className="absolute top-4 right-4 z-20 flex flex-col gap-1.5">
        {(["top", "front", "side", "default"] as const).map((preset) => (
          <button
            key={preset}
            onClick={() => setCameraPreset(preset)}
            className="px-3 py-1.5 bg-kairo-gray-900/80 backdrop-blur border border-kairo-gray-800 text-kairo-gray-300 text-[10px] font-medium uppercase tracking-wider rounded hover:border-kairo-orange hover:text-kairo-orange transition-all"
          >
            {preset === "default" ? "Reset" : preset}
          </button>
        ))}
      </div>

      <Canvas
        shadows
        camera={{ position: [8, 8, 8], fov: 50 }}
        onCreated={() => {
          if (!modelUrl) setLoading(false);
        }}
        gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping }}
      >
        <color attach="background" args={["#111111"]} />
        <fog attach="fog" args={["#111111", 20, 40]} />

        <ambientLight intensity={0.4} />
        <directionalLight position={[5, 10, 5]} intensity={0.8} castShadow />
        <directionalLight position={[-3, 6, -4]} intensity={0.3} />

        <Suspense fallback={null}>
          {modelUrl ? (
            <Model
              url={modelUrl}
              layers={layers}
              onObjectClick={onObjectClick}
              onLoaded={handleLoaded}
            />
          ) : (
            <PlaceholderModel />
          )}

          <ContactShadows
            opacity={0.3}
            scale={20}
            blur={2}
            far={10}
            position={[0, -0.01, 0]}
          />
        </Suspense>

        <OrbitControls makeDefault enableDamping />

        <CameraSetter preset={cameraPreset} onDone={() => setCameraPreset(null)} />

        {/* Ground grid */}
        <gridHelper args={[20, 40, "#222222", "#1a1a1a"]} />
      </Canvas>

      {/* Awaiting model overlay */}
      {!modelUrl && !loading && (
        <div className="absolute bottom-4 left-4 z-20">
          <div className="px-3 py-1.5 bg-kairo-gray-900/80 backdrop-blur border border-kairo-gray-800 rounded text-xs text-kairo-gray-500 font-mono">
            Awaiting 3D model…
          </div>
        </div>
      )}
    </div>
  );
}
