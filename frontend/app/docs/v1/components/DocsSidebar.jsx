"use client";
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
} from "@/components/ui/sidebar";
import Image from "next/image";
import { DocsSidebarLinks } from "./DocsSidebarLinks";
import Link from "next/link";

export default function DocsSidebar() {
  return (
    <Sidebar
      collapsible="offcanvas"
      className="fixed left-0 top-0 z-40 h-screen w-64  text-white"
    >
      {" "}
      <SidebarHeader className="relative flex items-center justify-between p-6">
        <Link href="/" className="flex items-center justify-center gap-2">
          <Image src="/logos/icon.png" width={40} height={40} alt="Tekkscope" />
          <span className="text-2xl font-instrument text-white">Tekkscope</span>
        </Link>
      </SidebarHeader>
      <SidebarContent className="overflow-y-auto p-4">
        <DocsSidebarLinks />
      </SidebarContent>
    </Sidebar>
  );
}
