"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogIn, LogOut, User as UserIcon } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

const navLinks = [
  { href: "/workspace", label: "Workspace" },
  { href: "/history", label: "History" },
];

export function Navbar() {
  const pathname = usePathname();
  const { user, signOut, loading } = useAuth();
  const isHomePage = pathname === "/";

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-kairo-gray-200 bg-white/95 backdrop-blur-sm">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <span className="inline-block w-2 h-2 rounded-sm bg-kairo-orange" />
            <span className="text-lg font-bold tracking-tight text-kairo-black">
              KAIRO
            </span>
          </Link>

          {/* Navigation - hidden on home screen */}
          {!isHomePage && (
            <div className="hidden sm:flex items-center gap-8">
              {navLinks.map((link) => {
                const isActive = pathname.startsWith(link.href);
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`text-sm font-medium transition-colors duration-200 ${
                      isActive
                        ? "text-kairo-black"
                        : "text-kairo-gray-500 hover:text-kairo-black"
                    }`}
                  >
                    {link.label}
                  </Link>
                );
              })}
            </div>
          )}

          {/* Primary action / Auth state */}
          <div className="hidden sm:flex items-center gap-4">
            {!loading && user ? (
              <div className="flex items-center gap-3">
                <Link
                  href="/dashboard"
                  className="flex items-center gap-2 px-3 py-1.5 rounded-kairo bg-kairo-offwhite border border-kairo-gray-200 text-xs font-medium text-kairo-black max-w-[200px] truncate hover:border-kairo-orange/50 transition-colors"
                  title="Go to Dashboard"
                >
                  <UserIcon className="w-3.5 h-3.5 text-kairo-orange shrink-0" />
                  <span className="truncate">
                    {user.user_metadata?.full_name || user.email?.split("@")[0] || "User"}
                  </span>
                </Link>
                <button
                  onClick={() => signOut()}
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-kairo-gray-500 hover:text-kairo-black border border-kairo-gray-200 rounded-kairo transition-colors"
                  title="Sign Out"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            ) : (
              <Link
                href="/auth"
                className="btn-primary text-sm inline-flex items-center gap-2"
              >
                Login / Sign Up
                <LogIn className="w-4 h-4" />
              </Link>
            )}
          </div>

          {/* Mobile menu action */}
          <div className="sm:hidden flex items-center gap-3">
            {!loading && user ? (
              <button
                onClick={() => signOut()}
                className="inline-flex items-center gap-1 text-xs text-kairo-gray-600 px-2.5 py-1.5 border border-kairo-gray-200 rounded-kairo"
              >
                <LogOut className="w-3.5 h-3.5" />
                Sign Out
              </button>
            ) : (
              <Link
                href="/auth"
                className="btn-primary text-xs px-3 py-1.5"
              >
                Login
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
