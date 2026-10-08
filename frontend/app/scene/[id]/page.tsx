"use client";

import { useState, useCallback, useEffect } from "react";
import dynamic from "next/dynamic";
import { useParams, useRouter } from "next/navigation";
import { LayerControls } from "@/components/viewer/LayerControls";
import { SceneStats } from "@/components/viewer/SceneStats";
import { Download, ArrowLeft, Compass } from "lucide-react";
import type { SceneLayer, ReconstructionMetadata } from "@/lib/types";
import { USE_MOCK, MOCK_METADATA } from "@/lib/mock";

// Dynamic import to avoid SSR issues with Three.js
const SceneViewer = dynamic(
  () =>
    import("@/components/viewer/SceneViewer").then((mod) => ({
      default: mod.SceneViewer,
    })),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full min-h-[400px] flex items-center justify-center bg-kairo-gray-950 text-kairo-gray-500 font-mono text-xs">
        <div className="flex items-center gap-2">
          <div className="w-3.5 h-3.5 border-2 border-kairo-orange border-t-transparent rounded-full animate-spin" />
          <span>INITIALIZING SPATIAL CANVAS…</span>
        </div>
      </div>
    ),
  }
);

const DEFAULT_LAYERS: SceneLayer[] = [
  { id: "walls", label: "Walls", visible: true, prefix: "wall" },
  { id: "doors", label: "Doors", visible: true, prefix: "door" },
  { id: "windows", label: "Windows", visible: true, prefix: "window" },
  { id: "floor", label: "Floor", visible: true, prefix: "floor" },
  { id: "dimensions", label: "Dimensions", visible: false, prefix: "dim" },
];

function Blueprint2DViewer({ layers }: { layers: SceneLayer[] }) {
  const isVisible = (prefix: string) => {
    const l = layers.find((layer) => layer.prefix === prefix);
    return l ? l.visible : true;
  };

  const showWalls = isVisible("wall");
  const showDoors = isVisible("door");
  const showWindows = isVisible("window");
  const showDims = isVisible("dim");

  return (
    <div className="w-full h-full bg-[#0d0d0d] relative flex flex-col items-center justify-center p-6 overflow-hidden">
      {/* Background CAD Grid */}
      <div
        className="absolute inset-0 opacity-[0.05] pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(#F15A24 1px, transparent 1px),
            linear-gradient(90deg, #F15A24 1px, transparent 1px)
          `,
          backgroundSize: "24px 24px",
        }}
      />

      {/* Top Banner */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-2 px-3 py-1.5 rounded bg-black/60 border border-kairo-gray-800 text-[10px] font-mono text-kairo-gray-400">
        <Compass className="w-3 h-3 text-kairo-orange" />
        <span>2D ORTHOGRAPHIC PROJECTION</span>
      </div>

      {/* Metric SVG Architectural Drawing */}
      <svg
        viewBox="0 0 520 340"
        className="w-full max-w-2xl max-h-[75vh] select-none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Outer Boundary Dimensions */}
        {showDims && (
          <g stroke="#F15A24" strokeWidth="1" strokeDasharray="2 2" opacity="0.6">
            <line x1="40" y1="20" x2="480" y2="20" />
            <text x="240" y="15" fill="#F15A24" fontSize="10" fontFamily="monospace" textAnchor="middle">
              WIDTH: 8.00m
            </text>
            <line x1="20" y1="40" x2="20" y2="300" />
            <text x="15" y="175" fill="#F15A24" fontSize="10" fontFamily="monospace" textAnchor="middle" transform="rotate(-90 15 175)">
              LENGTH: 6.00m
            </text>
          </g>
        )}

        {/* Room Area fills */}
        <rect x="40" y="40" width="240" height="260" fill="#141414" />
        <rect x="280" y="40" width="200" height="160" fill="#181818" />
        <rect x="280" y="200" width="200" height="100" fill="#161616" />

        {/* Room Labels */}
        <text x="160" y="170" fill="#aaaaaa" fontSize="11" fontFamily="monospace" textAnchor="middle" fontWeight="bold">
          LIVING ROOM (24 m²)
        </text>
        <text x="380" y="120" fill="#aaaaaa" fontSize="11" fontFamily="monospace" textAnchor="middle" fontWeight="bold">
          BEDROOM (14 m²)
        </text>
        <text x="380" y="255" fill="#aaaaaa" fontSize="10" fontFamily="monospace" textAnchor="middle" fontWeight="bold">
          BATH / UTILITY (6 m²)
        </text>

        {/* Structural Walls */}
        {showWalls && (
          <g stroke="#ffffff" strokeWidth="3" strokeLinecap="square">
            {/* Outer Perimeter */}
            <rect x="40" y="40" width="440" height="260" fill="none" />
            {/* Interior Dividers */}
            <line x1="280" y1="40" x2="280" y2="300" />
            <line x1="280" y1="200" x2="480" y2="200" />
          </g>
        )}

        {/* Doors with CAD Swing Arcs */}
        {showDoors && (
          <g stroke="#F15A24" strokeWidth="1.5" fill="none">
            {/* Main Entrance (South) */}
            <line x1="130" y1="300" x2="165" y2="300" stroke="#0d0d0d" strokeWidth="5" />
            <line x1="130" y1="300" x2="130" y2="270" stroke="#F15A24" strokeWidth="1.5" />
            <path d="M 130 270 A 30 30 0 0 1 160 300" stroke="#F15A24" strokeWidth="1" strokeDasharray="3 2" />

            {/* Bedroom Door */}
            <line x1="280" y1="100" x2="280" y2="135" stroke="#0d0d0d" strokeWidth="5" />
            <line x1="280" y1="100" x2="310" y2="100" stroke="#F15A24" strokeWidth="1.5" />
            <path d="M 310 100 A 30 30 0 0 1 280 130" stroke="#F15A24" strokeWidth="1" strokeDasharray="3 2" />

            {/* Bathroom Door */}
            <line x1="280" y1="220" x2="280" y2="250" stroke="#0d0d0d" strokeWidth="5" />
            <line x1="280" y1="220" x2="305" y2="220" stroke="#F15A24" strokeWidth="1.5" />
            <path d="M 305 220 A 25 25 0 0 1 280 245" stroke="#F15A24" strokeWidth="1" strokeDasharray="3 2" />
          </g>
        )}

        {/* Windows */}
        {showWindows && (
          <g stroke="#64B5F6" strokeWidth="3">
            {/* Living Room North Windows */}
            <line x1="80" y1="40" x2="180" y2="40" />
            {/* Living Room West Windows */}
            <line x1="40" y1="100" x2="40" y2="200" />
            {/* Bedroom East Window */}
            <line x1="480" y1="80" x2="480" y2="150" />
          </g>
        )}

        {/* Coordinate Corner Ticks */}
        <circle cx="40" cy="40" r="3" fill="#F15A24" />
        <circle cx="480" cy="40" r="3" fill="#F15A24" />
        <circle cx="480" cy="300" r="3" fill="#F15A24" />
        <circle cx="40" cy="300" r="3" fill="#F15A24" />
      </svg>

      {/* Bottom Scale Bar */}
      <div className="absolute bottom-4 right-4 z-10 flex items-center gap-3 px-3 py-1.5 rounded bg-black/60 border border-kairo-gray-800 text-[10px] font-mono text-kairo-gray-400">
        <span>SCALE: 19.82 mm/px</span>
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
        <span>RECONSTRUCTED</span>
      </div>
    </div>
  );
}

export default function ScenePage() {
  const params = useParams();
  const router = useRouter();
  const sceneId = params.id as string;

  const [layers, setLayers] = useState<SceneLayer[]>(DEFAULT_LAYERS);
  const [selectedObject, setSelectedObject] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"3d" | "2d" | "split">("3d");

  const [metadata, setMetadata] = useState<ReconstructionMetadata | null>(USE_MOCK ? MOCK_METADATA : null);
  const [hasFailed, setHasFailed] = useState(false);
  const modelUrl = USE_MOCK || hasFailed ? null : `http://localhost:8000/api/result/${sceneId}/model`;

  useEffect(() => {
    if (!USE_MOCK) {
      fetch(`http://localhost:8000/api/result/${sceneId}/metadata`)
        .then(res => res.json())
        .then(data => {
          if (data.status === "failed") {
            setHasFailed(true);
            setMetadata(data.metadata);
          } else {
            setMetadata(data.metadata);
          }
        })
        .catch(err => {
          console.error("Failed to fetch metadata:", err);
          setHasFailed(true);
        });
    }
  }, [sceneId]);

  const handleLayerToggle = useCallback((id: string) => {
    setLayers((prev) =>
      prev.map((l) => (l.id === id ? { ...l, visible: !l.visible } : l))
    );
  }, []);

  const handleObjectClick = useCallback((name: string) => {
    setSelectedObject(name);
  }, []);

  const handleExport = useCallback(() => {
    if (modelUrl) {
      window.location.href = modelUrl;
      return;
    }
    // Export geometric scene definition as JSON
    const sceneExport = {
      id: sceneId,
      metadata,
      exportedAt: new Date().toISOString(),
      format: "kairo-spatial-scene-v2",
      layers: layers.map((l) => ({ id: l.id, label: l.label, visible: l.visible })),
    };
    const blob = new Blob([JSON.stringify(sceneExport, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `kairo-scene-${sceneId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [modelUrl, sceneId, metadata, layers]);

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
            <p className="text-xs text-kairo-gray-400">KAIRO Spatial Reconstruction</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* View mode toggle */}
          <div className="flex items-center border border-kairo-gray-200 rounded-kairo overflow-hidden">
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

          <button
            onClick={handleExport}
            className="btn-secondary text-xs px-4 py-2 inline-flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Scene</span>
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Viewport container */}
        <div className="flex-1 flex overflow-hidden">
          {/* 3D Viewport */}
          {viewMode !== "2d" && (
            <div
              className={`relative h-full ${
                viewMode === "split" ? "w-1/2 border-r border-kairo-gray-800" : "w-full"
              }`}
            >
              <SceneViewer
                modelUrl={modelUrl}
                layers={layers}
                onObjectClick={handleObjectClick}
                className="w-full h-full rounded-none"
                metadata={metadata}
                hasFailed={hasFailed}
              />
            </div>
          )}

          {/* 2D Viewport */}
          {viewMode !== "3d" && (
            <div
              className={`relative h-full ${
                viewMode === "split" ? "w-1/2" : "w-full"
              }`}
            >
              <Blueprint2DViewer layers={layers} />
            </div>
          )}
        </div>

        {/* Side panel */}
        <div className="w-64 flex-shrink-0 border-l border-kairo-gray-200 bg-white overflow-y-auto hidden lg:block">
          <div className="p-6 space-y-8">
            <LayerControls layers={layers} onToggle={handleLayerToggle} />

            <div className="border-t border-kairo-gray-100 pt-6">
              {metadata ? <SceneStats metadata={metadata} /> : <div className="text-xs text-kairo-gray-500">Loading stats...</div>}
            </div>

            {/* Selected object info */}
            {selectedObject ? (
              <div className="border-t border-kairo-gray-100 pt-6">
                <p className="micro-label mb-2 text-kairo-orange">SELECTED COMPONENT</p>
                <div className="p-2.5 bg-kairo-offwhite border border-kairo-gray-200 rounded text-xs font-mono text-kairo-black break-words">
                  {selectedObject}
                </div>
              </div>
            ) : (
              <div className="border-t border-kairo-gray-100 pt-6">
                <p className="micro-label mb-1 text-kairo-gray-400">INTERACTIVE INSPECTION</p>
                <p className="text-[11px] text-kairo-gray-400 leading-relaxed">
                  Click on any 3D wall, door, or window to inspect its geometric parameters.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
