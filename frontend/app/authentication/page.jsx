"use client";

import GoogleSignInButton from "./components/GoogleSignInButton";
import { Button } from "@/components/ui/button";
import Image from "next/image";
import Link from "next/link";
import { useAuth } from "@/app/contexts/AuthContext";
import { useEffect } from "react";

import { useRouter } from "next/navigation";

const Page = () => {
  const router = useRouter();

  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      router.push("/dashboard");
    }
  }, [user]);

  return (
    <section className="h-screen w-full flex items-center justify-center p-4">
      <div className="h-full w-1/2 relative hidden md:block">
        <Image
          src="/auth-bg.svg"
          alt="auth-bg"
          fill
          className="object-cover rounded-3xl"
        />
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center justify-center absolute top-4 left-4 z-10"
        >
          <Image
            src="/logos/icon-white.png"
            alt="Tekkscope Logo"
            width={45}
            height={45}
          />
          <span className="font-instrument text-white text-3xl ">
            Tekkscope.
          </span>
        </Link>{" "}
        <div className="h-full w-full absolute bg-black/60 flex flex-col items-start justify-center p-20 text-white gap-4 rounded-3xl">
          <h1 className="text-5xl font-instrument">
            A single API call, World&apos;s best research
          </h1>
          <p className="text-lg font-inter">
            Analyze sources, synthesize insights, and get structured research
            reports, all via a simple API call.
          </p>
        </div>
      </div>

        {/* Right Side - Authentication Form */}
        <div className="flex-1 w-full md:h-full md:w-1/2 bg-white flex flex-col items-center justify-center gap-6 md:gap-8 py-8 md:py-0 px-4">
        <div className="flex flex-col items-center justify-center gap-2 text-center">
          <h1 className="text-2xl md:text-3xl font-instrument">Almost there!</h1>
          <p className="text-sm text-gray-500">
            Sign in or create your account to continue.
          </p>
        </div>
        <div className="w-full max-w-sm md:w-1/2 flex flex-col items-center justify-center gap-4">
          <GoogleSignInButton />
        </div>
        <p className="text-xs text-gray-400 text-center max-w-sm px-4">
          By authenticating, you agree to our{" "}
          <Link
            href="/legal/terms-of-service"
            className="underline hover:text-black"
          >
            Terms of Service
          </Link>{" "}
          and{" "}
          <Link
            href="/legal/privacy-policy"
            className="underline hover:text-black"
          >
            Privacy Policy
          </Link>
          .
        </p>
      </div>
    </section>
  );
};

export default Page;
