"use client";

import { useState, useCallback } from "react";
import dynamic from "next/dynamic";
import { useParams, useRouter } from "next/navigation";
import { LayerControls } from "@/components/viewer/LayerControls";
import { SceneStats } from "@/components/viewer/SceneStats";
import { Download, ArrowLeft } from "lucide-react";
import type { SceneLayer, ReconstructionMetadata } from "@/lib/types";
import { USE_MOCK, MOCK_METADATA } from "@/lib/mock";

// Dynamic import to avoid SSR issues with Three.js
const SceneViewer = dynamic(
  () =>
    import("@/components/viewer/SceneViewer").then((mod) => ({
      default: mod.SceneViewer,
    })),
  { ssr: false }
);

const DEFAULT_LAYERS: SceneLayer[] = [
  { id: "walls", label: "Walls", visible: true, prefix: "wall" },
  { id: "doors", label: "Doors", visible: true, prefix: "door" },
  { id: "windows", label: "Windows", visible: true, prefix: "window" },
  { id: "floor", label: "Floor", visible: true, prefix: "floor" },
  { id: "dimensions", label: "Dimensions", visible: false, prefix: "dim" },
];

export default function ScenePage() {
  const params = useParams();
  const router = useRouter();
  const sceneId = params.id as string;

  const [layers, setLayers] = useState<SceneLayer[]>(DEFAULT_LAYERS);
  const [selectedObject, setSelectedObject] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"3d" | "2d" | "split">("3d");

  // In production this comes from API; in mock mode use demo data
  const metadata: ReconstructionMetadata = MOCK_METADATA;
  const modelUrl = USE_MOCK ? null : `/api/result/${sceneId}/model`; // null shows placeholder in mock

  const handleLayerToggle = useCallback((id: string) => {
    setLayers((prev) =>
      prev.map((l) => (l.id === id ? { ...l, visible: !l.visible } : l))
    );
  }, []);

  const handleObjectClick = useCallback((name: string) => {
    setSelectedObject(name);
  }, []);

  return (
    <div className="h-[calc(100vh-64px)] flex flex-col">
      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-kairo-gray-200 bg-white flex-shrink-0">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="p-1.5 hover:bg-kairo-offwhite rounded transition-colors"
            aria-label="Go back"
          >
            <ArrowLeft className="w-4 h-4 text-kairo-gray-500" />
          </button>
          <div>
            <p className="text-sm font-semibold text-kairo-black">
              Scene #{sceneId}
            </p>
            <p className="text-xs text-kairo-gray-400">KAIRO Reconstruction</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* View mode toggle */}
          <div className="hidden md:flex items-center border border-kairo-gray-200 rounded-kairo overflow-hidden">
            {(["2d", "3d", "split"] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`px-3 py-1.5 text-xs font-medium uppercase tracking-wider transition-colors ${
                  viewMode === mode
                    ? "bg-kairo-black text-white"
                    : "text-kairo-gray-500 hover:text-kairo-black"
                }`}
              >
                {mode}
              </button>
            ))}
          </div>

          <a
            href={modelUrl || "#"}
            download
            className="btn-secondary text-xs px-4 py-2"
          >
            <Download className="w-3.5 h-3.5" />
            Export GLB
          </a>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* 3D Viewport */}
        <div
          className={`flex-1 relative ${
            viewMode === "split" ? "w-1/2" : "w-full"
          }`}
        >
          {viewMode !== "2d" && (
            <SceneViewer
              modelUrl={modelUrl}
              layers={layers}
              onObjectClick={handleObjectClick}
              className="w-full h-full rounded-none"
            />
          )}

          {viewMode === "2d" && (
            <div className="w-full h-full bg-white flex items-center justify-center">
              <div className="text-center">
                <p className="micro-label mb-2 text-kairo-gray-400">
                  ORIGINAL BLUEPRINT
                </p>
                <p className="text-sm text-kairo-gray-400">
                  Upload blueprint to view 2D comparison
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Split: 2D side */}
        {viewMode === "split" && (
          <div className="w-1/2 border-l border-kairo-gray-200 bg-white flex items-center justify-center">
            <div className="text-center">
              <p className="micro-label mb-2 text-kairo-gray-400">
                ORIGINAL BLUEPRINT
              </p>
              <p className="text-sm text-kairo-gray-400">
                2D source reference
              </p>
            </div>
          </div>
        )}

        {/* Side panel */}
        <div className="w-64 flex-shrink-0 border-l border-kairo-gray-200 bg-white overflow-y-auto hidden lg:block">
          <div className="p-6 space-y-8">
            <LayerControls layers={layers} onToggle={handleLayerToggle} />

            <div className="border-t border-kairo-gray-100 pt-6">
              <SceneStats metadata={metadata} />
            </div>

            {/* Selected object info */}
            {selectedObject && (
              <div className="border-t border-kairo-gray-100 pt-6">
                <p className="micro-label mb-3">SELECTED</p>
                <p className="text-sm font-mono text-kairo-black">
                  {selectedObject}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
