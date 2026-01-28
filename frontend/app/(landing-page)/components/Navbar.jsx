"use client";
import Link from "next/link";
import Image from "next/image";
import { ArrowRight, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

const Navbar = () => {
  const router = useRouter();

  return (
    <nav className=" w-full md:w-7xl flex items-center justify-between mx-auto">
      <div className="flex items-center justify-between w-full  md:py-4 md:px-0 p-4 mx-auto">
        {/* Logo */}
        <Link href="/" className="flex items-center justify-center">
          <Image
            src="/logos/icon.png"
            alt="Tekkscope Logo"
            width={45}
            height={45}
          />
          <span className="font-instrument text-black text-3xl ">
            Tekkscope.
          </span>
        </Link>

        <div className="hidden md:flex items-center justify-center gap-4  ">
          <Link href="/docs/v1" className="group cursor-pointer">
            <span className="flex items-center justify-center gap-2">
              Documentation{" "}
              <ArrowRight className="-rotate-45 h-5 w-5 transition-transform duration-200 group-hover:-translate-y-0.5" />
            </span>
          </Link>
          <Button
            className="bg-tekk-darkest text-white cursor-pointer"
            onClick={() => router.push("/authentication")}
            onTap={() => router.push("/authentication")}
          >
            Get Started
          </Button>
        </div>
        {/* menu button */}
        <Sheet>
          <SheetTrigger className="block md:hidden">
            <Menu />
          </SheetTrigger>
          <SheetContent className="w-full ">
            <SheetHeader>
              <SheetTitle>
                <Link href="/" className="flex items-center justify-center">
                  <Image
                    src="/logos/icon.png"
                    alt="Tekkscope Logo"
                    width={45}
                    height={45}
                  />
                  <span className="font-instrument text-black text-3xl ">
                    Tekkscope.
                  </span>
                </Link>
              </SheetTitle>
            </SheetHeader>
            <div className="w-[90%]  mx-auto flex flex-col items-center justify-start gap-4 mt-10 ">
              <Link href="/docs" className="group cursor-pointer">
                <span className="flex items-center justify-center gap-2">
                  Documentation{" "}
                  <ArrowRight className="-rotate-45 h-5 w-5 transition-transform duration-200 group-hover:-translate-y-0.5" />
                </span>
              </Link>
              <Button
                className="bg-tekk-darkest text-white cursor-pointer w-full"
                onClick={() => router.push("/authentication")}
                onTap={() => router.push("/authentication")}
              >
                Get Started
              </Button>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </nav>
  );
};

export default Navbar;
