"use client";
//================ IMPORTS ================//
import { ChevronLeft, Plus, Coins } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import NotificationsButton from "./NotificationsButton";
import CreditsButton from "./CreditsButton";
import { isMobile } from "react-device-detect";
import CustomButton from "@/components/ui/custom-button";
import { useState } from "react";
import { useApiKeys } from "@/app/contexts/ApiKeysContext";
import { LoaderIcon } from "lucide-react";
import { CreateApiKeyDialog } from "@/components/CreateApiKeyDialog";
import * as Popover from "@radix-ui/react-popover";
import { CreditsProvider, useCredits } from "@/app/contexts/CreditsContext";
import { useAuth } from "@/app/contexts/AuthContext";

//================ COMPONENT ================//
const TopBar = () => {
  //================ STATE & HOOKS ================//
  const router = useRouter();
  const { generateApiKey } = useApiKeys();
  const [isGenerating, setIsGenerating] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const pathname = usePathname();
  const isMainDashboard = pathname === "/dashboard";

  //================ HANDLERS ================//
  const handleGenerateKey = async (name) => {
    setIsGenerating(true);
    const newKey = await generateApiKey(name);
    setIsGenerating(false);
    if (newKey) {
      router.push("/dashboard/api-keys");
    }
    return newKey;
  };

  // Handle back navigation
  const handleBack = () => {
    router.back();
  };

  //================ HELPER ================//
  // Get the current page name from pathname
  const getPageName = () => {
    const segments = pathname.split("/").filter((segment) => segment !== "");
    if (segments.length <= 1) return "Dashboard";

    // Capitalize the last segment
    const lastSegment = segments[segments.length - 1];
    return lastSegment.charAt(0).toUpperCase() + lastSegment.slice(1);
  };

  //================ JSX ================//
  return (
    <>
      <div className="flex h-16 items-center justify-between px-6 py-4">
        {/* Left Section - Dashboard Breadcrumb */}
        <div className="flex items-center">
          {!isMainDashboard && (
            <button
              onClick={handleBack}
              className="mr-3 flex h-8 w-8 items-center justify-center rounded-full text-gray-200"
            >
              <ChevronLeft size={20} />
            </button>
          )}
          <h1 className="text-xl font-semibold text-gray-200">
            {getPageName()}
          </h1>
        </div>

        {/* Right Section - Actions */}
        <div className="flex items-center gap-4">
          {/* Credits Button */}
          <CreditsButton />

          {/* Notifications Button */}
          <NotificationsButton iconSize={isMobile ? 16 : 20} />

          {/* Generate Key Button */}
          <CustomButton
            onClick={() => setIsDialogOpen(true)}
            disabled={isGenerating}
            variant="outline"
            className=" w-auto items-center space-x-2 rounded-full bg-tekk-darkest  text-white px-4 py-2 text-sm font-medium transition-all flex"
            data-tooltip-id="generate-key"
            data-tooltip-content="Generate Key"
          >
            {isGenerating ? (
              <LoaderIcon className="animate-spin" />
            ) : (
              <Plus size={18} />
            )}{" "}
            Api Keys
          </CustomButton>
        </div>
      </div>
      <CreateApiKeyDialog
        open={isDialogOpen}
        onOpenChange={setIsDialogOpen}
        onCreate={handleGenerateKey}
        isGenerating={isGenerating}
      />
    </>
  );
};

//================ EXPORTS ================//
export default TopBar;
