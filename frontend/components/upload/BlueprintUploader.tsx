"use client";

import { useCallback, useState, useRef } from "react";
import { Upload, FileText, X } from "lucide-react";

interface BlueprintUploaderProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export function BlueprintUploader({ onFileSelect, disabled }: BlueprintUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (disabled) return;
      const file = e.dataTransfer.files[0];
      if (file) onFileSelect(file);
    },
    [onFileSelect, disabled]
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (!disabled) setIsDragging(true);
    },
    [disabled]
  );

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) onFileSelect(file);
    },
    [onFileSelect]
  );

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      className={`
        relative border-2 border-dashed rounded-kairo p-12 lg:p-16
        flex flex-col items-center justify-center text-center
        transition-all duration-300 cursor-pointer min-h-[320px]
        ${isDragging
          ? "border-kairo-orange bg-kairo-orange-light"
          : "border-kairo-gray-200 hover:border-kairo-gray-400 bg-white"
        }
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}
      `}
      onClick={() => !disabled && inputRef.current?.click()}
      role="button"
      tabIndex={0}
      aria-label="Upload blueprint"
      style={{
        backgroundImage: isDragging
          ? "none"
          : `
            linear-gradient(rgba(0,0,0,0.015) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,0,0,0.015) 1px, transparent 1px)
          `,
        backgroundSize: "20px 20px",
      }}
    >
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept=".png,.jpg,.jpeg,.pdf"
        onChange={handleChange}
        disabled={disabled}
      />

      <div className="w-14 h-14 rounded-full border-2 border-kairo-gray-200 flex items-center justify-center mb-6">
        <Upload className="w-6 h-6 text-kairo-gray-400" />
      </div>

      <h3 className="text-lg font-semibold text-kairo-black mb-2">
        Upload Blueprint
      </h3>
      <p className="text-sm text-kairo-gray-500 mb-6">
        Drag & drop your blueprint or browse files
      </p>

      <p className="micro-label text-kairo-gray-400">
        PNG · JPG · JPEG · PDF
      </p>

      <button
        className="btn-outline mt-8 text-sm px-6 py-2.5"
        onClick={(e) => {
          e.stopPropagation();
          inputRef.current?.click();
        }}
        disabled={disabled}
      >
        Choose File
      </button>
    </div>
  );
}

// ── Blueprint Preview ──

interface BlueprintPreviewProps {
  file: File;
  previewUrl: string | null;
  onReplace: () => void;
}

export function BlueprintPreview({ file, previewUrl, onReplace }: BlueprintPreviewProps) {
  const sizeKB = (file.size / 1024).toFixed(1);
  const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
  const sizeStr = file.size > 1024 * 1024 ? `${sizeMB} MB` : `${sizeKB} KB`;
  const ext = file.name.split(".").pop()?.toUpperCase() || "FILE";

  return (
    <div className="border border-kairo-gray-200 rounded-kairo overflow-hidden bg-white">
      <div className="p-4 flex items-center justify-between border-b border-kairo-gray-100">
        <p className="micro-label">BLUEPRINT</p>
        <button
          onClick={onReplace}
          className="text-kairo-gray-400 hover:text-kairo-black transition-colors p-1"
          aria-label="Remove file"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Preview */}
      <div className="bg-kairo-offwhite flex items-center justify-center min-h-[240px] p-4">
        {previewUrl ? (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img
            src={previewUrl}
            alt="Blueprint preview"
            className="max-h-[300px] w-auto object-contain"
          />
        ) : (
          <div className="flex flex-col items-center gap-3 text-kairo-gray-400">
            <FileText className="w-12 h-12" />
            <p className="text-sm">Preview not available</p>
          </div>
        )}
      </div>

      {/* File info */}
      <div className="p-4 flex items-center gap-4">
        <div className="w-10 h-10 rounded-kairo bg-kairo-offwhite flex items-center justify-center">
          <FileText className="w-5 h-5 text-kairo-gray-500" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-kairo-black truncate">
            {file.name}
          </p>
          <p className="text-xs text-kairo-gray-500">
            {sizeStr} · {ext}
          </p>
        </div>
        <button
          onClick={onReplace}
          className="text-sm text-kairo-gray-500 hover:text-kairo-black transition-colors"
        >
          Replace
        </button>
      </div>
    </div>
  );
}
