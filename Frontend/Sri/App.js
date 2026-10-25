import { useEffect } from "react";
import Lenis from "lenis";
import "@fontsource/cormorant-garamond/400.css";
import "@fontsource/cormorant-garamond/500.css";
import "@fontsource/cormorant-garamond/400-italic.css";
import "@fontsource/cormorant-garamond/500-italic.css";
import "@fontsource/manrope/400.css";
import "@fontsource/manrope/500.css";
import "@fontsource/manrope/600.css";
import "@/App.css";
import { Toaster } from "@/components/ui/sonner";
import { Nav } from "@/components/site/Nav";
import { Hero } from "@/components/site/Hero";
import { Marquee } from "@/components/site/Marquee";
import { About } from "@/components/site/About";
import { Services } from "@/components/site/Services";
import { SingleWindow } from "@/components/site/SingleWindow";
import { Clients } from "@/components/site/Clients";
import { Enquiry } from "@/components/site/Enquiry";
import { Footer } from "@/components/site/Footer";
import { Intro } from "@/components/site/Intro";
import { Pristin } from "@/components/site/Pristin";

function App() {
  useEffect(() => {
    const lenis = new Lenis({ lerp: 0.09, smoothWheel: true });
    window.__lenis = lenis;
    let id;
    const raf = (t) => { lenis.raf(t); id = requestAnimationFrame(raf); };
    id = requestAnimationFrame(raf);
    return () => { cancelAnimationFrame(id); lenis.destroy(); window.__lenis = null; };
  }, []);

  return (
    <div className="relative min-h-screen bg-[#07090E] text-[#F3EEE4] overflow-x-clip">
      <Intro />
      <div className="grain" />
      <Nav />
      <main>
        <Hero />
        <Marquee />
        <About />
        <Services />
        <SingleWindow />
        <Clients />
        <Pristin />
        <Enquiry />
      </main>
      <Footer />
      <Toaster theme="dark" position="bottom-right" />
    </div>
  );
}

export default App;
