"use client";
import {useState, useEffect} from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot, ChevronUp, LogOutIcon } from "lucide-react";

import { useAuth } from "@/app/contexts/AuthContext";
import { useRouter } from "next/navigation";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarFooter,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import Image from "next/image";
import { signout } from "@/lib/actions/auth-actions";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export function SidebarFooterComponent() {
  const { user, setUser } = useAuth();
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const router = useRouter();

  if (!isMounted) {
    return null;
  }

  return (
    <SidebarFooter>
      <SidebarMenu>
        <SidebarMenuItem>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button className="mb-2 flex h-auto w-full justify-between rounded-xl  p-4">
                <div className="flex h-full w-full justify-between gap-2">
                  <Avatar>
                    <Image
                      fill="true"
                      src={user?.avatarURL || "/placeholder-avatar.png"}
                      alt={user?.name || "User"}
                    />
                    <AvatarFallback>
                      {user?.name
                        ?.split(" ")
                        .map((n) => n[0])
                        .join("")
                        .toUpperCase() || "?"}
                    </AvatarFallback>
                  </Avatar>
                  <div className="w-full text-left leading-tight">
                    <p className="font-semibold">
                      {user?.name || "Loading..."}
                    </p>
                    <p className="text-sm text-gray-500 line-clamp-1">
                      {user?.email ? `${user.email.slice(0, 12)}...` : "..."}
                    </p>
                  </div>
                  <ChevronUp className="ml-auto transition-transform group-data-[state=open]/collapsible:rotate-180" />
                </div>
              </Button>
            </DropdownMenuTrigger>

            <DropdownMenuContent
              side="top"
              className="bg-tekk-bg text-white border-0 w-60"
            >
              <DropdownMenuItem>
                <Link
                  className="flex items-center justify-center gap-2"
                  href="/docs/v1"
                >
                  <Bot /> Api Reference
                </Link>
              </DropdownMenuItem>

              <DropdownMenuItem>
                <SidebarMenuButton
                  className=""
                  onClick={async () => {
                    setUser(null);
                    localStorage.removeItem("user");
                    await signout();
                  }}
                >
                  <LogOutIcon /> Logout
                </SidebarMenuButton>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarFooter>
  );
}
