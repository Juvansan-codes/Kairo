import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-kairo-gray-200 bg-white">
      <div className="mx-auto max-w-7xl px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row justify-between items-center gap-4 text-xs text-kairo-gray-500">
          {/* Brand */}
          <div className="flex items-center gap-2">
            <Link href="/" className="flex items-center gap-2 group">
              <span className="inline-block w-2 h-2 rounded-sm bg-kairo-orange" />
              <span className="text-sm font-bold tracking-tight text-kairo-black">
                KAIRO
              </span>
            </Link>
            <span className="text-kairo-gray-300">|</span>
            <span>Metric-Aware Blueprint Intelligence</span>
          </div>

          <p className="text-xs text-kairo-gray-400">
            From blueprint to spatial reality.
          </p>
        </div>
      </div>
    </footer>
  );
}
