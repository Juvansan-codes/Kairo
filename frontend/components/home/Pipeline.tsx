const steps = [
  {
    number: "01",
    title: "Semantic Perception",
    description: "Identify walls, doors, windows, and rooms from pixel-level features.",
  },
  {
    number: "02",
    title: "Geometric Analysis",
    description: "Extract line segments, junctions, and structural relationships.",
  },
  {
    number: "03",
    title: "Dimension Extraction",
    description: "Read annotated dimensions and scale markers via OCR.",
  },
  {
    number: "04",
    title: "Metric-Aware Geometric Reconciliation",
    description: "Fuse evidence into a metrically consistent spatial graph.",
  },
  {
    number: "05",
    title: "3D Reconstruction",
    description: "Generate navigable geometry with correct topology.",
  },
];

export function Pipeline() {
  return (
    <section className="bg-kairo-offwhite">
      <div className="mx-auto max-w-7xl px-6 lg:px-8 py-20 lg:py-28">
        <p className="micro-label mb-4 text-kairo-orange">PIPELINE</p>
        <h2 className="text-section text-kairo-black mb-16 max-w-lg">
          From blueprint to spatial intelligence
        </h2>

        {/* Desktop horizontal timeline */}
        <div className="hidden lg:block">
          <div className="grid grid-cols-5 gap-6">
            {steps.map((step, i) => (
              <div key={step.number} className="relative">
                {/* Connector line */}
                {i < steps.length - 1 && (
                  <div className="absolute top-5 left-[calc(50%+16px)] right-0 h-px bg-kairo-gray-300 translate-x-4" />
                )}

                <div className="relative z-10">
                  <div className="w-10 h-10 rounded-full border-2 border-kairo-black flex items-center justify-center mb-4 bg-white">
                    <span className="text-xs font-bold text-kairo-black">
                      {step.number}
                    </span>
                  </div>
                  <h3 className="text-sm font-semibold text-kairo-black mb-2 leading-snug">
                    {step.title}
                  </h3>
                  <p className="text-xs text-kairo-gray-500 leading-relaxed">
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Mobile vertical list */}
        <div className="lg:hidden space-y-8">
          {steps.map((step, i) => (
            <div key={step.number} className="flex gap-5">
              <div className="flex flex-col items-center">
                <div className="w-10 h-10 rounded-full border-2 border-kairo-black flex items-center justify-center bg-white flex-shrink-0">
                  <span className="text-xs font-bold text-kairo-black">
                    {step.number}
                  </span>
                </div>
                {i < steps.length - 1 && (
                  <div className="w-px flex-1 bg-kairo-gray-300 mt-2" />
                )}
              </div>
              <div className="pb-4">
                <h3 className="text-sm font-semibold text-kairo-black mb-1">
                  {step.title}
                </h3>
                <p className="text-sm text-kairo-gray-500">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
