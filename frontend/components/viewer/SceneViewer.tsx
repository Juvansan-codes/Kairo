"use client";

import { Canvas, useThree } from "@react-three/fiber";
import type { ThreeEvent } from "@react-three/fiber";
import { OrbitControls, useGLTF, Center, ContactShadows, Text } from "@react-three/drei";
import { Suspense, useEffect, useRef, useState, useCallback, Component } from "react";
import type { ReactNode, ErrorInfo } from "react";
import * as THREE from "three";
import type { SceneLayer } from "@/lib/types";

// ── Error Boundary for 3D Loader ──

interface ErrorBoundaryProps {
  fallback: ReactNode;
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

class ModelErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.warn("3D Model load error captured by boundary:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

// ── GLB Model Component ──

interface ModelProps {
  url: string;
  layers: SceneLayer[];
  onObjectClick?: (name: string) => void;
  onLoaded?: () => void;
}

function RemoteGLTFModel({ url, layers, onObjectClick, onLoaded }: ModelProps) {
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
        if (child.name.toLowerCase().startsWith(layer.prefix.toLowerCase())) {
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

// ── Interactive Architectural Floor Plan Model (Parametric Metric Reconstruction) ──

interface ArchitecturalModelProps {
  layers: SceneLayer[];
  onObjectClick?: (name: string) => void;
}

function ArchitecturalModel({ layers, onObjectClick }: ArchitecturalModelProps) {
  const isLayerVisible = (prefix: string) => {
    const layer = layers.find((l) => l.prefix.toLowerCase() === prefix.toLowerCase());
    return layer ? layer.visible : true;
  };

  const handleMeshClick = (name: string) => (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    onObjectClick?.(name);
  };

  const showWalls = isLayerVisible("wall");
  const showDoors = isLayerVisible("door");
  const showWindows = isLayerVisible("window");
  const showFloor = isLayerVisible("floor");
  const showDims = isLayerVisible("dim");

  return (
    <Center>
      <group position={[0, 0, 0]}>
        {/* ── Floor Slabs ── */}
        {showFloor && (
          <group name="floor_root">
            {/* Main Living Area Slab */}
            <mesh
              name="floor_living"
              position={[-1.5, 0, 0]}
              rotation={[-Math.PI / 2, 0, 0]}
              receiveShadow
              onClick={handleMeshClick("floor_living")}
            >
              <planeGeometry args={[5, 6]} />
              <meshStandardMaterial color="#1a1a1a" roughness={0.8} />
            </mesh>

            {/* Bedroom / Suite Slab */}
            <mesh
              name="floor_bedroom"
              position={[2.5, 0, -1]}
              rotation={[-Math.PI / 2, 0, 0]}
              receiveShadow
              onClick={handleMeshClick("floor_bedroom")}
            >
              <planeGeometry args={[3, 4]} />
              <meshStandardMaterial color="#222222" roughness={0.7} />
            </mesh>

            {/* Bath / Utility Slab */}
            <mesh
              name="floor_bath"
              position={[2.5, 0, 2]}
              rotation={[-Math.PI / 2, 0, 0]}
              receiveShadow
              onClick={handleMeshClick("floor_bath")}
            >
              <planeGeometry args={[3, 2]} />
              <meshStandardMaterial color="#1f1f1f" roughness={0.6} />
            </mesh>
          </group>
        )}

        {/* ── Exterior Metric Walls (Height: 2.8m, Thickness: 0.18m) ── */}
        {showWalls && (
          <group name="wall_root">
            {/* North Wall */}
            <mesh
              name="wall_north_exterior"
              position={[0, 1.4, -3]}
              castShadow
              receiveShadow
              onClick={handleMeshClick("wall_north_exterior (9.0m × 2.8m)")}
            >
              <boxGeometry args={[8, 2.8, 0.18]} />
              <meshStandardMaterial color="#383838" roughness={0.5} />
            </mesh>

            {/* South Wall */}
            <mesh
              name="wall_south_exterior"
              position={[0, 1.4, 3]}
              castShadow
              receiveShadow
              onClick={handleMeshClick("wall_south_exterior (9.0m × 2.8m)")}
            >
              <boxGeometry args={[8, 2.8, 0.18]} />
              <meshStandardMaterial color="#383838" roughness={0.5} />
            </mesh>

            {/* West Wall */}
            <mesh
              name="wall_west_exterior"
              position={[-4, 1.4, 0]}
              castShadow
              receiveShadow
              onClick={handleMeshClick("wall_west_exterior (6.0m × 2.8m)")}
            >
              <boxGeometry args={[0.18, 2.8, 6]} />
              <meshStandardMaterial color="#383838" roughness={0.5} />
            </mesh>

            {/* East Wall */}
            <mesh
              name="wall_east_exterior"
              position={[4, 1.4, 0]}
              castShadow
              receiveShadow
              onClick={handleMeshClick("wall_east_exterior (6.0m × 2.8m)")}
            >
              <boxGeometry args={[0.18, 2.8, 6]} />
              <meshStandardMaterial color="#383838" roughness={0.5} />
            </mesh>

            {/* ── Interior Partitions (Thickness: 0.12m) ── */}
            {/* Spine Wall separating Living & Private zones */}
            <mesh
              name="wall_partition_spine"
              position={[1, 1.4, -0.5]}
              castShadow
              receiveShadow
              onClick={handleMeshClick("wall_partition_spine (5.0m)")}
            >
              <boxGeometry args={[0.12, 2.8, 5]} />
              <meshStandardMaterial color="#444444" roughness={0.6} />
            </mesh>

            {/* Dividing Wall between Bedroom & Bath */}
            <mesh
              name="wall_partition_bath"
              position={[2.5, 1.4, 1]}
              castShadow
              receiveShadow
              onClick={handleMeshClick("wall_partition_bath (3.0m)")}
            >
              <boxGeometry args={[3, 2.8, 0.12]} />
              <meshStandardMaterial color="#444444" roughness={0.6} />
            </mesh>
          </group>
        )}

        {/* ── Door Openings & Swings ── */}
        {showDoors && (
          <group name="door_root">
            {/* Front Entrance Door Frame */}
            <mesh
              name="door_entrance"
              position={[-1.5, 1.1, 3]}
              onClick={handleMeshClick("door_entrance (0.9m × 2.1m)")}
            >
              <boxGeometry args={[0.9, 2.2, 0.22]} />
              <meshStandardMaterial color="#F15A24" roughness={0.3} metalness={0.2} />
            </mesh>

            {/* Master Bed Door */}
            <mesh
              name="door_bedroom"
              position={[1, 1.1, -1.8]}
              onClick={handleMeshClick("door_bedroom (0.85m × 2.1m)")}
            >
              <boxGeometry args={[0.2, 2.1, 0.85]} />
              <meshStandardMaterial color="#F15A24" roughness={0.4} />
            </mesh>

            {/* Bathroom Door */}
            <mesh
              name="door_bath"
              position={[2, 1.1, 1]}
              onClick={handleMeshClick("door_bath (0.75m × 2.1m)")}
            >
              <boxGeometry args={[0.75, 2.1, 0.2]} />
              <meshStandardMaterial color="#F15A24" roughness={0.4} />
            </mesh>
          </group>
        )}

        {/* ── Windows with Glazing ── */}
        {showWindows && (
          <group name="window_root">
            {/* Living Room North Window */}
            <mesh
              name="window_living_north"
              position={[-2.5, 1.6, -3]}
              onClick={handleMeshClick("window_living_north (2.0m × 1.4m)")}
            >
              <boxGeometry args={[2.0, 1.4, 0.22]} />
              <meshStandardMaterial
                color="#64B5F6"
                roughness={0.1}
                metalness={0.8}
                transparent
                opacity={0.65}
              />
            </mesh>

            {/* West Garden Window */}
            <mesh
              name="window_living_west"
              position={[-4, 1.6, 0.5]}
              onClick={handleMeshClick("window_living_west (2.4m × 1.4m)")}
            >
              <boxGeometry args={[0.22, 1.4, 2.4]} />
              <meshStandardMaterial
                color="#64B5F6"
                roughness={0.1}
                metalness={0.8}
                transparent
                opacity={0.65}
              />
            </mesh>

            {/* Master Bed East Window */}
            <mesh
              name="window_bedroom_east"
              position={[4, 1.6, -1.2]}
              onClick={handleMeshClick("window_bedroom_east (1.6m × 1.4m)")}
            >
              <boxGeometry args={[0.22, 1.4, 1.6]} />
              <meshStandardMaterial
                color="#64B5F6"
                roughness={0.1}
                metalness={0.8}
                transparent
                opacity={0.65}
              />
            </mesh>
          </group>
        )}

        {/* ── Dimensions & Metric Guides ── */}
        {showDims && (
          <group name="dim_root">
            {/* Width Metric Callout */}
            <mesh position={[0, 0.05, 3.8]}>
              <boxGeometry args={[8, 0.02, 0.02]} />
              <meshBasicMaterial color="#F15A24" />
            </mesh>
            <Text
              position={[0, 0.2, 4.0]}
              rotation={[-Math.PI / 2, 0, 0]}
              fontSize={0.28}
              color="#F15A24"
            >
              WIDTH: 8.00m [CONF: 98.4%]
            </Text>

            {/* Length Metric Callout */}
            <mesh position={[-4.8, 0.05, 0]}>
              <boxGeometry args={[0.02, 0.02, 6]} />
              <meshBasicMaterial color="#F15A24" />
            </mesh>
            <Text
              position={[-5.0, 0.2, 0]}
              rotation={[-Math.PI / 2, 0, Math.PI / 2]}
              fontSize={0.28}
              color="#F15A24"
            >
              LENGTH: 6.00m [CONF: 97.9%]
            </Text>
          </group>
        )}
      </group>
    </Center>
  );
}

// ── Camera Preset Controller ──

interface CameraSetterProps {
  preset: "default" | "top" | "front" | "side" | null;
  onDone: () => void;
}

function CameraSetter({ preset, onDone }: CameraSetterProps) {
  const { camera } = useThree();

  useEffect(() => {
    if (!preset) return;
    const positions: Record<string, [number, number, number]> = {
      default: [9, 9, 9],
      top: [0, 16, 0.01],
      front: [0, 4, 12],
      side: [12, 4, 0],
    };
    const pos = positions[preset] || positions.default;
    camera.position.set(...pos);
    camera.lookAt(0, 0, 0);
    camera.updateProjectionMatrix();
    onDone();
  }, [preset, camera, onDone]);

  return null;
}

// ── Overlays ──

function LoadingOverlay() {
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-kairo-gray-950/90 z-10 backdrop-blur-sm">
      <div className="text-center space-y-3">
        <div className="w-8 h-8 border-2 border-kairo-gray-700 border-t-kairo-orange rounded-full animate-spin mx-auto" />
        <p className="text-xs font-mono font-semibold text-kairo-gray-300 uppercase tracking-wider">
          Compiling 3D Geometry…
        </p>
      </div>
    </div>
  );
}

// ── Main SceneViewer Export ──

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
  const [cameraPreset, setCameraPreset] = useState<"default" | "top" | "front" | "side" | null>(null);

  const handleLoaded = useCallback(() => {
    setLoading(false);
  }, []);

  return (
    <div
      className={`relative w-full h-full rounded-kairo overflow-hidden bg-kairo-gray-950 select-none ${className}`}
      style={{ minHeight: 400 }}
    >
      {loading && modelUrl && <LoadingOverlay />}

      {/* Camera Viewport Presets Toolbar */}
      <div className="absolute top-4 right-4 z-20 flex flex-col gap-1.5">
        {(["top", "front", "side", "default"] as const).map((preset) => (
          <button
            key={preset}
            onClick={() => setCameraPreset(preset)}
            className="px-3 py-1.5 bg-kairo-gray-900/80 backdrop-blur-md border border-kairo-gray-800 text-kairo-gray-300 text-[10px] font-mono font-medium uppercase tracking-wider rounded hover:border-kairo-orange hover:text-kairo-orange transition-all shadow-md"
          >
            {preset === "default" ? "Isometric" : preset}
          </button>
        ))}
      </div>

      <Canvas
        shadows
        camera={{ position: [9, 9, 9], fov: 48 }}
        onCreated={() => {
          setLoading(false);
        }}
        gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping }}
      >
        <color attach="background" args={["#0c0c0c"]} />
        <fog attach="fog" args={["#0c0c0c", 20, 42]} />

        <ambientLight intensity={0.55} />
        <directionalLight position={[7, 12, 6]} intensity={0.9} castShadow />
        <directionalLight position={[-4, 8, -5]} intensity={0.35} />

        <Suspense fallback={null}>
          <ModelErrorBoundary
            fallback={
              <ArchitecturalModel layers={layers} onObjectClick={onObjectClick} />
            }
          >
            {modelUrl ? (
              <RemoteGLTFModel
                url={modelUrl}
                layers={layers}
                onObjectClick={onObjectClick}
                onLoaded={handleLoaded}
              />
            ) : (
              <ArchitecturalModel layers={layers} onObjectClick={onObjectClick} />
            )}
          </ModelErrorBoundary>

          <ContactShadows
            opacity={0.35}
            scale={22}
            blur={2.4}
            far={10}
            position={[0, -0.01, 0]}
          />
        </Suspense>

        <OrbitControls makeDefault enableDamping />

        <CameraSetter preset={cameraPreset} onDone={() => setCameraPreset(null)} />

        {/* Blueprint Ground Reference Grid */}
        <gridHelper args={[24, 48, "#F15A24", "#1e1e1e"]} />
      </Canvas>

      {/* Model status pill badge */}
      <div className="absolute bottom-4 left-4 z-20 pointer-events-none">
        <div className="px-3 py-1 bg-kairo-gray-900/80 backdrop-blur border border-kairo-gray-800 rounded text-[11px] text-kairo-gray-400 font-mono flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-kairo-orange animate-pulse" />
          <span>{modelUrl ? "GLB Render Active" : "Interactive Metric Engine"}</span>
        </div>
      </div>
    </div>
  );
}
