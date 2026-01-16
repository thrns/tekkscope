import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { LoaderIcon } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "./ui/dialog";
import { Input } from "./ui/input";
import { Skeleton } from "./ui/skeleton";
import { toast } from "sonner";
export function CreateApiKeyDialog({
  open,
  onOpenChange,
  onCreate,
  isGenerating,
}) {
  const [name, setName] = useState("");
  const [apiKey, setApiKey] = useState(null);

  useEffect(() => {
    if (!open) {
      setName("");
      setApiKey(null);
    }
  }, [open]);

  const handleCreate = async () => {
    const result = await onCreate(name);
    if (result) {
      setApiKey(result);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-tekk-darkest text-white border-tekk-dark">
        <DialogHeader>
          <DialogTitle className="text-white">
            {apiKey ? "Save your key" : "Create new secret key"}
          </DialogTitle>
        </DialogHeader>
        {apiKey ? (
          <div>
            <p className="text-gray-400 mb-4">
              Please save your secret key in a safe place since you won’t be
              able to view it again. Keep it secure, as anyone with your API key
              can make requests on your behalf. If you do lose it, you’ll need
              to generate a new one.
            </p>
            <div className="flex items-center space-x-2">
              <Input
                value={apiKey}
                readOnly
                className="bg-tekk-dark border-tekk-dark"
              />
              <Button
              variant="outline"
                onClick={() => {
                  toast.success("API Key copied to clipboard!");
                  navigator.clipboard.writeText(apiKey);
                }}
                className="bg-tekk-darkest "
              >
                Copy
              </Button>
            </div>
          </div>
        ) : (
          <div>
            <p className="text-gray-400 mb-4">Name (Optional)</p>
            <Input
              placeholder="My Test Key"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="bg-tekk-darkest border-white"
            />
          </div>
        )}
        <DialogFooter>
          {!apiKey && (
            <div className="flex justify-end w-full">
              <Button
                variant="ghost"
                onClick={() => onOpenChange(false)}
                className="mr-2"
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreate}
                disabled={isGenerating}
                className="bg-tekk-bg text-white cursor-pointer"
              >
                {isGenerating ? (
                  <>
                    <LoaderIcon className="animate-spin mr-2" />
                    Generating...
                  </>
                ) : (
                  "Create secret key"
                )}
              </Button>
            </div>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
