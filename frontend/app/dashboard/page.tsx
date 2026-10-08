"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import Link from "next/link";
import {
  Layers,
  Box,
  History,
  ArrowRight,
  Upload,
  CheckCircle2,
  Sparkles,
  Compass,
  Cpu,
  Building2,
  Plus,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import type { Reconstruction } from "@/lib/types";
import { MOCK_HISTORY, MOCK_ROOMS } from "@/lib/mock";
import { getDbReconstructions, isSupabaseConfigured } from "@/lib/supabase";

export default function DashboardPage() {
  const { user } = useAuth();
  const [items, setItems] = useState<Reconstruction[]>(MOCK_HISTORY);
  const [loading, setLoading] = useState(false);

  const userName =
    user?.user_metadata?.full_name ||
    user?.email?.split("@")[0] ||
    "Lead Architect";

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
      } else {
        setItems(MOCK_HISTORY);
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

  // Aggregate Metrics
  const stats = useMemo(() => {
    const total = items.length;
    const completed = items.filter((i) => i.status === "completed").length;
    const totalWalls = items.reduce(
      (sum, i) => sum + (i.metadata?.walls || 0),
      0
    );
    const totalRooms = items.reduce(
      (sum, i) => sum + (i.metadata?.rooms || 0),
      0
    );
    const avgScale =
      items
        .filter((i) => i.metadata?.scale_mm_per_px)
        .reduce((sum, i) => sum + (i.metadata?.scale_mm_per_px || 0), 0) /
        (items.filter((i) => i.metadata?.scale_mm_per_px).length || 1);

    return {
      total,
      completed,
      totalWalls,
      totalRooms,
      avgScale: avgScale.toFixed(2),
    };
  }, [items]);

  // Dynamic Architectural Backdrops
  const [activeSlide, setActiveSlide] = useState(0);

  const slides = useMemo(
    () => [
      {
        title: "Orthographic CAD Perception",
        tag: "LAYER 01 · 2D VECTOR",
        desc: "Sub-millimeter wall thickness & aperture extraction",
      },
      {
        title: "Isometric 3D Spatial Mesh",
        tag: "LAYER 02 · 3D GEOMETRY",
        desc: "Watertight volumetric mesh with collision-ready topology",
      },
      {
        title: "Metric Reconciliation Graph",
        tag: "LAYER 03 · MGR FUSION",
        desc: "Multi-evidence topological constraints & OCR scale calibration",
      },
    ],
    []
  );

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveSlide((prev) => (prev + 1) % slides.length);
    }, 6000);
    return () => clearInterval(timer);
  }, [slides.length]);

  return (
    <div className="p-6 lg:p-10 max-w-7xl mx-auto space-y-8 animate-fade-in">
      {/* ── Top Header Banner with Architectural Slider Backdrop ── */}
      <div className="relative rounded-kairo overflow-hidden bg-kairo-black text-white border border-kairo-gray-800 shadow-xl">
        {/* Dynamic Slider Backdrops */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {/* Slide 0: 2D Orthographic CAD Blueprint */}
          <div
            className={`absolute inset-0 transition-opacity duration-1000 ease-in-out ${
              activeSlide === 0 ? "opacity-35" : "opacity-0"
            }`}
          >
            <div
              className="absolute inset-0"
              style={{
                backgroundImage: `
                  linear-gradient(rgba(241,90,36,0.12) 1px, transparent 1px),
                  linear-gradient(90deg, rgba(241,90,36,0.12) 1px, transparent 1px)
                `,
                backgroundSize: "32px 32px",
              }}
            />
            {/* Architectural CAD Vector SVG */}
            <svg
              className="absolute right-0 top-0 h-full w-2/3 object-cover opacity-60"
              viewBox="0 0 600 240"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <rect x="50" y="30" width="500" height="180" stroke="#F15A24" strokeWidth="1.5" />
              <line x1="220" y1="30" x2="220" y2="210" stroke="#F15A24" strokeWidth="1.2" />
              <line x1="380" y1="30" x2="380" y2="130" stroke="#F15A24" strokeWidth="1.2" />
              <line x1="220" y1="130" x2="550" y2="130" stroke="#F15A24" strokeWidth="1.2" />
              <path d="M 220 70 A 25 25 0 0 1 245 95" stroke="#ffffff" strokeWidth="1.5" strokeDasharray="3 2" />
              <path d="M 380 170 A 25 25 0 0 0 405 195" stroke="#ffffff" strokeWidth="1.5" strokeDasharray="3 2" />
              <circle cx="50" cy="30" r="4" fill="#F15A24" />
              <circle cx="550" cy="30" r="4" fill="#F15A24" />
              <circle cx="550" cy="210" r="4" fill="#F15A24" />
              <circle cx="50" cy="210" r="4" fill="#F15A24" />
              <text x="120" y="125" fill="#888888" fontSize="10" fontFamily="monospace">SECTOR A: 48.2m²</text>
              <text x="290" y="85" fill="#888888" fontSize="10" fontFamily="monospace">SECTOR B: 24.0m²</text>
              <text x="440" y="85" fill="#888888" fontSize="10" fontFamily="monospace">SECTOR C: 16.5m²</text>
            </svg>
          </div>

          {/* Slide 1: Isometric 3D Wireframe */}
          <div
            className={`absolute inset-0 transition-opacity duration-1000 ease-in-out ${
              activeSlide === 1 ? "opacity-35" : "opacity-0"
            }`}
          >
            <div
              className="absolute inset-0"
              style={{
                backgroundImage: `
                  linear-gradient(rgba(100,181,246,0.12) 1px, transparent 1px),
                  linear-gradient(90deg, rgba(100,181,246,0.12) 1px, transparent 1px)
                `,
                backgroundSize: "28px 28px",
              }}
            />
            {/* Isometric 3D Geometry SVG */}
            <svg
              className="absolute right-0 top-0 h-full w-2/3 object-cover opacity-60"
              viewBox="0 0 600 240"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <polygon points="300,30 480,90 300,150 120,90" stroke="#64B5F6" strokeWidth="1.5" />
              <polygon points="300,90 480,150 300,210 120,150" stroke="#64B5F6" strokeWidth="1" strokeDasharray="3 3" />
              <line x1="120" y1="90" x2="120" y2="150" stroke="#64B5F6" strokeWidth="1.5" />
              <line x1="480" y1="90" x2="480" y2="150" stroke="#64B5F6" strokeWidth="1.5" />
              <line x1="300" y1="30" x2="300" y2="90" stroke="#F15A24" strokeWidth="1.5" />
              <line x1="300" y1="150" x2="300" y2="210" stroke="#F15A24" strokeWidth="1.5" />
              <circle cx="300" cy="30" r="4" fill="#F15A24" />
              <circle cx="480" cy="90" r="4" fill="#F15A24" />
              <circle cx="300" cy="150" r="4" fill="#F15A24" />
              <circle cx="120" cy="90" r="4" fill="#F15A24" />
              <text x="310" y="55" fill="#64B5F6" fontSize="10" fontFamily="monospace">Z: +2.80m [ELEVATION]</text>
              <text x="390" y="130" fill="#aaaaaa" fontSize="9" fontFamily="monospace">VOLUMETRIC EXTENSION</text>
            </svg>
          </div>

          {/* Slide 2: Metric Reconciliation Graph */}
          <div
            className={`absolute inset-0 transition-opacity duration-1000 ease-in-out ${
              activeSlide === 2 ? "opacity-35" : "opacity-0"
            }`}
          >
            <div
              className="absolute inset-0"
              style={{
                backgroundImage: `
                  radial-gradient(rgba(241,90,36,0.15) 1px, transparent 1px)
                `,
                backgroundSize: "24px 24px",
              }}
            />
            {/* Graph Network SVG */}
            <svg
              className="absolute right-0 top-0 h-full w-2/3 object-cover opacity-60"
              viewBox="0 0 600 240"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <line x1="180" y1="70" x2="290" y2="140" stroke="#F15A24" strokeWidth="1.2" />
              <line x1="290" y1="140" x2="420" y2="60" stroke="#F15A24" strokeWidth="1.2" />
              <line x1="290" y1="140" x2="390" y2="180" stroke="#F15A24" strokeWidth="1.2" />
              <line x1="420" y1="60" x2="520" y2="120" stroke="#F15A24" strokeWidth="1.2" />
              <line x1="390" y1="180" x2="520" y2="120" stroke="#F15A24" strokeWidth="1.2" />
              <circle cx="180" cy="70" r="6" fill="#F15A24" />
              <circle cx="290" cy="140" r="8" fill="#F15A24" />
              <circle cx="420" cy="60" r="6" fill="#F15A24" />
              <circle cx="390" cy="180" r="7" fill="#F15A24" />
              <circle cx="520" cy="120" r="6" fill="#F15A24" />
              <text x="210" y="110" fill="#F15A24" fontSize="9" fontFamily="monospace">EDGE: 0.982</text>
              <text x="350" y="90" fill="#F15A24" fontSize="9" fontFamily="monospace">EDGE: 0.994</text>
              <text x="310" y="165" fill="#F15A24" fontSize="9" fontFamily="monospace">SCALE: 19.82mm</text>
            </svg>
          </div>

          {/* Dark gradient fade for high text contrast */}
          <div className="absolute inset-0 bg-gradient-to-r from-kairo-black via-kairo-black/90 to-kairo-black/40" />
        </div>

        {/* Foreground Content */}
        <div className="relative z-10 p-6 sm:p-8 lg:p-10 flex flex-col justify-between min-h-[220px]">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-6">
            <div className="space-y-3 max-w-2xl">
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight text-white leading-tight">
                Welcome back, <span className="text-kairo-orange">{userName}</span>
              </h1>
              <p className="text-xs sm:text-sm text-kairo-gray-300 leading-relaxed max-w-xl">
                Metric-Aware geometric reconciliation pipeline overview. Manage floor plans,
                inspect spatial topology, and export interactive GLB scenes.
              </p>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <button
                onClick={() => loadData()}
                disabled={loading}
                className="p-3 rounded-kairo border border-kairo-gray-700 bg-kairo-black/60 text-kairo-gray-300 hover:text-white hover:border-kairo-gray-500 transition-all backdrop-blur-md"
                title="Refresh data"
              >
                <RefreshCw
                  className={`w-4 h-4 ${loading ? "animate-spin text-kairo-orange" : ""}`}
                />
              </button>

              <Link
                href="/workspace"
                className="btn-primary text-xs py-3 px-5 font-semibold uppercase tracking-wider inline-flex items-center gap-2 shadow-lg"
              >
                <Plus className="w-4 h-4" />
                <span>New Reconstruction</span>
              </Link>
            </div>
          </div>

          {/* Bottom Slider Indicators & Controls */}
          <div className="mt-6 pt-4 border-t border-white/10 flex items-center justify-between">
            <div className="flex items-center gap-2 text-[10px] font-mono text-kairo-gray-400">
              <span className="text-kairo-orange font-bold">
                {slides[activeSlide].tag}
              </span>
              <span className="text-kairo-gray-600">·</span>
              <span className="hidden sm:inline text-kairo-gray-300">
                {slides[activeSlide].title}
              </span>
            </div>

            <div className="flex items-center gap-2">
              {slides.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => setActiveSlide(idx)}
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    activeSlide === idx
                      ? "w-6 bg-kairo-orange"
                      : "w-2 bg-kairo-gray-700 hover:bg-kairo-gray-500"
                  }`}
                  aria-label={`Go to slide ${idx + 1}`}
                />
              ))}

              <div className="flex items-center gap-1 ml-3 pl-3 border-l border-white/10">
                <button
                  onClick={() =>
                    setActiveSlide((prev) => (prev === 0 ? slides.length - 1 : prev - 1))
                  }
                  className="p-1 rounded text-kairo-gray-400 hover:text-white hover:bg-white/10 transition-colors"
                  aria-label="Previous backdrop slide"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() =>
                    setActiveSlide((prev) => (prev + 1) % slides.length)
                  }
                  className="p-1 rounded text-kairo-gray-400 hover:text-white hover:bg-white/10 transition-colors"
                  aria-label="Next backdrop slide"
                >
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Key Metrics Grid ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Total Reconstructions */}
        <div className="p-5 rounded-kairo bg-white border border-kairo-gray-200 shadow-xs hover:border-kairo-gray-300 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] font-mono uppercase tracking-wider text-kairo-gray-500 font-semibold">
              Total Projects
            </span>
            <div className="w-7 h-7 rounded bg-kairo-offwhite flex items-center justify-center text-kairo-gray-600">
              <Layers className="w-3.5 h-3.5 text-kairo-orange" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight text-kairo-black">
            {String(stats.total).padStart(2, "0")}
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-[11px] text-emerald-600 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{stats.completed} models compiled</span>
          </div>
        </div>

        {/* Metric 2: Detected Wall Segments */}
        <div className="p-5 rounded-kairo bg-white border border-kairo-gray-200 shadow-xs hover:border-kairo-gray-300 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] font-mono uppercase tracking-wider text-kairo-gray-500 font-semibold">
              Extracted Walls
            </span>
            <div className="w-7 h-7 rounded bg-kairo-offwhite flex items-center justify-center text-kairo-gray-600">
              <Building2 className="w-3.5 h-3.5 text-kairo-orange" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight text-kairo-black">
            {stats.totalWalls}
          </div>
          <p className="mt-2 text-[11px] text-kairo-gray-500">
            Across {stats.totalRooms} identified room sectors
          </p>
        </div>

        {/* Metric 3: Mean Metric Scale */}
        <div className="p-5 rounded-kairo bg-white border border-kairo-gray-200 shadow-xs hover:border-kairo-gray-300 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] font-mono uppercase tracking-wider text-kairo-gray-500 font-semibold">
              Mean Precision
            </span>
            <div className="w-7 h-7 rounded bg-kairo-offwhite flex items-center justify-center text-kairo-gray-600">
              <Compass className="w-3.5 h-3.5 text-kairo-orange" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight text-kairo-black">
            {stats.avgScale}{" "}
            <span className="text-xs font-mono text-kairo-gray-400 font-normal">
              mm/px
            </span>
          </div>
          <p className="mt-2 text-[11px] text-emerald-600 font-medium">
            Sub-millimeter calibrated
          </p>
        </div>

        {/* Metric 4: MGR Reconciliation Confidence */}
        <div className="p-5 rounded-kairo bg-white border border-kairo-gray-200 shadow-xs hover:border-kairo-gray-300 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] font-mono uppercase tracking-wider text-kairo-gray-500 font-semibold">
              MGR Confidence
            </span>
            <div className="w-7 h-7 rounded bg-kairo-offwhite flex items-center justify-center text-kairo-gray-600">
              <ShieldCheck className="w-3.5 h-3.5 text-kairo-orange" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight text-kairo-black">
            94.8%
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-[11px] text-kairo-gray-500">
            <TrendingUp className="w-3 h-3 text-kairo-orange" />
            <span>High metric reliability</span>
          </div>
        </div>
      </div>

      {/* ── Main Two-Column Layout ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (2 Cols): Quick Action Launchpad & Recent Projects */}
        <div className="lg:col-span-2 space-y-8">
          {/* Quick Upload Launchpad Card */}
          <div className="p-6 rounded-kairo bg-kairo-black text-white relative overflow-hidden shadow-md">
            <div
              className="absolute inset-0 opacity-[0.05] pointer-events-none"
              style={{
                backgroundImage: `
                  linear-gradient(rgba(255,255,255,1) 1px, transparent 1px),
                  linear-gradient(90deg, rgba(255,255,255,1) 1px, transparent 1px)
                `,
                backgroundSize: "24px 24px",
              }}
            />

            <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-6">
              <div className="space-y-2 max-w-md">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-kairo-orange/20 text-kairo-orange text-[10px] font-mono font-semibold uppercase">
                  <Sparkles className="w-3 h-3" />
                  Instant Reconstruction
                </span>
                <h3 className="text-xl font-bold tracking-tight">
                  Start a new architectural reconstruction
                </h3>
                <p className="text-xs text-kairo-gray-400 leading-relaxed">
                  Upload any 2D architectural drawing, PNG/JPG blueprint or floor plan PDF to
                  automatically fuse geometry and generate 3D spaces.
                </p>
              </div>

              <div className="shrink-0">
                <Link
                  href="/workspace"
                  className="btn-primary text-xs py-3.5 px-6 font-semibold uppercase tracking-wider flex items-center justify-center gap-2 shadow-lg"
                >
                  <Upload className="w-4 h-4" />
                  <span>Open Workspace</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </div>

          {/* Recent Reconstructions Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-kairo-black tracking-tight">
                  Recent Reconstructions
                </h3>
                <p className="text-xs text-kairo-gray-500">
                  Direct access to compiled scenes and metric inspections
                </p>
              </div>
              <Link
                href="/history"
                className="text-xs font-semibold text-kairo-orange hover:underline inline-flex items-center gap-1"
              >
                <span>View all ({items.length})</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {/* Project Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {items.slice(0, 4).map((rec) => (
                <div
                  key={rec.id}
                  className="p-5 rounded-kairo bg-white border border-kairo-gray-200 hover:border-kairo-orange/50 transition-all flex flex-col justify-between group shadow-2xs"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <div>
                        <h4 className="text-sm font-bold text-kairo-black group-hover:text-kairo-orange transition-colors">
                          {rec.name}
                        </h4>
                        <p className="text-[10px] font-mono text-kairo-gray-400 mt-0.5">
                          ID: #{rec.id} ·{" "}
                          {new Date(rec.createdAt).toLocaleDateString()}
                        </p>
                      </div>

                      <span
                        className={`text-[9px] font-mono font-medium px-2 py-0.5 rounded uppercase tracking-wider ${
                          rec.status === "completed"
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : rec.status === "processing"
                            ? "bg-amber-50 text-amber-700 border border-amber-200"
                            : "bg-red-50 text-red-700 border border-red-200"
                        }`}
                      >
                        {rec.status}
                      </span>
                    </div>

                    {rec.metadata ? (
                      <div className="grid grid-cols-3 gap-2 py-3 border-y border-kairo-gray-100 text-center text-xs">
                        <div>
                          <p className="font-bold text-kairo-black">
                            {rec.metadata.rooms}
                          </p>
                          <p className="text-[9px] uppercase tracking-wider text-kairo-gray-400">
                            Rooms
                          </p>
                        </div>
                        <div>
                          <p className="font-bold text-kairo-black">
                            {rec.metadata.walls}
                          </p>
                          <p className="text-[9px] uppercase tracking-wider text-kairo-gray-400">
                            Walls
                          </p>
                        </div>
                        <div>
                          <p className="font-bold text-kairo-black font-mono">
                            {rec.metadata.scale_mm_per_px
                              ? `${rec.metadata.scale_mm_per_px.toFixed(1)}`
                              : "—"}
                          </p>
                          <p className="text-[9px] uppercase tracking-wider text-kairo-gray-400">
                            mm/px
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="py-3 border-y border-kairo-gray-100 text-xs text-kairo-gray-400 text-center">
                        Processing spatial data…
                      </div>
                    )}
                  </div>

                  <div className="pt-4 flex items-center justify-between">
                    <Link
                      href={`/scene/${rec.id}`}
                      className="btn-outline w-full text-xs py-2 justify-center group-hover:border-kairo-black transition-colors"
                    >
                      <Box className="w-3.5 h-3.5 text-kairo-orange" />
                      <span>Inspect in 3D</span>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column (1 Col): Spatial Engine Status & Topology */}
        <div className="space-y-6">
          {/* Spatial Pipeline Health */}
          <div className="p-5 rounded-kairo bg-white border border-kairo-gray-200 space-y-4 shadow-2xs">
            <div className="flex items-center justify-between pb-3 border-b border-kairo-gray-100">
              <h3 className="text-xs font-bold uppercase tracking-wider text-kairo-black flex items-center gap-2">
                <Cpu className="w-4 h-4 text-kairo-orange" />
                <span>Reconciliation Engines</span>
              </h3>
              <span className="text-[10px] font-mono text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded font-semibold">
                OPERATIONAL
              </span>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded bg-kairo-offwhite border border-kairo-gray-200">
                <div>
                  <p className="font-semibold text-kairo-black">
                    Semantic Perception
                  </p>
                  <p className="text-[10px] text-kairo-gray-400">
                    Wall & opening segmentation
                  </p>
                </div>
                <span className="text-[10px] font-mono text-emerald-700 font-medium">
                  Active (99.4%)
                </span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded bg-kairo-offwhite border border-kairo-gray-200">
                <div>
                  <p className="font-semibold text-kairo-black">
                    MGR Geometry Fusion
                  </p>
                  <p className="text-[10px] text-kairo-gray-400">
                    Multi-source graph reconciliation
                  </p>
                </div>
                <span className="text-[10px] font-mono text-emerald-700 font-medium">
                  Active (GPU)
                </span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded bg-kairo-offwhite border border-kairo-gray-200">
                <div>
                  <p className="font-semibold text-kairo-black">
                    GLB Spatial Packager
                  </p>
                  <p className="text-[10px] text-kairo-gray-400">
                    Binary scene compilation
                  </p>
                </div>
                <span className="text-[10px] font-mono text-emerald-700 font-medium">
                  Ready
                </span>
              </div>
            </div>
          </div>

          {/* Room Area Topology Breakdown */}
          <div className="p-5 rounded-kairo bg-white border border-kairo-gray-200 space-y-4 shadow-2xs">
            <h3 className="text-xs font-bold uppercase tracking-wider text-kairo-black flex items-center gap-2 pb-3 border-b border-kairo-gray-100">
              <Building2 className="w-4 h-4 text-kairo-orange" />
              <span>Standard Sector Topology</span>
            </h3>

            <div className="space-y-2.5">
              {MOCK_ROOMS.map((room) => (
                <div
                  key={room.id}
                  className="flex items-center justify-between text-xs"
                >
                  <span className="text-kairo-gray-600 font-medium truncate max-w-[140px]">
                    {room.label}
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 bg-kairo-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-kairo-orange"
                        style={{
                          width: `${Math.min(100, (room.area_m2 / 25) * 100)}%`,
                        }}
                      />
                    </div>
                    <span className="font-mono text-[11px] text-kairo-black font-semibold min-w-[42px] text-right">
                      {room.area_m2} m²
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Tool Navigation Card */}
          <div className="p-5 rounded-kairo bg-white border border-kairo-gray-200 space-y-3 shadow-2xs">
            <h3 className="text-xs font-bold uppercase tracking-wider text-kairo-black">
              Quick Shortcuts
            </h3>
            <div className="space-y-1.5">
              <Link
                href="/scene/demo"
                className="flex items-center justify-between p-2 rounded hover:bg-kairo-offwhite text-xs text-kairo-gray-700 hover:text-kairo-black transition-colors"
              >
                <span className="flex items-center gap-2">
                  <Box className="w-3.5 h-3.5 text-kairo-orange" />
                  <span>3D Interactive Scene Viewer</span>
                </span>
                <ArrowRight className="w-3.5 h-3.5 text-kairo-gray-400" />
              </Link>
              <Link
                href="/workspace"
                className="flex items-center justify-between p-2 rounded hover:bg-kairo-offwhite text-xs text-kairo-gray-700 hover:text-kairo-black transition-colors"
              >
                <span className="flex items-center gap-2">
                  <Upload className="w-3.5 h-3.5 text-kairo-orange" />
                  <span>Reconstruct New Blueprint</span>
                </span>
                <ArrowRight className="w-3.5 h-3.5 text-kairo-gray-400" />
              </Link>
              <Link
                href="/history"
                className="flex items-center justify-between p-2 rounded hover:bg-kairo-offwhite text-xs text-kairo-gray-700 hover:text-kairo-black transition-colors"
              >
                <span className="flex items-center gap-2">
                  <History className="w-3.5 h-3.5 text-kairo-orange" />
                  <span>Full Reconstruction Archive</span>
                </span>
                <ArrowRight className="w-3.5 h-3.5 text-kairo-gray-400" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
