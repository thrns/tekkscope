"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  ShieldCheck,
  FileText,
  ChevronRight,
} from "lucide-react";
import {
  SidebarMenu,
} from "@/components/ui/sidebar";
import { useCallback, useState } from "react";

export function DocsSidebarLinks() {
  const pathname = usePathname();
  const isActive = useCallback((path) => path === pathname, [pathname]);

  const base =
    "flex items-center w-full px-4 py-2.5 rounded-md transition-all duration-200 ease-in-out text-sm";
  const active = "bg-tekk-bg /50 text-white/80 font-medium";
  const inactive = "text-gray-300";

  const [openApi, setOpenApi] = useState(true);

  return (
    <div className="space-y-4 px-2">
      <SidebarMenu className="space-y-2 text-gray-700">
        <Link
          href="/docs/v1/"
          passHref
          className={`${base} ${isActive("/docs/v1/") ? active : inactive}`}
        >
          <BookOpen className="mr-3 h-5 w-5" />
          <span>Quickstart</span>
        </Link>
        <Link
          href="/docs/v1/authentication"
          passHref
          className={`${base} ${isActive("/docs/v1/authentication") ? active : inactive}`}
        >
          <ShieldCheck className="mr-3 h-5 w-5" />
          <span>Authentication</span>
        </Link>
        <Link
          href="/docs/v1/pricing"
          passHref
          className={`${base} ${isActive("/pricing") ? active : inactive}`}
        >
          <FileText className="mr-3 h-5 w-5" />
          <span>Pricing</span>
        </Link>
      </SidebarMenu>

      <div className="mb-2">
        <div className="menu-item">
          <button
            onClick={() => setOpenApi((v) => !v)}
            className={`${base} ${openApi ? active : inactive} group justify-between w-full flex items-center`}
          >
            <span className="flex items-center">
              <FileText className="mr-3 h-5 w-5" />
              <span>API Reference</span>
            </span>
            <ChevronRight
              className={`ml-2 h-5 w-5 transition-transform duration-200 ${openApi ? "rotate-90 text-tekk-primary" : ""}`}
            />
          </button>
        </div>
        {openApi && (
          <div className="space-y-2 py-1 pl-2">
            <Link
              href="/docs/v1/search"
              passHref
              className={`${base} pl-6 ${isActive("/docs/v1/search") ? active : inactive}`}
            >
              <span className="mr-2 inline-block text-[10px] px-2 py-0.5 rounded-lg bg-tekk-dark text-white/90 border border-tekk-dark">POST</span>
              <span>Search</span>
            </Link>

             <Link
              href="/docs/v1/tek"
              passHref
              className={`${base} pl-6 ${isActive("/docs/v1/tek") ? active : inactive}`}
            >
              <span className="mr-2 inline-block text-[10px] px-2 py-0.5 rounded-lg bg-tekk-dark text-white/90 border border-tekk-dark">POST</span>
              <span>Tek</span>
            </Link>

            <Link
              href="/docs/v1/lens"
              passHref
              className={`${base} pl-6 ${isActive("/docs/v1/lens") ? active : inactive}`}
            >
              <span className="mr-2 inline-block text-[10px] px-2 py-0.5 rounded-lg bg-tekk-dark text-white/90 border border-tekk-dark">POST</span>
              <span>Lens</span>
            </Link>
            <Link
              href="/docs/v1/deeplens"
              passHref
              className={`${base} pl-6 ${isActive("/docs/v1/deeplens") ? active : inactive}`}
            >
              <span className="mr-2 inline-block text-[10px] px-2 py-0.5 rounded-lg bg-tekk-dark text-white/90 border border-tekk-dark">POST</span>
              <span>DeepLens</span>
            </Link>
            <Link
              href="/docs/v1/reportlens"
              passHref
              className={`${base} pl-6 ${isActive("/docs/v1/reportlens") ? active : inactive}`}
            >
              <span className="mr-2 inline-block text-[10px] px-2 py-0.5 rounded-lg bg-tekk-dark text-white/90 border border-tekk-dark">POST</span>
              <span>ReportLens</span>
            </Link>
           
           
          
          </div>
        )}
      </div>

    
    </div>
  );
}