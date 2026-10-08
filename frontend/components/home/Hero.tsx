"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div className="mx-auto max-w-7xl px-6 lg:px-8 py-20 lg:py-32">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left — Copy */}
          <div className="animate-fade-in">
            <p className="micro-label mb-6 text-kairo-orange">
              METRIC-AWARE BLUEPRINT INTELLIGENCE
            </p>
            <h1 className="text-hero-lg lg:text-hero-xl text-kairo-black mb-6">
              From blueprint
              <br />
              to spatial
              <br />
              <span className="text-kairo-orange">reality.</span>
            </h1>
            <p className="text-lg text-kairo-gray-500 max-w-md mb-10 leading-relaxed">
              Turn architectural blueprints into metrically consistent,
              navigable 3D environments.
            </p>
            <Link href="/workspace" className="btn-primary text-base px-8 py-4">
              Start Reconstruction
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>

          {/* Right — Blueprint Visual */}
          <div className="animate-slide-up">
            <BlueprintVisual />
          </div>
        </div>
      </div>

      {/* Subtle grid background */}
      <div
        className="absolute inset-0 -z-10"
        style={{
          backgroundImage: `
            linear-gradient(rgba(0,0,0,0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,0,0,0.02) 1px, transparent 1px)
          `,
          backgroundSize: "40px 40px",
        }}
      />
    </section>
  );
}

function BlueprintVisual() {
  return (
    <div className="relative">
      {/* 2D Blueprint */}
      <div className="border border-kairo-gray-200 rounded-kairo p-6 bg-white">
        <p className="micro-label mb-4">2D FLOOR PLAN</p>
        <svg
          viewBox="0 0 320 220"
          className="w-full"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Outer walls */}
          <rect
            x="10"
            y="10"
            width="300"
            height="200"
            stroke="#0A0A0A"
            strokeWidth="2.5"
            fill="none"
          />

          {/* Horizontal divider */}
          <line x1="10" y1="120" x2="310" y2="120" stroke="#0A0A0A" strokeWidth="2" />

          {/* Vertical divider top */}
          <line x1="140" y1="10" x2="140" y2="120" stroke="#0A0A0A" strokeWidth="2" />

          {/* Vertical divider bottom */}
          <line x1="200" y1="120" x2="200" y2="210" stroke="#0A0A0A" strokeWidth="2" />

          {/* Doors (arcs) */}
          <path d="M 140 55 A 25 25 0 0 1 165 80" stroke="#F15A24" strokeWidth="1.5" fill="none" />
          <line x1="140" y1="55" x2="140" y2="80" stroke="#F15A24" strokeWidth="1.5" strokeDasharray="4 3" />

          <path d="M 80 120 A 25 25 0 0 0 105 145" stroke="#F15A24" strokeWidth="1.5" fill="none" />
          <line x1="80" y1="120" x2="105" y2="120" stroke="#F15A24" strokeWidth="1.5" strokeDasharray="4 3" />

          {/* Windows */}
          <line x1="40" y1="10" x2="90" y2="10" stroke="#F15A24" strokeWidth="3" />
          <line x1="180" y1="10" x2="260" y2="10" stroke="#F15A24" strokeWidth="3" />
          <line x1="240" y1="120" x2="290" y2="120" stroke="#F15A24" strokeWidth="3" />

          {/* Room labels */}
          <text x="55" y="72" className="text-[10px] font-medium" fill="#737373">
            BEDROOM
          </text>
          <text x="185" y="72" className="text-[10px] font-medium" fill="#737373">
            LIVING ROOM
          </text>
          <text x="75" y="172" className="text-[10px] font-medium" fill="#737373">
            KITCHEN
          </text>
          <text x="225" y="172" className="text-[10px] font-medium" fill="#737373">
            BATH
          </text>

          {/* Dimension lines */}
          <line x1="10" y1="225" x2="310" y2="225" stroke="#A3A3A3" strokeWidth="0.5" />
          <line x1="10" y1="222" x2="10" y2="228" stroke="#A3A3A3" strokeWidth="0.5" />
          <line x1="310" y1="222" x2="310" y2="228" stroke="#A3A3A3" strokeWidth="0.5" />
          <text x="140" y="236" textAnchor="middle" className="text-[8px]" fill="#A3A3A3">
            9.60 m
          </text>
        </svg>
      </div>

      {/* Arrow */}
      <div className="flex justify-center my-4">
        <div className="flex flex-col items-center gap-1">
          <div className="w-px h-6 bg-kairo-orange" />
          <ArrowRight className="w-4 h-4 text-kairo-orange rotate-90" />
        </div>
      </div>

      {/* 3D reconstruction indicator */}
      <div className="border border-kairo-orange rounded-kairo p-6 bg-kairo-black">
        <p className="micro-label mb-3 text-kairo-orange">3D RECONSTRUCTION</p>
        <div className="flex items-center gap-6">
          {/* Isometric grid hint */}
          <svg
            viewBox="0 0 120 80"
            className="w-28 flex-shrink-0"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            {/* Isometric box */}
            <polygon
              points="60,10 110,35 60,60 10,35"
              stroke="#F15A24"
              strokeWidth="1.5"
              fill="rgba(241,90,36,0.1)"
            />
            <line x1="10" y1="35" x2="10" y2="55" stroke="#F15A24" strokeWidth="1.5" />
            <line x1="60" y1="60" x2="60" y2="80" stroke="#F15A24" strokeWidth="1.5" />
            <line x1="110" y1="35" x2="110" y2="55" stroke="#F15A24" strokeWidth="1.5" />
            <polygon
              points="10,55 60,80 110,55 60,60"
              stroke="#F15A24"
              strokeWidth="1.5"
              fill="rgba(241,90,36,0.05)"
            />
            {/* Internal walls */}
            <line x1="60" y1="35" x2="60" y2="60" stroke="#F15A24" strokeWidth="0.8" opacity="0.5" />
            <line x1="35" y1="22" x2="35" y2="47" stroke="#F15A24" strokeWidth="0.8" opacity="0.5" />
          </svg>

          <div>
            <p className="text-white text-sm font-medium mb-1">scene.glb</p>
            <p className="text-kairo-gray-500 text-xs">
              Interactive · Navigable · Metric
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
