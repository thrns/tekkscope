"use client";

import { ControllerProvider } from "@/app/contexts/ControllerContext";
import TopBar from "./components/TopBar/TopBar";
import Sidebar from "./components/sidebar/Sidebar";

import { ApiKeysProvider } from "@/app/contexts/ApiKeysContext";
import { useEffect } from "react";
import { useAuth } from "@/app/contexts/AuthContext";
import { useRouter } from "next/navigation";
import { CreditsProvider } from "@/app/contexts/CreditsContext";

export default function DashboardClientLayout({ children }) {
  const { user } = useAuth();
  const router = useRouter();

  return (
    <>
      <ControllerProvider>
        <ApiKeysProvider>
          <CreditsProvider>
            <main className={`flex h-screen w-full bg-tekk-bg `}>
              <aside className="flex w-full overflow-hidden ">
                {/* Render the Sidebar only for dashboard-related routes */}
                <Sidebar />
                <div className="flex w-full max-w-full flex-col overflow-hidden pb-20 md:pb-0">
                  <TopBar />
                  {children}{" "}
                </div>
              </aside>
            </main>
          </CreditsProvider>
        </ApiKeysProvider>
      </ControllerProvider>{" "}
    </>
  );
}
