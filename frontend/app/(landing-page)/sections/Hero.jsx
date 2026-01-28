"use client";
import { useRouter } from "next/navigation";
import { useRef, useEffect } from "react";
import { InteractiveHoverButton } from "@/components/ui/get-started";

const Hero = () => {
  const router = useRouter();
  const videoRef = useRef(null);

  useEffect(() => {
    // Force video to play on mount (helps with iOS autoplay)
    if (videoRef.current) {
      videoRef.current.play().catch((error) => {
        console.log("Video autoplay failed:", error);
      });
    }
  }, []);

  return (
    <section className="min-h-[50vh] md:mt-24 2xl:mt-5 w-full flex flex-col md:flex-row items-center justify-center max-w-7xl mx-auto p-4 md:p-8 gap-8 md:gap-12">
      <div className="flex flex-col items-start justify-center gap-4 md:gap-6 w-full md:w-1/2">
        <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-instrument text-tekk-darkest leading-tight">
          Give your app superhuman research abilities.
        </h1>
        <p className="text-base sm:text-lg md:text-xl text-tekk-darkest/80 leading-relaxed">
          Our AI scans the web, analyzes sources, synthesizes insights, and
          returns structured research reports, all via a simple API call.
        </p>
        <div className="flex flex-col items-start justify-center gap-2 w-full sm:w-auto">
          <InteractiveHoverButton
            className="bg-white text-black w-auto sm:w-auto"
            onClick={() => router.push("/authentication")}
            onTap={() => router.push("/authentication")}
          >
            Get Started
          </InteractiveHoverButton>
          <p className="text-sm text-tekk-darkest/60">
            Start for free, initial credits on us.
          </p>
        </div>
      </div>
      <div className="w-full md:w-1/2 flex items-center justify-center">
        <video 
          ref={videoRef}
          className="w-full max-w-[600px] rounded-lg md:rounded-xl lg:rounded-2xl bg-white shadow-lg" 
          autoPlay 
          loop 
          muted 
          playsInline
          webkit-playsinline="true"
        >
          <source src="/hero-video.mp4" type="video/mp4" />
          Your browser does not support the video tag.
        </video>
      </div>
    </section>
  );
};

export default Hero;
