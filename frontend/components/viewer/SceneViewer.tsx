"use client";

import { Canvas } from "@react-three/fiber";
import { OrbitControls, Stage, useGLTF } from "@react-three/drei";
import { Suspense } from "react";

interface SceneViewerProps {
  modelUrl?: string | null;
}

function Model({ url }: { url: string }) {
  const { scene } = useGLTF(url);
  return <primitive object={scene} />;
}

export function SceneViewer({ modelUrl }: SceneViewerProps) {
  return (
    <div className="w-full h-full bg-neutral-900 rounded-lg overflow-hidden border border-neutral-800 relative">
      <Canvas shadows camera={{ position: [0, 10, 10], fov: 50 }}>
        <Suspense fallback={null}>
          <Stage environment="city" intensity={0.5}>
            {modelUrl ? (
              <Model url={modelUrl} />
            ) : (
              <mesh>
                <boxGeometry args={[1, 1, 1]} />
                <meshStandardMaterial color="#f97316" wireframe />
              </mesh>
            )}
          </Stage>
        </Suspense>
        <OrbitControls makeDefault />
      </Canvas>
      
      {!modelUrl && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-neutral-500 font-mono text-sm bg-neutral-900/80 px-4 py-2 rounded">
            Awaiting 3D Model...
          </div>
        </div>
      )}
    </div>
  );
}
