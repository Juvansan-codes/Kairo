"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowRight } from "lucide-react";

const navLinks = [
  { href: "/", label: "Home" },
  { href: "/workspace", label: "Workspace" },
  { href: "/history", label: "History" },
];

export function Navbar() {
  const pathname = usePathname();

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

          {/* Navigation */}
          <div className="hidden sm:flex items-center gap-8">
            {navLinks.map((link) => {
              const isActive =
                link.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(link.href);
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

          {/* Primary action */}
          <Link
            href="/workspace"
            className="btn-primary text-sm hidden sm:inline-flex"
          >
            New Reconstruction
            <ArrowRight className="w-4 h-4" />
          </Link>

          {/* Mobile menu button */}
          <div className="sm:hidden flex items-center gap-4">
            <Link
              href="/workspace"
              className="btn-primary text-xs px-4 py-2"
            >
              New
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
