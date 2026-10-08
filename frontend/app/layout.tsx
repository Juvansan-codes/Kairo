import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "KAIRO — Metric-Aware Blueprint Intelligence",
  description:
    "Transform architectural blueprints into metrically consistent, navigable 3D environments.",
  icons: {
    icon: "/icon.svg",
  },
};

import { AuthProvider } from "@/lib/auth-context";
import { AppShell } from "@/components/layout/AppShell";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen">
        <AuthProvider>
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
