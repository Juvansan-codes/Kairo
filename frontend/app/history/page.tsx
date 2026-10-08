"use client";

import { useState, useMemo, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Search,
  XCircle,
  RotateCw,
  Plus,
  RefreshCw,
  Box,
  Building2,
  X,
} from "lucide-react";
import type { Reconstruction, ReconstructionStatus } from "@/lib/types";
import { MOCK_HISTORY, USE_MOCK } from "@/lib/mock";
import { getDbReconstructions, isSupabaseConfigured } from "@/lib/supabase";
import { useAuth } from "@/lib/auth-context";

type FilterStatus = "all" | ReconstructionStatus;

export default function HistoryPage() {
  const { user } = useAuth();
  const [filter, setFilter] = useState<FilterStatus>("all");
  const [search, setSearch] = useState("");
  const [items, setItems] = useState<Reconstruction[]>(MOCK_HISTORY);
  const [loading, setLoading] = useState(false);

  const loadData = useCallback(async () => {
    if (!isSupabaseConfigured) {
      setItems(MOCK_HISTORY);
      return;
    }
    setLoading(true);
    try {
      const dbItems = await getDbReconstructions(user?.id);
      if (dbItems && dbItems.length > 0) {
        setItems(dbItems);
      } else if (USE_MOCK) {
        setItems(MOCK_HISTORY);
      } else {
        setItems([]);
      }
    } catch {
      setItems(MOCK_HISTORY);
    } finally {
      setLoading(false);
    }
  }, [user?.id]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const filtered = useMemo(() => {
    let result = [...items];
    if (filter !== "all") {
      result = result.filter((r) => r.status === filter);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (r) =>
          r.name.toLowerCase().includes(q) ||
          r.id.toLowerCase().includes(q)
      );
    }
    return result.sort(
      (a, b) =>
        new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  }, [items, filter, search]);

  const completedCount = items.filter((i) => i.status === "completed").length;
  const failedCount = items.filter((i) => i.status === "failed").length;

  const filterOptions: { value: FilterStatus; label: string; count: number }[] =
    [
      { value: "all", label: "All", count: items.length },
      { value: "completed", label: "Completed", count: completedCount },
      { value: "failed", label: "Failed", count: failedCount },
    ];

  return (
    <div className="p-6 lg:p-10 max-w-6xl mx-auto w-full animate-fade-in">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-10">
        <div>
          <p className="text-[11px] font-mono font-semibold uppercase tracking-widest text-kairo-orange mb-1">
            Archive
          </p>
          <h1 className="text-2xl font-bold tracking-tight text-kairo-black">
            Reconstruction History
          </h1>
          <p className="text-sm text-kairo-gray-500 mt-1">
            Previously generated spatial models &amp; geometric assets.
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <button
            onClick={() => loadData()}
            disabled={loading}
            className="h-9 w-9 flex items-center justify-center border border-kairo-gray-200 rounded-kairo bg-white text-kairo-gray-500 hover:text-kairo-black hover:border-kairo-gray-400 transition-colors"
            title="Refresh"
          >
            <RefreshCw
              className={`w-4 h-4 ${loading ? "animate-spin text-kairo-orange" : ""}`}
            />
          </button>
          <Link
            href="/workspace"
            className="btn-primary text-xs h-9 px-4 font-semibold uppercase tracking-wider inline-flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            New Reconstruction
          </Link>
        </div>
      </div>

      {/* ── Search + Filters ── */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 mb-6">
        <div className="relative max-w-sm w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-kairo-gray-400" />
          <input
            type="text"
            placeholder="Search by name or ID…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full h-9 pl-9 pr-8 bg-white border border-kairo-gray-200 rounded-kairo text-sm text-kairo-black placeholder:text-kairo-gray-400 focus:border-kairo-orange focus:outline-none transition-colors"
          />
          {search && (
            <button
              onClick={() => setSearch("")}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-kairo-gray-400 hover:text-kairo-black"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center p-0.5 bg-kairo-offwhite border border-kairo-gray-200 rounded-kairo">
            {filterOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setFilter(opt.value)}
                className={`h-8 px-3 text-xs font-medium rounded transition-all ${
                  filter === opt.value
                    ? "bg-white text-kairo-black shadow-sm"
                    : "text-kairo-gray-500 hover:text-kairo-black"
                }`}
              >
                {opt.label}
                <span className="ml-1.5 text-[10px] font-mono text-kairo-gray-400">
                  {opt.count}
                </span>
              </button>
            ))}
          </div>

          <span className="text-xs text-kairo-gray-400 font-mono hidden md:inline whitespace-nowrap">
            {filtered.length} of {items.length} records
          </span>
        </div>
      </div>

      {/* ── Table ── */}
      {filtered.length === 0 ? (
        <EmptyState
          hasItems={items.length > 0}
          onReset={() => {
            setSearch("");
            setFilter("all");
          }}
        />
      ) : (
        <div className="border border-kairo-gray-200 rounded-kairo bg-white overflow-hidden">
          {/* Header */}
          <div className="hidden lg:grid grid-cols-12 gap-4 px-6 py-3 border-b border-kairo-gray-200 bg-kairo-offwhite">
            <div className="col-span-4 text-[11px] font-mono font-semibold uppercase tracking-wider text-kairo-gray-500">
              Project
            </div>
            <div className="col-span-2 text-[11px] font-mono font-semibold uppercase tracking-wider text-kairo-gray-500">
              Date
            </div>
            <div className="col-span-3 text-[11px] font-mono font-semibold uppercase tracking-wider text-kairo-gray-500">
              Topology
            </div>
            <div className="col-span-1 text-[11px] font-mono font-semibold uppercase tracking-wider text-kairo-gray-500">
              Status
            </div>
            <div className="col-span-2 text-[11px] font-mono font-semibold uppercase tracking-wider text-kairo-gray-500 text-right">
              Actions
            </div>
          </div>

          {/* Rows */}
          <div className="divide-y divide-kairo-gray-100">
            {filtered.map((rec) => (
              <HistoryRow key={rec.id} reconstruction={rec} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ───────────────────────────────────────────────────── */
/*  Table Row                                            */
/* ───────────────────────────────────────────────────── */

function HistoryRow({
  reconstruction: rec,
}: {
  reconstruction: Reconstruction;
}) {
  const dateStr = new Date(rec.createdAt).toLocaleDateString("en-US", {
    month: "short",
    day: "2-digit",
    year: "numeric",
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-y-2 gap-x-4 items-center px-6 py-5 hover:bg-kairo-offwhite/60 transition-colors group">
      {/* ── Project ── */}
      <div className="lg:col-span-4 flex items-center gap-3">
        <div className="w-9 h-9 rounded-kairo bg-kairo-offwhite border border-kairo-gray-200 flex items-center justify-center shrink-0 group-hover:border-kairo-orange/30 transition-colors">
          <Building2 className="w-4 h-4 text-kairo-orange" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-kairo-black truncate">
            {rec.name}
          </p>
          <p className="text-[11px] font-mono text-kairo-gray-400 mt-0.5">
            {rec.id}
          </p>
        </div>
      </div>

      {/* ── Date ── */}
      <div className="lg:col-span-2">
        <span className="text-sm font-mono text-kairo-gray-600">
          {dateStr}
        </span>
      </div>

      {/* ── Topology ── */}
      <div className="lg:col-span-3">
        {rec.metadata ? (
          <div className="flex items-center gap-4 text-sm text-kairo-gray-700">
            <span>
              <span className="font-semibold text-kairo-black">
                {rec.metadata.rooms}
              </span>{" "}
              Rooms
            </span>
            <span className="text-kairo-gray-300">·</span>
            <span>
              <span className="font-semibold text-kairo-black">
                {rec.metadata.walls}
              </span>{" "}
              Walls
            </span>
            {rec.metadata.scale_mm_per_px && (
              <>
                <span className="text-kairo-gray-300">·</span>
                <span className="text-xs font-mono text-kairo-gray-500">
                  {rec.metadata.scale_mm_per_px.toFixed(1)}&thinsp;mm/px
                </span>
              </>
            )}
          </div>
        ) : (
          <span className="text-sm text-kairo-gray-400">—</span>
        )}
      </div>

      {/* ── Status ── */}
      <div className="lg:col-span-1">
        <StatusBadge status={rec.status} />
      </div>

      {/* ── Actions ── */}
      <div className="lg:col-span-2 flex items-center justify-start lg:justify-end gap-2">
        {rec.status === "completed" ? (
          <Link
            href={`/scene/${rec.id}`}
            className="inline-flex items-center gap-1.5 h-8 px-3.5 bg-kairo-orange text-white text-xs font-semibold rounded-kairo hover:bg-kairo-orange-hover transition-colors"
          >
            <Box className="w-3.5 h-3.5" />
            Inspect in 3D
          </Link>
        ) : rec.status === "failed" ? (
          <Link
            href="/workspace"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-kairo-orange hover:underline"
          >
            <RotateCw className="w-3.5 h-3.5" />
            Retry Synthesis
          </Link>
        ) : (
          <span className="text-xs text-kairo-gray-400 font-mono">
            Processing…
          </span>
        )}
      </div>
    </div>
  );
}

/* ───────────────────────────────────────────────────── */
/*  Status Badge                                         */
/* ───────────────────────────────────────────────────── */

function StatusBadge({ status }: { status: ReconstructionStatus }) {
  if (status === "completed") {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-700">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
        Complete
      </span>
    );
  }
  if (status === "failed") {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-red-600">
        <XCircle className="w-3.5 h-3.5" />
        Failed
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-amber-600">
      <RotateCw className="w-3.5 h-3.5 animate-spin" />
      Running
    </span>
  );
}

/* ───────────────────────────────────────────────────── */
/*  Empty State                                          */
/* ───────────────────────────────────────────────────── */

function EmptyState({
  hasItems,
  onReset,
}: {
  hasItems: boolean;
  onReset: () => void;
}) {
  return (
    <div className="text-center py-24 bg-white border border-kairo-gray-200 rounded-kairo">
      <div className="w-12 h-12 rounded-full bg-kairo-offwhite flex items-center justify-center mx-auto mb-4 border border-kairo-gray-200">
        <Building2 className="w-5 h-5 text-kairo-gray-400" />
      </div>
      <h3 className="text-sm font-semibold text-kairo-black mb-1">
        {hasItems ? "No matching results" : "No reconstructions yet"}
      </h3>
      <p className="text-xs text-kairo-gray-500 mb-6 max-w-xs mx-auto">
        {hasItems
          ? "Try adjusting your search or filters."
          : "Upload a blueprint to generate your first 3D spatial model."}
      </p>
      {hasItems ? (
        <button onClick={onReset} className="btn-outline text-xs px-4 py-2">
          Clear Filters
        </button>
      ) : (
        <Link
          href="/workspace"
          className="btn-primary text-xs px-5 py-2.5 inline-flex items-center gap-1.5"
        >
          <Plus className="w-3.5 h-3.5" />
          Upload Blueprint
        </Link>
      )}
    </div>
  );
}
