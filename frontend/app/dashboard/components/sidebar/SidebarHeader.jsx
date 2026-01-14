"use client";

import { SidebarHeader } from "@/components/ui/sidebar";
import Image from "next/image";

const SidebarHeaderComponent = () => {
  return (
    <SidebarHeader className="relative flex items-center justify-between p-6">
      <div className="flex items-center justify-center gap-2">
        <Image src="/logos/icon.png" width={50} height={50} alt="Logo" />
        <span className="text-3xl font-instrument text-white">
          Tekkscope
        </span>
      </div>
    </SidebarHeader>
  );
};

export default SidebarHeaderComponent;
