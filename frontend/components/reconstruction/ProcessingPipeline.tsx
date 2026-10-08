"use client";

import type { PipelineStage } from "@/lib/types";
import { Check } from "lucide-react";

interface ProcessingPipelineProps {
  stages: PipelineStage[];
  fileName?: string;
}

export function ProcessingPipeline({ stages, fileName }: ProcessingPipelineProps) {
  const currentStage = stages.find((s) => s.status === "active");
  const completedCount = stages.filter((s) => s.status === "completed").length;

  return (
    <div className="grid lg:grid-cols-3 gap-8">
      {/* Pipeline stages */}
      <div className="lg:col-span-2">
        <div className="border border-kairo-gray-200 rounded-kairo p-6 bg-white">
          <p className="micro-label mb-6">PIPELINE</p>

          <div className="space-y-1">
            {stages.map((stage) => (
              <div
                key={stage.id}
                className={`
                  flex items-center gap-4 py-3 px-4 rounded-kairo transition-all duration-300
                  ${stage.status === "active" ? "bg-kairo-orange-light" : ""}
                `}
              >
                {/* Status indicator */}
                <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center">
                  {stage.status === "completed" ? (
                    <div className="w-7 h-7 rounded-full bg-kairo-black flex items-center justify-center">
                      <Check className="w-3.5 h-3.5 text-white" />
                    </div>
                  ) : stage.status === "active" ? (
                    <div className="w-7 h-7 rounded-full bg-kairo-orange flex items-center justify-center animate-pulse-subtle">
                      <div className="w-2 h-2 rounded-full bg-white" />
                    </div>
                  ) : stage.status === "failed" ? (
                    <div className="w-7 h-7 rounded-full bg-red-500 flex items-center justify-center">
                      <span className="text-white text-xs font-bold">!</span>
                    </div>
                  ) : (
                    <div className="w-7 h-7 rounded-full border-2 border-kairo-gray-200" />
                  )}
                </div>

                {/* Stage number */}
                <span
                  className={`text-xs font-mono w-6 flex-shrink-0 ${
                    stage.status === "active"
                      ? "text-kairo-orange font-bold"
                      : stage.status === "completed"
                      ? "text-kairo-black"
                      : "text-kairo-gray-400"
                  }`}
                >
                  {stage.number}
                </span>

                {/* Stage label */}
                <span
                  className={`text-sm ${
                    stage.status === "active"
                      ? "text-kairo-orange font-semibold"
                      : stage.status === "completed"
                      ? "text-kairo-black font-medium"
                      : "text-kairo-gray-400"
                  }`}
                >
                  {stage.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Processing details */}
      <div className="lg:col-span-1">
        <div className="border border-kairo-gray-200 rounded-kairo p-6 bg-white">
          <p className="micro-label mb-6">PROCESSING</p>

          <div className="space-y-5">
            <DetailRow label="Input" value={fileName || "—"} />
            <DetailRow label="Engine" value="KAIRO MGR" />
            <DetailRow
              label="Geometry"
              value={completedCount >= 3 ? "Extracted" : "Pending"}
            />
            <DetailRow
              label="Scale"
              value={
                completedCount >= 4
                  ? "Estimated"
                  : currentStage?.id === "dim"
                  ? "Analyzing"
                  : "Pending"
              }
            />
            <DetailRow
              label="Topology"
              value={completedCount >= 6 ? "Resolved" : "Pending"}
            />
            <DetailRow
              label="Output"
              value={completedCount >= 8 ? "scene.glb" : "—"}
              highlight={completedCount >= 8}
            />
          </div>

          {/* Progress bar */}
          <div className="mt-8 pt-6 border-t border-kairo-gray-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-kairo-gray-500">Progress</span>
              <span className="text-xs font-mono text-kairo-gray-600">
                {completedCount}/{stages.length}
              </span>
            </div>
            <div className="h-1 bg-kairo-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-kairo-orange rounded-full transition-all duration-500"
                style={{ width: `${(completedCount / stages.length) * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function DetailRow({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs uppercase tracking-wider text-kairo-gray-400">
        {label}
      </span>
      <span
        className={`text-sm font-mono ${
          highlight ? "text-kairo-orange font-medium" : "text-kairo-gray-700"
        }`}
      >
        {value}
      </span>
    </div>
  );
}
