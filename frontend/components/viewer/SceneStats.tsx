import type { ReconstructionMetadata } from "@/lib/types";

interface SceneStatsProps {
  metadata: ReconstructionMetadata | null;
}

export function SceneStats({ metadata }: SceneStatsProps) {
  if (!metadata) return null;

  const stats = [
    { label: "Rooms", value: metadata.rooms },
    { label: "Walls", value: metadata.walls },
    { label: "Doors", value: metadata.doors },
    { label: "Windows", value: metadata.windows },
  ];

  return (
    <div>
      <p className="micro-label mb-4">INSPECT</p>
      <div className="space-y-3">
        {stats.map((s) => (
          <div key={s.label} className="flex items-center justify-between">
            <span className="text-sm text-kairo-gray-500">{s.label}</span>
            <span className="text-sm font-semibold text-kairo-black tabular-nums">
              {String(s.value).padStart(2, "0")}
            </span>
          </div>
        ))}

        {metadata.scale_mm_per_px != null && (
          <div className="pt-3 mt-3 border-t border-kairo-gray-100">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase tracking-wider text-kairo-gray-400">
                Scale
              </span>
              <span className="text-sm font-mono text-kairo-orange">
                {metadata.scale_mm_per_px.toFixed(2)} mm/px
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
