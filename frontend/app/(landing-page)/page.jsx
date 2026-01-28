"use client";
import Hero from "./sections/Hero";
import Features from "./sections/Features";
import Differentiators from "./sections/Differentiators";
import Security from "./sections/Security";
import Integrations from "./sections/Integrations";
import UseCases from "./sections/UseCases";
import FooterBanner from "./sections/FooterBanner";
import Footer from "./sections/Footer";

const LandingPage = () => {
  return (
    <main className="relative max-w-7xl  border-gray-300 mx-auto  w-full h-full overflow-x-hidden">
      <Hero />
      {/* <Features />
      <Differentiators />
      <UseCases />
      <Integrations />
      <Security /> */}
      <FooterBanner />
      <Footer />
    </main>
  );
};

export default LandingPage;
