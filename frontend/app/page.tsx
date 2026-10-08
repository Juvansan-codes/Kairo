import { Hero } from "@/components/home/Hero";
import { Pipeline } from "@/components/home/Pipeline";
import { ResearchSection } from "@/components/home/ResearchSection";
import { Showcase } from "@/components/home/Showcase";
import { BottomCTA } from "@/components/home/BottomCTA";

export default function HomePage() {
  return (
    <>
      <Hero />
      <Pipeline />
      <ResearchSection />
      <Showcase />
      <BottomCTA />
    </>
  );
}
