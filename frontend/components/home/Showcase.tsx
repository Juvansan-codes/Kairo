import { ArrowRight } from "lucide-react";

const stats = [
  { label: "Rooms", value: "5" },
  { label: "Walls", value: "18" },
  { label: "Doors", value: "6" },
  { label: "Windows", value: "9" },
];

export function Showcase() {
  return (
    <section className="bg-kairo-offwhite">
      <div className="mx-auto max-w-7xl px-6 lg:px-8 py-20 lg:py-28">
        <p className="micro-label mb-4 text-kairo-orange">OUTPUT</p>
        <h2 className="text-section text-kairo-black mb-16">
          Blueprint in, spatial model out
        </h2>

        <div className="grid lg:grid-cols-2 gap-8 items-stretch">
          {/* Input */}
          <div className="border border-kairo-gray-200 rounded-kairo p-8 bg-white flex flex-col">
            <p className="micro-label mb-6">INPUT</p>
            <div className="flex-1 flex items-center justify-center min-h-[200px]">
              <svg
                viewBox="0 0 200 140"
                className="w-48 opacity-60"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <rect
                  x="5"
                  y="5"
                  width="190"
                  height="130"
                  stroke="#0A0A0A"
                  strokeWidth="1.5"
                />
                <line x1="5" y1="70" x2="195" y2="70" stroke="#0A0A0A" strokeWidth="1" />
                <line x1="90" y1="5" x2="90" y2="70" stroke="#0A0A0A" strokeWidth="1" />
                <line x1="130" y1="70" x2="130" y2="135" stroke="#0A0A0A" strokeWidth="1" />
              </svg>
            </div>
            <p className="text-sm text-kairo-gray-500 mt-4">
              Architectural Blueprint · PNG / JPG / PDF
            </p>
          </div>

          {/* Output */}
          <div className="border border-kairo-orange rounded-kairo p-8 bg-kairo-black flex flex-col">
            <p className="micro-label mb-6 text-kairo-orange">OUTPUT</p>
            <div className="flex-1 flex items-center justify-center min-h-[200px]">
              <svg
                viewBox="0 0 200 140"
                className="w-48"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                {/* Isometric representation */}
                <polygon
                  points="100,15 180,55 100,95 20,55"
                  stroke="#F15A24"
                  strokeWidth="1.5"
                  fill="rgba(241,90,36,0.08)"
                />
                <line x1="20" y1="55" x2="20" y2="85" stroke="#F15A24" strokeWidth="1.5" />
                <line x1="100" y1="95" x2="100" y2="125" stroke="#F15A24" strokeWidth="1.5" />
                <line x1="180" y1="55" x2="180" y2="85" stroke="#F15A24" strokeWidth="1.5" />
                <polygon
                  points="20,85 100,125 180,85"
                  stroke="#F15A24"
                  strokeWidth="1.5"
                  fill="none"
                />
                {/* Internal walls */}
                <line x1="100" y1="55" x2="100" y2="95" stroke="#F15A24" strokeWidth="0.8" opacity="0.4" />
                <line x1="60" y1="35" x2="60" y2="70" stroke="#F15A24" strokeWidth="0.8" opacity="0.4" />
              </svg>
            </div>
            <div className="flex items-center justify-between mt-4">
              <div>
                <p className="text-sm text-white font-medium">
                  Interactive 3D Scene
                </p>
                <p className="text-xs text-kairo-gray-500">scene.glb + scene.json</p>
              </div>
              <ArrowRight className="w-4 h-4 text-kairo-orange" />
            </div>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-3 mt-6 pt-6 border-t border-kairo-gray-800">
              {stats.map((s) => (
                <div key={s.label} className="text-center">
                  <p className="text-xl font-semibold text-white">{s.value}</p>
                  <p className="text-[10px] uppercase tracking-wider text-kairo-gray-500">
                    {s.label}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
