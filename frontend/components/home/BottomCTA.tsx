import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function BottomCTA() {
  return (
    <section className="bg-kairo-black">
      <div className="mx-auto max-w-7xl px-6 lg:px-8 py-20 lg:py-28 text-center">
        <p className="micro-label mb-4 text-kairo-orange">READY TO RECONSTRUCT?</p>
        <h2 className="text-section text-white mb-6 max-w-md mx-auto">
          Turn your next blueprint into a spatial model.
        </h2>
        <Link href="/workspace" className="btn-primary text-base px-8 py-4 mt-4">
          Start Reconstruction
          <ArrowRight className="w-5 h-5" />
        </Link>
      </div>
    </section>
  );
}
