"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { Navbar } from "./Navbar";
import { Footer } from "./Footer";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isMarketing = pathname === "/";
  const isAuth = pathname === "/auth";

  // Public Landing Page: Header + Landing Page + Footer
  if (isMarketing) {
    return (
      <div className="min-h-screen flex flex-col bg-white">
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </div>
    );
  }

  // Auth Page: Clean standalone layout
  if (isAuth) {
    return (
      <div className="min-h-screen flex flex-col bg-white">
        <main className="flex-1">{children}</main>
      </div>
    );
  }

  // Application Layout (Dashboard, Workspace, History, Scene Viewer): Fixed Sidebar + Scrollable Content
  return (
    <div className="h-screen w-full overflow-hidden flex flex-col lg:flex-row bg-[#FAFAF9]">
      <Sidebar />
      <main className="flex-1 h-full min-w-0 overflow-y-auto flex flex-col">
        {children}
      </main>
    </div>
  );
}
