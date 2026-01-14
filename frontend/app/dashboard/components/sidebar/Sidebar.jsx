"use client";
import SidebarHeaderComponent from "./SidebarHeader";
import { Sidebar, SidebarContent } from "@/components/ui/sidebar";
import { SidebarFooterComponent } from "./SidebarFooter";
import { SidebarLinks } from "./SidebarLinks";

export default function DashboardSidebar() {
  return (
    <Sidebar
      collapsible="offcanvas"
      className="fixed left-0 top-0 z-40 h-screen w-64  text-white"
    >
      <SidebarHeaderComponent />

      <SidebarContent className="overflow-y-auto p-4">
        <SidebarLinks />
      </SidebarContent>

      <SidebarFooterComponent />
    </Sidebar>
  );
}
