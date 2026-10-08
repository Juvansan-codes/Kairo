import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-kairo-gray-200 bg-white">
      <div className="mx-auto max-w-7xl px-6 lg:px-8 py-12">
        <div className="flex flex-col md:flex-row justify-between items-start gap-8">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="inline-block w-2 h-2 rounded-sm bg-kairo-orange" />
              <span className="text-base font-bold tracking-tight text-kairo-black">
                KAIRO
              </span>
            </div>
            <p className="text-sm text-kairo-gray-500 max-w-xs">
              Metric-Aware Blueprint Intelligence
            </p>
          </div>

          {/* Links */}
          <div className="flex gap-10">
            <Link
              href="/"
              className="text-sm text-kairo-gray-500 hover:text-kairo-black transition-colors"
            >
              Home
            </Link>
            <Link
              href="/workspace"
              className="text-sm text-kairo-gray-500 hover:text-kairo-black transition-colors"
            >
              Workspace
            </Link>
            <Link
              href="/history"
              className="text-sm text-kairo-gray-500 hover:text-kairo-black transition-colors"
            >
              History
            </Link>
          </div>

          {/* Hackathon ID */}
          <div className="text-right">
            <p className="micro-label mb-1">Hackathon</p>
            <p className="text-sm font-mono text-kairo-gray-600">HNX26EPS06</p>
          </div>
        </div>

        <div className="mt-10 pt-6 border-t border-kairo-gray-100">
          <p className="text-xs text-kairo-gray-400">
            KAIRO — From blueprint to spatial reality.
          </p>
        </div>
      </div>
    </footer>
  );
}
