"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Layers,
  History,
  Box,
  LogOut,
  Menu,
  X,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

const navItems = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    badge: null,
  },
  {
    label: "Reconstruct Blueprint",
    href: "/workspace",
    icon: Layers,
    badge: "Active",
  },
  {
    label: "Reconstruction History",
    href: "/history",
    icon: History,
    badge: null,
  },
  {
    label: "3D Spatial Viewer",
    href: "/scene/demo",
    icon: Box,
    badge: "GLB",
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, signOut, isConfigured } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const userName =
    user?.user_metadata?.full_name ||
    user?.email?.split("@")[0] ||
    "Lead Architect";
  const userEmail = user?.email || "architect@kairo.space";

  return (
    <>
      {/* Mobile Top Header with Hamburger */}
      <div className="lg:hidden sticky top-0 z-40 flex items-center justify-between px-4 h-14 bg-white border-b border-kairo-gray-200">
        <Link href="/dashboard" className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-sm bg-kairo-orange" />
          <span className="text-base font-bold tracking-tight text-kairo-black">
            KAIRO
          </span>
        </Link>
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="p-2 text-kairo-gray-600 hover:text-kairo-black rounded-kairo hover:bg-kairo-offwhite transition-colors"
          aria-label="Toggle Navigation"
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-black/40 backdrop-blur-sm animate-fade-in"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Main Sidebar Container */}
      <aside
        className={`
          fixed top-0 bottom-0 left-0 z-50 w-64 bg-white border-r border-kairo-gray-200
          flex flex-col justify-between transition-transform duration-300 ease-in-out
          h-screen shrink-0 overflow-hidden
          ${mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
          lg:sticky lg:top-0
        `}
      >
        {/* Top Branding */}
        <div className="p-6 border-b border-kairo-gray-100 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-2.5 group">
            <span className="w-3 h-3 rounded-sm bg-kairo-orange transition-transform group-hover:scale-110" />
            <div className="flex flex-col">
              <span className="text-lg font-bold tracking-tight text-kairo-black leading-none">
                KAIRO
              </span>
              <span className="text-[9px] font-mono tracking-widest text-kairo-gray-400 uppercase mt-0.5">
                SPATIAL SUITE
              </span>
            </div>
          </Link>
          <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded bg-kairo-offwhite border border-kairo-gray-200 text-kairo-gray-500">
            v2.4
          </span>
        </div>

        {/* Navigation Items */}
        <div className="flex-1 overflow-y-auto px-3 py-6 space-y-6">
          {/* Main workspace section */}
          <div>
            <p className="px-3 text-[10px] font-mono uppercase tracking-wider text-kairo-gray-400 mb-2 font-semibold">
              WORKSPACE
            </p>
            <nav className="space-y-1">
              {navItems.map((item) => {
                const isActive =
                  pathname === item.href ||
                  (item.href !== "/dashboard" && pathname.startsWith(item.href));
                const Icon = item.icon;

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    className={`
                      flex items-center justify-between px-3 py-2.5 rounded-kairo text-xs font-medium transition-all group
                      ${
                        isActive
                          ? "bg-kairo-black text-white shadow-sm"
                          : "text-kairo-gray-600 hover:text-kairo-black hover:bg-kairo-offwhite"
                      }
                    `}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <Icon
                        className={`w-4 h-4 shrink-0 transition-colors ${
                          isActive
                            ? "text-kairo-orange"
                            : "text-kairo-gray-400 group-hover:text-kairo-black"
                        }`}
                      />
                      <span className="truncate">{item.label}</span>
                    </div>

                    {item.badge && (
                      <span
                        className={`text-[9px] font-mono px-1.5 py-0.2 rounded uppercase ${
                          isActive
                            ? "bg-kairo-orange text-white"
                            : "bg-kairo-gray-100 text-kairo-gray-500"
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>

        {/* User Footer / Account Actions */}
        <div className="p-4 border-t border-kairo-gray-100 bg-white space-y-3">
          {/* User profile card */}
          <div className="flex items-center gap-3 px-2 py-1.5 rounded-kairo bg-kairo-offwhite border border-kairo-gray-200">
            <div className="w-8 h-8 rounded-full bg-kairo-black text-white flex items-center justify-center text-xs font-bold uppercase shrink-0">
              {userName.charAt(0)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <p className="text-xs font-semibold text-kairo-black truncate">
                  {userName}
                </p>
                <span
                  title={isConfigured ? "Connected to Supabase" : "Demo Mode Active"}
                  className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                    isConfigured ? "bg-emerald-500" : "bg-amber-500"
                  }`}
                />
              </div>
              <p className="text-[10px] text-kairo-gray-400 truncate">
                {userEmail}
              </p>
            </div>
          </div>

          {/* Sign out action */}
          <button
            onClick={() => signOut()}
            className="w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-kairo border border-kairo-gray-200 text-xs font-medium text-kairo-gray-500 hover:text-red-600 hover:border-red-200 hover:bg-red-50/30 transition-all"
            title="Sign Out"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>
    </>
  );
}
