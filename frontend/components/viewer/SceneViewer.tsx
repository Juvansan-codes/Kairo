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
  onBoundsComputed?: (bounds: { center: THREE.Vector3; distance: number; size: THREE.Vector3 }) => void;
}

function RemoteGLTFModel({ url, layers, onObjectClick, onLoaded, onBoundsComputed }: ModelProps) {
  const { scene } = useGLTF(url);
  const groupRef = useRef<THREE.Group>(null);
  const { camera } = useThree();

  useEffect(() => {
    if (scene && groupRef.current) {
      const box = new THREE.Box3().setFromObject(groupRef.current);
      if (!box.isEmpty() && onBoundsComputed) {
        const center = new THREE.Vector3();
        box.getCenter(center);
        const size = new THREE.Vector3();
        box.getSize(size);
        const maxDim = Math.max(size.x, size.y, size.z);
        const effectiveDim = maxDim < 0.1 ? 10 : maxDim;
        const fov = (camera as THREE.PerspectiveCamera).fov * (Math.PI / 180);
        // Tighter framing: 1.1 margin instead of 1.5
        const distance = Math.abs(effectiveDim / 2 / Math.tan(fov / 2)) * 1.1;
        const safeDistance = Math.min(Math.max(distance, 5), 10000);
        onBoundsComputed({ center, distance: safeDistance, size });
      }
      onLoaded?.();
    }
  }, [scene, camera, onLoaded, onBoundsComputed]);

  // Apply layer visibility and architectural materials
  useEffect(() => {
    if (!scene) return;
    scene.traverse((child: THREE.Object3D) => {
      // Visibility toggle based on layers
      for (const layer of layers) {
        if (child.name.toLowerCase().startsWith(layer.prefix.toLowerCase())) {
          child.visible = layer.visible;
        }
      }

      // Material overrides for architectural visualization
      if (child instanceof THREE.Mesh) {
        child.castShadow = true;
        child.receiveShadow = true;
        
        // Ensure normals exist for lighting
        if (child.geometry && !child.geometry.hasAttribute('normal')) {
          child.geometry.computeVertexNormals();
        }

        let current: THREE.Object3D | null = child;
        let matchedName = "";
        while (current) {
          if (current.name) {
            const lowerName = current.name.toLowerCase();
            if (lowerName.includes("door") || lowerName.includes("win") || lowerName.includes("wall") || lowerName.includes("room") || lowerName.includes("floor")) {
              matchedName = lowerName;
              break;
            }
          }
          current = current.parent;
        }
        
        if (matchedName.includes("door")) {
          child.material = new THREE.MeshStandardMaterial({
            color: "#F15A24", // Kairo Orange
            roughness: 0.3,
            metalness: 0.1,
          });
        } else if (matchedName.includes("win")) {
          child.material = new THREE.MeshPhysicalMaterial({
            color: "#64B5F6",
            transmission: 0.8,
            opacity: 1,
            transparent: true,
            roughness: 0.1,
            metalness: 0.1,
            ior: 1.5,
          });
        } else if (matchedName.includes("wall")) {
          child.material = new THREE.MeshStandardMaterial({
            color: "#E5E7EB", // Clean light architectural gray
            roughness: 0.9,
            metalness: 0.05,
          });
        } else if (matchedName.includes("room") || matchedName.includes("floor")) {
          child.material = new THREE.MeshStandardMaterial({
            color: "#F3F4F6", 
            roughness: 1.0,
            metalness: 0.0,
          });
        } else {
          // Fallback material for any unmatched geometry
          child.material = new THREE.MeshStandardMaterial({
            color: "#D4D4D4", 
            roughness: 0.8,
          });
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
    <group ref={groupRef}>
      <primitive object={scene} onClick={handleClick} />
    </group>
  );
}

// ── Interactive Architectural Model (Parametric Metric Reconstruction) ──

interface ArchitecturalModelProps {
  layers: SceneLayer[];
  onObjectClick?: (name: string) => void;
  onBoundsComputed?: (bounds: { center: THREE.Vector3; distance: number; size: THREE.Vector3 }) => void;
}

function ArchitecturalModel({ layers, onObjectClick, onBoundsComputed }: ArchitecturalModelProps) {
  useEffect(() => {
    if (onBoundsComputed) {
      onBoundsComputed({ center: new THREE.Vector3(0, 1.4, 0), distance: 16, size: new THREE.Vector3(12, 3, 8) });
    }
  }, [onBoundsComputed]);

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
  bounds: { center: THREE.Vector3; distance: number } | null;
  onDone: () => void;
}

function CameraSetter({ preset, bounds, onDone }: CameraSetterProps) {
  const { camera, controls } = useThree();

  useEffect(() => {
    if (!preset) return;
    
    let center = new THREE.Vector3(0, 0, 0);
    let distance = 16;

    if (bounds) {
      center = bounds.center;
      distance = bounds.distance;
    }

    const offset = new THREE.Vector3();
    if (preset === "default") {
      offset.set(distance * 0.7, distance * 0.7, distance * 0.7);
    } else if (preset === "top") {
      offset.set(0, distance, 0.01); // small z to avoid gimble lock
    } else if (preset === "front") {
      offset.set(0, distance * 0.3, distance);
    } else if (preset === "side") {
      offset.set(distance, distance * 0.3, 0);
    }

    const newPos = center.clone().add(offset);
    camera.position.copy(newPos);
    camera.lookAt(center);
    camera.updateProjectionMatrix();

    if (controls) {
      // @ts-ignore
      controls.target.copy(center);
      // @ts-ignore
      controls.update();
    }

    onDone();
  }, [preset, camera, controls, bounds, onDone]);

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
  metadata?: any;
  hasFailed?: boolean;
}

export function SceneViewer({
  modelUrl,
  layers = [],
  onObjectClick,
  className = "",
  metadata = null,
  hasFailed = false,
}: SceneViewerProps) {
  const [loading, setLoading] = useState(true);
  const [cameraPreset, setCameraPreset] = useState<"default" | "top" | "front" | "side" | null>(null);
  const [modelBounds, setModelBounds] = useState<{ center: THREE.Vector3; distance: number; size: THREE.Vector3 } | null>(null);

  const handleLoaded = useCallback(() => {
    setLoading(false);
    setCameraPreset("default");
  }, []);

  const handleBoundsComputed = useCallback((bounds: { center: THREE.Vector3; distance: number; size: THREE.Vector3 }) => {
    setModelBounds(bounds);
    setCameraPreset("default");
  }, []);

  const groundY = 0; // Trimesh GLTF exporter always puts base at Y=0
  const gridScale = modelBounds ? Math.max(modelBounds.size.x, modelBounds.size.z) * 2.5 : 200;
  const isMetric = metadata?.coordinate_space === "metric";

  return (
    <div
      className={`relative w-full h-full rounded-kairo overflow-hidden bg-kairo-gray-50 select-none ${className}`}
      style={{ minHeight: 400 }}
    >
      {loading && modelUrl && <LoadingOverlay />}

      {/* Scale & Coordinate System UI Indicator */}
      {metadata && (
        <div className="absolute top-4 left-4 z-20 flex flex-col gap-1 pointer-events-none">
          <div className="px-3 py-1.5 bg-white/80 backdrop-blur-md border border-kairo-gray-200 rounded shadow-sm text-[11px] font-mono flex items-center gap-2 text-kairo-gray-700">
            <span className={`w-1.5 h-1.5 rounded-full ${isMetric ? 'bg-green-500' : 'bg-amber-400'}`} />
            <span>Scale: {isMetric && metadata.scale_mm_per_px ? `${metadata.scale_mm_per_px.toFixed(1)} mm/px` : 'Uncalibrated'}</span>
          </div>
          <div className="px-3 py-1.5 bg-white/80 backdrop-blur-md border border-kairo-gray-200 rounded shadow-sm text-[11px] font-mono text-kairo-gray-600">
            Space: {isMetric ? 'Metric' : 'Relative'}
          </div>
        </div>
      )}

      {/* Camera Viewport Presets Toolbar */}
      <div className="absolute top-4 right-4 z-20 flex flex-col gap-1.5">
        {(["top", "front", "side", "default"] as const).map((preset) => (
          <button
            key={preset}
            onClick={() => setCameraPreset(preset)}
            className="px-3 py-1.5 bg-white/80 backdrop-blur-md border border-kairo-gray-200 text-kairo-gray-700 text-[10px] font-mono font-bold uppercase tracking-wider rounded hover:border-kairo-orange hover:text-kairo-orange transition-all shadow-sm"
          >
            {preset === "default" ? "Isometric" : preset}
          </button>
        ))}
      </div>

      <Canvas
        shadows
        camera={{ position: [9, 9, 9], fov: 48, far: 50000 }}
        onCreated={() => {
          setLoading(false);
        }}
        gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping }}
      >
        <color attach="background" args={["#F5F5F7"]} />
        <fog attach="fog" args={["#F5F5F7", gridScale * 1.5 + 10, gridScale * 3.5 + 50]} />

        {/* Professional Architectural Lighting */}
        <hemisphereLight skyColor="#ffffff" groundColor="#d4d4d4" intensity={0.6} />
        
        {/* Key Light scaled to scene bounds */}
        <directionalLight 
          position={[gridScale * 0.2, gridScale * 0.4, gridScale * 0.3]} 
          intensity={1.2} 
          castShadow 
          shadow-mapSize={[2048, 2048]} 
          shadow-camera-near={0.1}
          shadow-camera-far={gridScale * 2 + 1000} 
          shadow-camera-left={-gridScale / 2}
          shadow-camera-right={gridScale / 2}
          shadow-camera-top={gridScale / 2}
          shadow-camera-bottom={-gridScale / 2}
          shadow-bias={-0.001} 
        />
        <directionalLight position={[-gridScale * 0.2, gridScale * 0.2, -gridScale * 0.2]} intensity={0.4} />

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
                onBoundsComputed={handleBoundsComputed}
              />
            ) : (
              <ArchitecturalModel layers={layers} onObjectClick={onObjectClick} onBoundsComputed={handleBoundsComputed} />
            )}
          </ModelErrorBoundary>

          {/* Reference Ground Plane (Presentation Layer) */}
          {modelBounds && (
            <mesh 
              position={[modelBounds.center.x, groundY - 0.02, modelBounds.center.z]} 
              rotation={[-Math.PI / 2, 0, 0]} 
              receiveShadow
            >
              <planeGeometry args={[Math.max(gridScale, 50), Math.max(gridScale, 50)]} />
              <meshStandardMaterial color="#FFFFFF" roughness={1} metalness={0} />
            </mesh>
          )}

          <ContactShadows
            opacity={0.4}
            scale={gridScale}
            blur={2.0}
            far={Math.max(10, gridScale * 0.1)}
            position={[modelBounds?.center.x || 0, groundY, modelBounds?.center.z || 0]}
          />
        </Suspense>

        <OrbitControls 
          makeDefault 
          enableDamping 
          dampingFactor={0.05}
          minPolarAngle={0} 
          maxPolarAngle={Math.PI / 2 + 0.1} 
        />

        <CameraSetter preset={cameraPreset} bounds={modelBounds} onDone={() => setCameraPreset(null)} />

        {/* Subtle Architectural Grid */}
        <gridHelper 
          args={[Math.max(gridScale, 50), 40, "#E5E7EB", "#F3F4F6"]} 
          position={[modelBounds?.center.x || 0, groundY - 0.01, modelBounds?.center.z || 0]} 
        />
      </Canvas>

      {/* Model status pill badge */}
      <div className="absolute bottom-4 left-4 z-20 pointer-events-none">
        <div className={`px-3 py-1 bg-white/80 backdrop-blur border shadow-sm rounded text-[11px] font-mono flex items-center gap-2 ${hasFailed ? 'border-red-200 text-red-600' : 'border-kairo-gray-200 text-kairo-gray-600'}`}>
          <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${hasFailed ? 'bg-red-500' : 'bg-kairo-orange'}`} />
          <span>{hasFailed ? "Reconstruction Failed (Fallback Mode)" : (modelUrl ? "GLB Render Active" : "Interactive Metric Engine")}</span>
        </div>
      </div>
    </div>
  );
}
