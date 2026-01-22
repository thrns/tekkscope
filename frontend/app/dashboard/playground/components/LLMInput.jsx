"use client";
//================ IMPORTS ================//
import { Loader2Icon, ArrowUp, ChevronDown, KeyIcon, LineSquiggle } from "lucide-react";
import AutosizingTextArea from "./AutosizingTextArea";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { usePlayground } from "@/app/contexts/PlaygroundContext";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { CodeIcon, LineSquiggleIcon } from "lucide-react";

//================ COMPONENT ================//
const LLMInput = ({
  placeholder = "Let's Cook...",
  maxLines = 18,
  className = "",
}) => {
  //================ STATE & HOOKS ================//
  const {
    messages,
    inputRef,
    inputValue,
    setInputValue,
    handleSend,
    loading,
    selectedApiKey,
    setSelectedApiKey,
    apiKeys,
    mode,
    setMode,
    viewMode,
    setViewMode,
  } = usePlayground();

  //================ HANDLERS ================//
  const handleSendMessage = () => {
    if (!inputValue.trim() || loading || !selectedApiKey) return;
    handleSend();
    requestAnimationFrame(() => {
      if (inputRef?.current) {
        inputRef.current.focus();
      }
    });
  };

  //================ EFFECTS ================//
  useEffect(() => {
    if (inputRef?.current) {
      inputRef.current.focus();
    }
  }, []);

  //================ RENDER ================//
  return (
    <div
      className={`sticky bottom-0 mx-auto w-full max-w-4xl p-4 ${className}`}
    >
      <div className="flex items-center justify-end gap-3 mb-2">
        <span className="text-xs text-gray-400 mr-2">Output mode:</span>
        <button
          className={`flex items-center px-3 py-1 rounded-md transition-all border ${viewMode === "stream"
              ? "bg-tekk-darkest border-tekk text-white"
              : "bg-transparent border-tekk-dark text-gray-400 hover:text-white"
            }`}
          onClick={() => setViewMode("stream")}
          title="Stream output"
          type="button"
        >
          <LineSquiggleIcon className="w-4 h-4 mr-2" /> Stream
        </button>
        <button
          className={`flex items-center px-3 py-1 rounded-md transition-all border ${viewMode === "structured"
              ? "bg-tekk-darkest border-tekk text-white"
              : "bg-transparent border-tekk-dark text-gray-400 hover:text-white"
            }`}
          onClick={() => setViewMode("structured")}
          title="Raw output"
          type="button"
        >
          <CodeIcon className="w-4 h-4 mr-2" />
          Structured
        </button>
      </div>
      <div className="bg-tekk-darkest border border-tekk-dark relative flex flex-col gap-2 rounded-2xl p-2">
        <AutosizingTextArea
          ref={inputRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={placeholder}
          className="w-full resize-none rounded-2xl border-none bg-transparent p-4 text-white placeholder:text-gray-500 focus:outline-none focus:ring-0"
          onEnter={handleSendMessage}
          maxLines={maxLines}
        />
        <div className="flex w-full items-center justify-between">
          <div className="flex items-center gap-2">
            <Popover>
              <PopoverTrigger asChild>
                <button className="flex items-center gap-2 rounded-lg border border-tekk-dark bg-tekk-darkest px-4 py-2 text-white/90">
                  <span className="flex items-center gap-2">
                    <KeyIcon className="w-4 h-4" />{" "}
                    {selectedApiKey
                      ? apiKeys.find((k) => k.api_key === selectedApiKey)
                        ?.api_key_name
                      : "Select Key"}
                  </span>
                  <ChevronDown size={16} />
                </button>
              </PopoverTrigger>
              <PopoverContent className="bg-tekk-darkest w-56 border border-tekk-dark text-white p-2">
                <div className="flex flex-col gap-1">
                  {apiKeys && apiKeys.length > 0 ? (
                    apiKeys.map((key) => (
                      <button
                        key={key.id}
                        onClick={() => setSelectedApiKey?.(key.api_key)}
                        className={`hover:text-white flex w-full items-center justify-start rounded-md px-3 py-2 text-left text-sm transition-colors ${selectedApiKey === key.api_key
                            ? "text-white"
                            : "text-gray-400 "
                          }`}
                      >
                        {key.api_key_name}
                      </button>
                    ))
                  ) : (
                    <a
                      href="/dashboard/api-keys"
                      className="hover:bg-tekk-dark flex w-full items-center justify-start rounded-md px-3 py-2 text-left text-sm text-white"
                    >
                      Create API Key
                    </a>
                  )}
                </div>
              </PopoverContent>
            </Popover>

            <Popover>
              <PopoverTrigger asChild>
                <button className="flex items-center gap-2 rounded-lg border border-tekk-dark bg-tekk-darkest px-4 py-2 text-white/90">
                  <span className="flex items-center gap-2">
                    <ArrowUp className="w-4 h-4" />
                    {mode.charAt(0).toUpperCase() + mode.slice(1)}
                  </span>
                  <ChevronDown size={16} />
                </button>
              </PopoverTrigger>
              <PopoverContent className="bg-tekk-darkest w-56 border border-tekk-dark text-white p-2">
                <div className="flex flex-col gap-1">
                  <div className="px-3 py-1 text-xs text-tekk-primary">
                    SERP
                  </div>
                  <button
                    onClick={() => setMode("search_links")}
                    className={`hover:text-white flex w-full items-center justify-start rounded-md px-3 py-2 text-left text-sm transition-colors ${mode === "search_links" ? "text-white" : "text-gray-400 "
                      }`}
                  >
                    Search Links
                  </button>
                  <button
                    onClick={() => setMode("search_content")}
                    className={`hover:text-white flex w-full items-center justify-start rounded-md px-3 py-2 text-left text-sm transition-colors ${mode === "search_content"
                        ? "text-white"
                        : "text-gray-400 "
                      }`}
                  >
                    Search Content
                  </button>
                </div>
                <div className="flex flex-col gap-1">
                  <div className="px-3 py-1 text-xs text-tekk-primary">
                    Chat
                  </div>
                  <button
                    onClick={() => setMode("tek")}
                    className={`hover:text-white flex w-full items-center justify-start rounded-md px-3 py-2 text-left text-sm transition-colors ${mode === "tek" ? "text-white" : "text-gray-400 "
                      }`}
                  >
                    Tek
                  </button>

                  <div className="px-3 py-1 text-xs text-tekk-primary">
                    Research
                  </div>
                  <button
                    onClick={() => setMode("lens")}
                    className={`hover:text-white flex w-full items-center justify-start rounded-md px-3 py-2 text-left text-sm transition-colors ${mode === "lens" ? "text-white" : "text-gray-400 "
                      }`}
                  >
                    Lens
                  </button>
                  <button
                    onClick={() => setMode("deeplens")}
                    className={`hover:text-white flex w-full items-center justify-start rounded-md px-3 py-2 text-left text-sm transition-colors ${mode === "deeplens" ? "text-white" : "text-gray-400 "
                      }`}
                  >
                    Deeplens
                  </button>
                  <button
                    onClick={() => setMode("reportlens")}
                    className={`hover:text-white flex w-full items-center justify-start rounded-md px-3 py-2 text-left text-sm transition-colors ${mode === "reportlens" ? "text-white" : "text-gray-400 "
                      }`}
                  >
                    Reportlens
                  </button>

                  <div className="px-3 py-1 text-xs text-tekk-primary">
                    {"NL -> Structure"}
                  </div>
                  <button
                    onClick={() => setMode("nlts")}
                    className={`hover:text-white flex w-full items-center justify-start rounded-md px-3 py-2 text-left text-sm transition-colors ${mode === "nlts" ? "text-white" : "text-gray-400 "
                      }`}
                  >
                    NLTS
                  </button>
                </div>
              </PopoverContent>
            </Popover>
          </div>

          <button
            onClick={handleSendMessage}
            disabled={loading || !inputValue.trim() || !selectedApiKey}
            className="hover:bg-primary/90 bg-primary rounded-full p-2 text-primary-foreground disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Send message"
          >
            {loading ? (
              <Loader2Icon size={18} className="animate-spin" />
            ) : (
              <ArrowUp size={18} className="" />
            )}
          </button>
        </div>
      </div>
      <div className="mt-1 flex items-center justify-center">
        <p className="text-center text-xs text-muted-foreground">
          For new line press Shift + Enter
        </p>
      </div>
    </div>
  );
};

//================ EXPORTS ================//
export default LLMInput;
