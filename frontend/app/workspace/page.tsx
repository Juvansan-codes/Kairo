"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  BlueprintUploader,
  BlueprintPreview,
} from "@/components/upload/BlueprintUploader";
import { ProcessingPipeline } from "@/components/reconstruction/ProcessingPipeline";
import { ArrowRight, Download, ExternalLink, AlertTriangle, RotateCw } from "lucide-react";
import type { PipelineStage, ReconstructionMetadata } from "@/lib/types";
import { submitReconstruction, getJobStatus, getMetadata, getModel } from "@/lib/api";
import { USE_MOCK, MOCK_METADATA, createMockPipeline } from "@/lib/mock";
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
  const [metadata, setMetadata] = useState<ReconstructionMetadata | null>(null);
  const [modelUrl, setModelUrl] = useState<string | null>(null);
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

      setTimeout(() => advanceStage(index + 1), 800 + Math.random() * 600);
    };

    setTimeout(() => advanceStage(0), 500);
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
    <div className="mx-auto max-w-6xl px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-10">
        <p className="micro-label mb-3 text-kairo-orange">
          {state === "processing"
            ? "RECONSTRUCTING"
            : state === "completed"
            ? "RECONSTRUCTION COMPLETE"
            : state === "failed"
            ? "RECONSTRUCTION FAILED"
            : "NEW RECONSTRUCTION"}
        </p>
        <h1 className="text-2xl lg:text-3xl font-bold text-kairo-black">
          {state === "processing"
            ? "Processing your blueprint…"
            : state === "completed"
            ? "Your spatial model is ready."
            : state === "failed"
            ? "Something went wrong."
            : "Upload an architectural blueprint"}
        </h1>
        {state === "upload" && (
          <p className="text-kairo-gray-500 mt-2">
            to generate a metric 3D environment.
          </p>
        )}
      </div>

      {/* ── Upload state ── */}
      {state === "upload" && (
        <BlueprintUploader onFileSelect={handleFileSelect} />
      )}

      {/* ── Preview state ── */}
      {state === "preview" && file && (
        <div className="grid lg:grid-cols-2 gap-8">
          <BlueprintPreview
            file={file}
            previewUrl={previewUrl}
            onReplace={handleReplace}
          />

          <div className="border border-kairo-gray-200 rounded-kairo p-8 bg-white flex flex-col justify-between">
            <div>
              <p className="micro-label mb-6">RECONSTRUCTION</p>

              <div className="space-y-5 mb-8">
                <div className="flex justify-between">
                  <span className="text-sm text-kairo-gray-500">Mode</span>
                  <span className="text-sm font-medium text-kairo-black">
                    Blueprint → 3D
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-kairo-gray-500">Output</span>
                  <span className="text-sm font-mono text-kairo-black">
                    GLB + JSON
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-kairo-gray-500">Engine</span>
                  <span className="text-sm font-mono text-kairo-black">
                    KAIRO MGR
                  </span>
                </div>
              </div>
            </div>

            <button
              onClick={startReconstruction}
              className="btn-primary w-full text-base py-4"
            >
              Reconstruct Blueprint
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {/* ── Processing state ── */}
      {state === "processing" && (
        <ProcessingPipeline stages={pipeline} fileName={file?.name} />
      )}

      {/* ── Completed state ── */}
      {state === "completed" && (
        <div className="max-w-xl mx-auto text-center">
          <div className="w-16 h-16 rounded-full bg-kairo-orange flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>

          {/* Stats */}
          {metadata && (
            <div className="grid grid-cols-4 gap-4 mb-8 mt-8">
              <StatBox label="Rooms" value={metadata.rooms} />
              <StatBox label="Walls" value={metadata.walls} />
              <StatBox label="Doors" value={metadata.doors} />
              <StatBox label="Windows" value={metadata.windows} />
            </div>
          )}

          {metadata?.scale_mm_per_px && (
            <p className="text-sm text-kairo-gray-500 mb-8">
              Estimated Scale:{" "}
              <span className="font-mono text-kairo-orange">
                {metadata.scale_mm_per_px.toFixed(2)} mm/px
              </span>
            </p>
          )}

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={() => router.push(`/scene/${jobId || "demo"}`)}
              className="btn-primary text-base px-8 py-4"
            >
              Open 3D Scene
              <ExternalLink className="w-4 h-4" />
            </button>
            {modelUrl && (
              <a
                href={modelUrl}
                download
                className="btn-outline text-base px-8 py-4"
              >
                <Download className="w-4 h-4" />
                Download GLB
              </a>
            )}
          </div>
        </div>
      )}

      {/* ── Failed state ── */}
      {state === "failed" && (
        <div className="max-w-md mx-auto text-center">
          <div className="w-16 h-16 rounded-full bg-kairo-gray-100 flex items-center justify-center mx-auto mb-6">
            <AlertTriangle className="w-8 h-8 text-kairo-gray-400" />
          </div>
          <p className="text-kairo-gray-500 mb-8">
            {error || "KAIRO could not reliably process this blueprint."}
          </p>
          <button
            onClick={() => {
              setState("preview");
              setError(null);
            }}
            className="btn-primary"
          >
            <RotateCw className="w-4 h-4" />
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}

function StatBox({ label, value }: { label: string; value: number }) {
  return (
    <div className="border border-kairo-gray-200 rounded-kairo p-4 bg-white">
      <p className="text-2xl font-semibold text-kairo-black">
        {String(value).padStart(2, "0")}
      </p>
      <p className="text-[10px] uppercase tracking-wider text-kairo-gray-500 mt-1">
        {label}
      </p>
    </div>
  );
}
