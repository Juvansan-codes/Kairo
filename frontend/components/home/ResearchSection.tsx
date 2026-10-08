import { Plus, ArrowDown } from "lucide-react";

const evidenceTypes = [
  "Semantic evidence",
  "Geometric evidence",
  "Dimension evidence",
  "Topological constraints",
];

export function ResearchSection() {
  return (
    <section className="bg-white">
      <div className="mx-auto max-w-7xl px-6 lg:px-8 py-20 lg:py-28">
        <div className="grid lg:grid-cols-2 gap-16 items-start">
          {/* Left — Explanation */}
          <div>
            <p className="micro-label mb-4 text-kairo-orange">RESEARCH</p>
            <h2 className="text-section text-kairo-black mb-6">
              Not just
              <br />
              image → 3D
            </h2>
            <p className="text-kairo-gray-500 leading-relaxed mb-6 max-w-md">
              Most reconstruction systems trust neural predictions as final
              geometry. KAIRO treats them as{" "}
              <span className="text-kairo-black font-medium">evidence</span>,
              not unquestionable truth.
            </p>
            <p className="text-kairo-gray-500 leading-relaxed max-w-md">
              Multiple evidence streams are fused through{" "}
              <span className="text-kairo-black font-medium">
                Metric-Aware Geometric Reconciliation
              </span>{" "}
              (MGR) — producing geometry that is metrically consistent, not
              just visually plausible.
            </p>
          </div>

          {/* Right — Evidence fusion diagram */}
          <div className="border border-kairo-gray-200 rounded-kairo p-8 bg-kairo-offwhite">
            <p className="micro-label mb-6">KAIRO COMBINES</p>

            <div className="space-y-3 mb-6">
              {evidenceTypes.map((ev, i) => (
                <div key={ev} className="flex items-center gap-3">
                  {i > 0 && (
                    <Plus className="w-3 h-3 text-kairo-gray-400 flex-shrink-0" />
                  )}
                  {i === 0 && <div className="w-3" />}
                  <div className="flex-1 py-2.5 px-4 bg-white border border-kairo-gray-200 rounded-kairo">
                    <span className="text-sm font-medium text-kairo-black">
                      {ev}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-center my-4">
              <ArrowDown className="w-5 h-5 text-kairo-orange" />
            </div>

            <div className="py-4 px-5 bg-kairo-black rounded-kairo text-center">
              <p className="micro-label text-kairo-orange mb-1">MGR</p>
              <p className="text-sm font-medium text-white">
                Metric-Aware Geometric Reconciliation
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
