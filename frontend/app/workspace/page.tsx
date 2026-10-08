"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  BlueprintUploader,
  BlueprintPreview,
} from "@/components/upload/BlueprintUploader";
import { ProcessingPipeline } from "@/components/reconstruction/ProcessingPipeline";
import {
  ArrowRight,
  Download,
  AlertTriangle,
  RotateCw,
  Box,
  Building2,
  Compass,
  ShieldCheck,
  Sparkles,
  CheckCircle2,
  FileText,
} from "lucide-react";
import type { PipelineStage, ReconstructionMetadata } from "@/lib/types";
import { submitReconstruction, getJobStatus, getMetadata, getModel } from "@/lib/api";
import { USE_MOCK, MOCK_METADATA, MOCK_ROOMS, createMockPipeline } from "@/lib/mock";
import { useAuth } from "@/lib/auth-context";
import { saveDbReconstruction, uploadBlueprintFile } from "@/lib/supabase";

type WorkspaceState = "upload" | "preview" | "processing" | "completed" | "failed";

export default function WorkspacePage() {
  const router = useRouter();
  const { user } = useAuth();
  const [state, setState] = useState<WorkspaceState>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [pipeline, setPipeline] = useState<PipelineStage[]>(createMockPipeline());
  const [metadata, setMetadata] = useState<ReconstructionMetadata>(MOCK_METADATA);
  const [modelUrl, setModelUrl] = useState<string | null>("/sample.glb");
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = useCallback((f: File) => {
    setFile(f);
    setState("preview");
    setError(null);

    // Generate image preview
    if (f.type.startsWith("image/")) {
      const url = URL.createObjectURL(f);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
  }, []);

  const handleReplace = useCallback(() => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(null);
    setPreviewUrl(null);
    setState("upload");
    setError(null);
  }, [previewUrl]);

  // Load a sample preset blueprint
  const handleLoadSample = (sampleName: string) => {
    const dummyBlob = new Blob(["sample-blueprint-content"], { type: "image/png" });
    const dummyFile = new File([dummyBlob], `${sampleName.toLowerCase().replace(/\s+/g, "_")}.png`, {
      type: "image/png",
    });
    setFile(dummyFile);
    setState("preview");
    setError(null);
  };

  // ── Mock pipeline simulation ──
  const simulatePipeline = useCallback(() => {
    const stages = createMockPipeline();
    setPipeline(stages);

    const generatedId = `rec-${Date.now().toString(36)}`;
    setJobId(generatedId);

    const advanceStage = (index: number) => {
      if (index >= stages.length) {
        setMetadata(MOCK_METADATA);
        setModelUrl("/sample.glb");
        setState("completed");

        // Save reconstruction to Supabase DB
        saveDbReconstruction({
          id: generatedId,
          name: file?.name ? file.name.replace(/\.[^/.]+$/, "") : "Spatial Reconstruction",
          status: "completed",
          userId: user?.id,
          modelUrl: "/sample.glb",
          metadata: MOCK_METADATA,
        });
        return;
      }

      setPipeline((prev) =>
        prev.map((s, i) => ({
          ...s,
          status:
            i < index
              ? "completed"
              : i === index
              ? "active"
              : "pending",
        }))
      );

      setTimeout(() => advanceStage(index + 1), 700 + Math.random() * 400);
    };

    setTimeout(() => advanceStage(0), 400);
  }, [file?.name, user?.id]);

  // ── Real pipeline with polling ──
  const startReconstruction = useCallback(async () => {
    if (!file) return;
    setState("processing");
    setPipeline(createMockPipeline());
    setError(null);

    // Optionally upload to Supabase storage in background
    uploadBlueprintFile(file, `blueprints/${Date.now()}_${file.name}`).catch(() => {});

    if (USE_MOCK) {
      simulatePipeline();
      return;
    }

    try {
      const { job_id } = await submitReconstruction(file);
      setJobId(job_id);

      // Start polling
      const pollInterval = setInterval(async () => {
        try {
          const status = await getJobStatus(job_id);

          if (status.status === "completed") {
            clearInterval(pollInterval);
            const [meta, model] = await Promise.all([
              getMetadata(job_id),
              getModel(job_id),
            ]);
            setMetadata(meta.metadata);
            setModelUrl(model.model_url);
            setPipeline((prev) =>
              prev.map((s) => ({ ...s, status: "completed" as const }))
            );
            setState("completed");

            // Save completed reconstruction to Supabase DB
            saveDbReconstruction({
              id: job_id,
              name: file.name.replace(/\.[^/.]+$/, ""),
              status: "completed",
              userId: user?.id,
              modelUrl: model.model_url,
              metadata: meta.metadata,
            });
          } else if (status.status === "failed") {
            clearInterval(pollInterval);
            setState("failed");
            setError("KAIRO could not reliably process this blueprint.");
            saveDbReconstruction({
              id: job_id,
              name: file.name.replace(/\.[^/.]+$/, ""),
              status: "failed",
              userId: user?.id,
            });
          }
        } catch {
          clearInterval(pollInterval);
          setState("failed");
          setError("Lost connection to the reconstruction engine.");
        }
      }, 3000);
    } catch {
      setState("failed");
      setError("Failed to start reconstruction. Please check the backend connection.");
    }
  }, [file, simulatePipeline, user?.id]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  return (
    <div className="p-6 lg:p-10 max-w-7xl mx-auto w-full animate-fade-in space-y-8">
      {/* ── Main Two-Column Split Layout ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-start">
        {/* ── LEFT COLUMN: Left-Aligned Header & Blueprint Uploader ── */}
        <div className="space-y-6">
          {/* Left-Aligned Header */}
          <div className="text-left space-y-2">
            <p className="micro-label text-kairo-orange font-semibold">
              NEW RECONSTRUCTION
            </p>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight text-kairo-black">
              Upload an architectural blueprint
            </h1>
            <p className="text-sm text-kairo-gray-500 leading-relaxed">
              to generate a metric 3D environment.
            </p>
          </div>

          {/* Upload State */}
          {state === "upload" && (
            <div className="space-y-4">
              <BlueprintUploader onFileSelect={handleFileSelect} />

              {/* Sample Presets */}
              <div className="p-4 rounded-kairo bg-white border border-kairo-gray-200 space-y-2.5 shadow-2xs">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono uppercase tracking-wider text-kairo-gray-500 font-semibold">
                    Test with Sample Blueprints
                  </span>
                  <span className="text-[10px] text-kairo-orange font-medium flex items-center gap-1">
                    <Sparkles className="w-3 h-3" />
                    1-Click Load
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    "Villa Floorplan",
                    "Modern Apartment",
                    "Executive Office",
                  ].map((name) => (
                    <button
                      key={name}
                      type="button"
                      onClick={() => handleLoadSample(name)}
                      className="p-2.5 rounded bg-kairo-offwhite hover:bg-orange-50/40 border border-kairo-gray-200 hover:border-kairo-orange/40 text-left transition-all group"
                    >
                      <p className="text-xs font-semibold text-kairo-black group-hover:text-kairo-orange truncate">
                        {name}
                      </p>
                      <p className="text-[9px] text-kairo-gray-400 mt-0.5">
                        2D CAD Plan
                      </p>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Preview State */}
          {state === "preview" && file && (
            <div className="space-y-5">
              <BlueprintPreview
                file={file}
                previewUrl={previewUrl}
                onReplace={handleReplace}
              />

              <div className="p-5 rounded-kairo bg-white border border-kairo-gray-200 space-y-4 shadow-2xs">
                <div className="flex items-center justify-between text-xs text-kairo-gray-500 pb-3 border-b border-kairo-gray-100">
                  <span className="font-semibold text-kairo-black">Pipeline Specification</span>
                  <span className="font-mono text-kairo-orange font-semibold">25.4 mm/px Calibrated</span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-2.5 rounded bg-kairo-offwhite border border-kairo-gray-100">
                    <p className="text-[10px] text-kairo-gray-400 uppercase font-mono">Input Document</p>
                    <p className="font-semibold text-kairo-black truncate mt-0.5">{file.name}</p>
                  </div>
                  <div className="p-2.5 rounded bg-kairo-offwhite border border-kairo-gray-100">
                    <p className="text-[10px] text-kairo-gray-400 uppercase font-mono">Reconstruction Engine</p>
                    <p className="font-semibold text-kairo-black mt-0.5">KAIRO MGR v2.4</p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={startReconstruction}
                  className="btn-primary w-full text-xs font-semibold uppercase tracking-wider py-3.5 flex items-center justify-center gap-2 shadow-sm"
                >
                  <span>Begin Metric Reconstruction</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* Processing State */}
          {state === "processing" && (
            <div className="space-y-4">
              <div className="p-4 rounded-kairo bg-white border border-kairo-gray-200 shadow-2xs">
                <ProcessingPipeline stages={pipeline} fileName={file?.name} />
              </div>
            </div>
          )}

          {/* Completed State Left Summary */}
          {state === "completed" && (
            <div className="p-6 rounded-kairo bg-white border border-kairo-gray-200 space-y-5 shadow-2xs">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-kairo-black">
                    Reconstruction Successfully Compiled
                  </h3>
                  <p className="text-xs text-kairo-gray-500">
                    Binary spatial model and geometric graph ready.
                  </p>
                </div>
              </div>

              <div className="pt-2 flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setState("upload");
                    setFile(null);
                    setPreviewUrl(null);
                  }}
                  className="btn-outline flex-1 text-xs py-3 justify-center"
                >
                  Reconstruct Another Plan
                </button>
              </div>
            </div>
          )}

          {/* Failed State Left Summary */}
          {state === "failed" && (
            <div className="p-6 rounded-kairo bg-white border border-red-200 space-y-4 shadow-2xs">
              <div className="flex items-center gap-3 text-red-600">
                <AlertTriangle className="w-6 h-6 shrink-0" />
                <div>
                  <h3 className="text-sm font-bold text-red-800">
                    Reconstruction Engine Alert
                  </h3>
                  <p className="text-xs text-red-600 mt-0.5">
                    {error || "KAIRO could not reliably extract metric graph."}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  setState("preview");
                  setError(null);
                }}
                className="btn-primary text-xs py-2.5 px-4"
              >
                <RotateCw className="w-3.5 h-3.5" />
                <span>Retry Synthesis</span>
              </button>
            </div>
          )}
        </div>

        {/* ── RIGHT COLUMN: Result of Analysis & 3D Spatial Viewer Button ── */}
        <div className="space-y-6">
          <div className="p-6 rounded-kairo bg-white border border-kairo-gray-200 space-y-6 shadow-sm">
            {/* Analysis Header */}
            <div className="flex items-center justify-between pb-4 border-b border-kairo-gray-100">
              <div>
                <p className="micro-label text-kairo-gray-400 mb-0.5">ANALYSIS REPORT</p>
                <h3 className="text-lg font-bold text-kairo-black tracking-tight">
                  Result of the Analysis
                </h3>
              </div>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-mono font-semibold uppercase">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                {state === "completed" ? "Synthesized" : state === "processing" ? "Calibrating" : "Ready"}
              </span>
            </div>

            {/* Primary Action Button: 3D SPATIAL VIEWER */}
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => router.push(`/scene/${jobId || "demo"}`)}
                className="btn-primary w-full text-xs font-semibold uppercase tracking-wider py-4 flex items-center justify-center gap-2.5 shadow-md hover:shadow-lg transition-all"
              >
                <Box className="w-4 h-4" />
                <span>Open 3D Spatial Viewer</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </button>

              {modelUrl && (
                <div className="flex gap-2 pt-1">
                  <a
                    href={modelUrl}
                    download="reconstructed_scene.glb"
                    className="btn-outline flex-1 text-xs py-2.5 justify-center flex items-center gap-1.5 text-kairo-gray-600 hover:text-kairo-black"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download GLB</span>
                  </a>

                  <Link
                    href="/history"
                    className="btn-outline flex-1 text-xs py-2.5 justify-center flex items-center gap-1.5 text-kairo-gray-600 hover:text-kairo-black"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>View In Archive</span>
                  </Link>
                </div>
              )}
            </div>

            {/* Metrics Breakdown Grid */}
            <div className="grid grid-cols-4 gap-3 pt-2">
              <div className="p-3.5 rounded-kairo bg-kairo-offwhite border border-kairo-gray-200 text-center">
                <p className="text-xl font-bold text-kairo-black">
                  {String(metadata.rooms).padStart(2, "0")}
                </p>
                <p className="text-[10px] font-mono uppercase tracking-wider text-kairo-gray-500 mt-0.5">
                  Rooms
                </p>
              </div>

              <div className="p-3.5 rounded-kairo bg-kairo-offwhite border border-kairo-gray-200 text-center">
                <p className="text-xl font-bold text-kairo-black">
                  {String(metadata.walls).padStart(2, "0")}
                </p>
                <p className="text-[10px] font-mono uppercase tracking-wider text-kairo-gray-500 mt-0.5">
                  Walls
                </p>
              </div>

              <div className="p-3.5 rounded-kairo bg-kairo-offwhite border border-kairo-gray-200 text-center">
                <p className="text-xl font-bold text-kairo-black">
                  {String(metadata.doors).padStart(2, "0")}
                </p>
                <p className="text-[10px] font-mono uppercase tracking-wider text-kairo-gray-500 mt-0.5">
                  Doors
                </p>
              </div>

              <div className="p-3.5 rounded-kairo bg-kairo-offwhite border border-kairo-gray-200 text-center">
                <p className="text-xl font-bold text-kairo-black">
                  {String(metadata.windows).padStart(2, "0")}
                </p>
                <p className="text-[10px] font-mono uppercase tracking-wider text-kairo-gray-500 mt-0.5">
                  Windows
                </p>
              </div>
            </div>

            {/* Precision & Scale Analysis Row */}
            <div className="p-4 rounded-kairo bg-kairo-offwhite border border-kairo-gray-200 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-1.5 font-medium text-kairo-gray-600">
                  <Compass className="w-3.5 h-3.5 text-kairo-orange" />
                  Estimated Metric Scale
                </span>
                <span className="font-mono font-bold text-kairo-black">
                  {metadata.scale_mm_per_px
                    ? `${metadata.scale_mm_per_px.toFixed(2)} mm/px`
                    : "Calibrating…"}
                </span>
              </div>

              <div className="flex items-center justify-between text-xs pt-1 border-t border-kairo-gray-200/60">
                <span className="flex items-center gap-1.5 font-medium text-kairo-gray-600">
                  <ShieldCheck className="w-3.5 h-3.5 text-kairo-orange" />
                  MGR Graph Confidence
                </span>
                <span className="font-mono font-bold text-emerald-700">
                  94.8% Verified
                </span>
              </div>
            </div>

            {/* Sector Topology Breakdown */}
            <div className="space-y-3 pt-1">
              <div className="flex items-center justify-between text-xs font-semibold text-kairo-black">
                <span className="flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-kairo-orange" />
                  <span>Detected Room Sectors</span>
                </span>
                <span className="font-mono text-kairo-gray-400 text-[11px]">
                  5 Sectors
                </span>
              </div>

              <div className="space-y-2">
                {MOCK_ROOMS.map((room) => (
                  <div
                    key={room.id}
                    className="flex items-center justify-between text-xs p-2 rounded bg-kairo-offwhite border border-kairo-gray-100"
                  >
                    <span className="font-medium text-kairo-gray-700">
                      {room.label}
                    </span>
                    <div className="flex items-center gap-3">
                      <div className="w-16 h-1.5 bg-kairo-gray-200 rounded-full overflow-hidden hidden sm:block">
                        <div
                          className="h-full bg-kairo-orange"
                          style={{
                            width: `${Math.min(100, (room.area_m2 / 24) * 100)}%`,
                          }}
                        />
                      </div>
                      <span className="font-mono font-bold text-kairo-black text-[11px]">
                        {room.area_m2} m²
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
