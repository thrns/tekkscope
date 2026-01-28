"use client";

import { InteractiveHoverButton } from "@/components/ui/get-started";
import { useRouter } from "next/navigation";

const FooterBanner = () => {
  const router = useRouter();
  return (
    <section
      className="mx-auto w-[95%] h-auto md:h-[400px] bg-cover bg-center rounded-3xl flex items-center justify-center text-center text-white my-10 md:my-20 p-8 md:p-0"
      style={{ backgroundImage: "url('/tekkscope-footer-banner.svg')" }}
    >
      <div className="max-w-2xl flex flex-col items-center gap-y-4">
        <h2 className="font-instrument text-3xl md:text-4xl font-medium">
          Give your app superhuman research abilities today.
        </h2>

        <InteractiveHoverButton
          className="bg-white text-black"
          onClick={() => router.push("/authentication")}
        >
          Get Started
        </InteractiveHoverButton>
      </div>
    </section>
  );
};

export default FooterBanner;
