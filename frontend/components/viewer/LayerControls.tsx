"use client";

import type { SceneLayer } from "@/lib/types";
import { Eye, EyeOff } from "lucide-react";

interface LayerControlsProps {
  layers: SceneLayer[];
  onToggle: (id: string) => void;
}

export function LayerControls({ layers, onToggle }: LayerControlsProps) {
  return (
    <div>
      <p className="micro-label mb-4">SCENE</p>
      <div className="space-y-1">
        {layers.map((layer) => (
          <button
            key={layer.id}
            onClick={() => onToggle(layer.id)}
            className={`
              w-full flex items-center gap-3 px-3 py-2.5 rounded-kairo text-sm transition-all
              ${layer.visible
                ? "text-kairo-black bg-kairo-offwhite"
                : "text-kairo-gray-400 hover:text-kairo-gray-600"
              }
            `}
          >
            {layer.visible ? (
              <Eye className="w-4 h-4 text-kairo-orange flex-shrink-0" />
            ) : (
              <EyeOff className="w-4 h-4 flex-shrink-0" />
            )}
            <span className="font-medium">{layer.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
