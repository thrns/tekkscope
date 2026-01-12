"use client";
//================ IMPORTS ================//
import { useAuth } from "@/app/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import {
  FlaskConical,
  KeyRound,
  BookText,
  Code,
  Copy,
  ChevronDown,
  Mic,
  Link as LinkIcon,
  Image as ImageIcon,
} from "lucide-react";
import { CodeBlock } from "@/components/ui/code-block";

//================ SUB-COMPONENTS ================//
const ActionCard = ({ href, icon: Icon, title, description }) => (
  <Link href={href} passHref>
    <div className="flex cursor-pointer items-center gap-4 rounded-lg border border-tekk-dark text-white bg-tekk-bg p-4 transition-colors hover:border-tekk-primary">
      <Icon className="h-8 w-8 text-tekk-primary" />
      <div>
        <h3 className="font-medium">{title}</h3>
        <p className="text-sm text-gray-400">{description}</p>
      </div>
    </div>
  </Link>
);

//================ MAIN COMPONENT ================//
const DashboardPage = () => {
  //================ STATE & HOOKS ================//
  const { user } = useAuth();

  //================ RENDER ================//
  return (
    <div className="h-full w-full bg-tekk-bg text-white p-4 sm:p-6 md:p-8">
      <div className="mx-auto max-w-5xl">
        {/* Header */}
        <header className="mb-12">
          <h1 className="text-3xl font-medium text-white font-instrument">
            Hello, {user?.name || "User"}
          </h1>
          <p className="mt-1 text-muted-foreground">
            The fastest way add a research brain to you apps
          </p>
        </header>

        {/* Main Actions */}
        <div className="mb-12 grid grid-cols-1 gap-4 md:grid-cols-3">
          <ActionCard
            href="/dashboard/playground"
            icon={FlaskConical}
            title="Go to Playground"
            description="Experiment with models and prompts."
          />
          <ActionCard
            href="/dashboard/api-keys"
            icon={KeyRound}
            title="Manage API Keys"
            description="Create and manage your API keys."
          />
          <ActionCard
            href="#"
            icon={BookText}
            title="Explore Docs"
            description="Read our documentation."
          />
        </div>

        {/* Get Started */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-medium tracking-tight text-white">
              Get started with Tekkscope API
            </h2>
            <div className="flex items-center gap-4">
              <Link href="/dashboard/api-keys" passHref>
                <Button
                  variant="outline"
                  className="bg-tekk-darkest border-tekk-dark text-white "
                >
                  View API keys
                </Button>
              </Link>
              <Link href="#" passHref>
                <Button
                  variant="outline"
                  className="bg-tekk-darkest border-tekk-dark text-white"
                >
                  Explore docs
                </Button>
              </Link>
            </div>
          </div>
          <CodeBlock
            language="bash"
            filename="curl-chat-completions.sh"
            code={`curl -X POST "https://api.tekkscope.com/chat/completions" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ts_xxx" \
-d '{
  "query": "Summarize the latest trends in edge AI"
}'`} />
        </div>
      </div>
    </div>
  );
};

//================ EXPORTS ================//
export default DashboardPage;
