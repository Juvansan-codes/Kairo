"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import {
  Search,
  ArrowRight,
  CheckCircle2,
  XCircle,
  RotateCw,
  Plus,
} from "lucide-react";
import type { Reconstruction, ReconstructionStatus } from "@/lib/types";
import { MOCK_HISTORY } from "@/lib/mock";

type FilterStatus = "all" | ReconstructionStatus;

export default function HistoryPage() {
  const [filter, setFilter] = useState<FilterStatus>("all");
  const [search, setSearch] = useState("");

  // In production, fetch from API. For now, use mock data.
  const history: Reconstruction[] = MOCK_HISTORY;

  const filtered = useMemo(() => {
    let items = history;
    if (filter !== "all") {
      items = items.filter((r) => r.status === filter);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      items = items.filter((r) => r.name.toLowerCase().includes(q));
    }
    return items;
  }, [history, filter, search]);

  const filterOptions: { value: FilterStatus; label: string }[] = [
    { value: "all", label: "All" },
    { value: "completed", label: "Completed" },
    { value: "failed", label: "Failed" },
  ];

  return (
    <div className="mx-auto max-w-5xl px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-10">
        <p className="micro-label mb-3 text-kairo-orange">ARCHIVE</p>
        <h1 className="text-2xl lg:text-3xl font-bold text-kairo-black">
          Reconstruction History
        </h1>
        <p className="text-kairo-gray-500 mt-2">
          Previously generated spatial models.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 mb-8">
        {/* Search */}
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-kairo-gray-400" />
          <input
            type="text"
            placeholder="Search projects…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 border border-kairo-gray-200 rounded-kairo text-sm text-kairo-black placeholder:text-kairo-gray-400 focus:border-kairo-orange focus:outline-none transition-colors"
          />
        </div>

        {/* Status filter */}
        <div className="flex items-center border border-kairo-gray-200 rounded-kairo overflow-hidden">
          {filterOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setFilter(opt.value)}
              className={`px-4 py-2.5 text-xs font-medium uppercase tracking-wider transition-colors ${
                filter === opt.value
                  ? "bg-kairo-black text-white"
                  : "text-kairo-gray-500 hover:text-kairo-black"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {filtered.length === 0 ? (
        <EmptyState hasHistory={history.length > 0} />
      ) : (
        <div className="space-y-2">
          {/* Table header */}
          <div className="hidden md:grid grid-cols-12 gap-4 px-5 py-3">
            <div className="col-span-4">
              <span className="micro-label">Project</span>
            </div>
            <div className="col-span-2">
              <span className="micro-label">Date</span>
            </div>
            <div className="col-span-2">
              <span className="micro-label">Rooms</span>
            </div>
            <div className="col-span-2">
              <span className="micro-label">Status</span>
            </div>
            <div className="col-span-2 text-right">
              <span className="micro-label">Action</span>
            </div>
          </div>

          {/* Rows */}
          {filtered.map((rec) => (
            <HistoryRow key={rec.id} reconstruction={rec} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── History Row ──

function HistoryRow({ reconstruction: rec }: { reconstruction: Reconstruction }) {
  const date = new Date(rec.createdAt);
  const dateStr = date.toLocaleDateString("en-US", {
    month: "short",
    day: "2-digit",
  });

  return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center px-5 py-4 border border-kairo-gray-200 rounded-kairo bg-white hover:border-kairo-gray-300 transition-colors">
      {/* Name */}
      <div className="md:col-span-4">
        <p className="text-sm font-semibold text-kairo-black">{rec.name}</p>
        {rec.metadata && (
          <p className="text-xs text-kairo-gray-400 mt-0.5 md:hidden">
            {rec.metadata.rooms} rooms · {rec.metadata.walls} walls
          </p>
        )}
      </div>

      {/* Date */}
      <div className="md:col-span-2 hidden md:block">
        <p className="text-sm text-kairo-gray-500">{dateStr}</p>
      </div>

      {/* Rooms */}
      <div className="md:col-span-2 hidden md:block">
        <p className="text-sm text-kairo-gray-600">
          {rec.metadata?.rooms ?? "—"}
        </p>
      </div>

      {/* Status */}
      <div className="md:col-span-2 hidden md:flex items-center gap-2">
        {rec.status === "completed" ? (
          <>
            <CheckCircle2 className="w-3.5 h-3.5 text-green-600" />
            <span className="text-xs font-medium text-green-700">Complete</span>
          </>
        ) : rec.status === "failed" ? (
          <>
            <XCircle className="w-3.5 h-3.5 text-red-500" />
            <span className="text-xs font-medium text-red-600">Failed</span>
          </>
        ) : (
          <>
            <RotateCw className="w-3.5 h-3.5 text-kairo-orange animate-spin" />
            <span className="text-xs font-medium text-kairo-orange">
              Processing
            </span>
          </>
        )}
      </div>

      {/* Action */}
      <div className="md:col-span-2 flex justify-end">
        {rec.status === "completed" ? (
          <Link
            href={`/scene/${rec.id}`}
            className="inline-flex items-center gap-1.5 text-sm font-medium text-kairo-black hover:text-kairo-orange transition-colors"
          >
            View
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        ) : rec.status === "failed" ? (
          <Link
            href="/workspace"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-kairo-gray-500 hover:text-kairo-orange transition-colors"
          >
            Retry
            <RotateCw className="w-3.5 h-3.5" />
          </Link>
        ) : null}
      </div>
    </div>
  );
}

// ── Empty State ──

function EmptyState({ hasHistory }: { hasHistory: boolean }) {
  return (
    <div className="text-center py-20">
      <div className="w-16 h-16 rounded-full bg-kairo-offwhite flex items-center justify-center mx-auto mb-6">
        <Plus className="w-6 h-6 text-kairo-gray-400" />
      </div>
      <h3 className="text-lg font-semibold text-kairo-black mb-2">
        {hasHistory ? "No matching results" : "No reconstructions yet"}
      </h3>
      <p className="text-sm text-kairo-gray-500 mb-8 max-w-xs mx-auto">
        {hasHistory
          ? "Try adjusting your search or filters."
          : "Your generated spatial models will appear here."}
      </p>
      {!hasHistory && (
        <Link href="/workspace" className="btn-primary">
          <Plus className="w-4 h-4" />
          Start Reconstruction
        </Link>
      )}
    </div>
  );
}
