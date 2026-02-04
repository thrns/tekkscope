"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { toast } from "sonner";

const DocsTopBar = () => {
  const pathname = usePathname();
  const isActive = (href) => pathname === href;
  return (
    <div className="flex items-center justify-between w-full bg-tekk-bg  px-4 py-3">
      <div className="flex items-center gap-2">
        <span className="font-inter text-xl text-white"> Docs</span>
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => toast("Examples are coming soon")}
          className={`px-3 py-2 rounded-md border border-tekk-dark text-white/80`}
        >
          Examples
        </button>
       
      </div>
    </div>
  );
};

export default DocsTopBar;