"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import Image from "next/image";
import { signInWithGoogle } from '@/lib/actions/auth-actions';
import { LoaderIcon } from "lucide-react";

const GoogleSignInButton = () => {
  const [isLoading, setIsLoading] = useState(false);

    const handleGoogleLogin = async () => {
    setIsLoading(true);
    await signInWithGoogle();
  };


  return (
    <Button
      className="flex items-center justify-center gap-2 w-full cursor-pointer"
      variant="outline"
      onClick={handleGoogleLogin}
      disabled={isLoading}
    >
        {isLoading ? <LoaderIcon className="w-5 h-5 animate-spin" /> : <Image src="/icons/google-icon.webp" alt="logo" width={15} height={15} />}
      Sign in with Google
    </Button>
  );
};

export default GoogleSignInButton;
