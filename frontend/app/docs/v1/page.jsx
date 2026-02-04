"use client";
import React from "react";
import Link from "next/link";
import { CodeBlock } from "@/components/ui/code-block";

const DocsHome = () => {
  return (
    <main className="flex flex-col h-full w-full mx-auto max-w-5xl bg-tekk-bg text-white p-6 gap-6">
      <section className="flex flex-col w-full space-y-4">
        <h1 className="font-instrument font-medium text-3xl text-white">
          Quickstart
        </h1>
        <p className="font-inter text-white/80">
          Welcome to the Tekkscope API documentation. Start with a basic request to our Search endpoint.
        </p>
        <div className="rounded-2xl bg-tekk-darkest border border-tekk-dark p-4 text-white">
          <CodeBlock
            className="w-full"
            language="bash"
            filename="curl-search.sh"
          code={`curl -X POST "https://api.tekkscope.com/search/links" \\
-H "Authorization: Bearer YOUR_API_KEY" \\
-H "Content-Type: application/json" \\
-d '{
  "query": "latest advancements in AI",
  "num_results": 5
}'`}
          />
        </div>
      </section>

      <section className="w-full space-y-4">
        <h1 className="font-instrument font-medium text-3xl text-white">
          Services Overview
        </h1>
        <p className="font-inter text-white/80">
          Tekkscope provides a suite of research and intelligence APIs, ranging from raw search data to deep, agentic reports.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          
          {/* Authentication */}
          <Link href="/docs/v1/authentication" className="block h-full">
            <div className="h-full rounded-2xl bg-tekk-darkest border border-tekk-dark p-4 hover:border-tekk-primary/50 transition-colors">
              <h3 className="font-instrument font-medium text-lg text-white">
                Authentication
              </h3>
              <p className="font-inter text-sm text-white/60 mt-2">
                Learn how to authenticate your requests using API keys.
              </p>
            </div>
          </Link>

          {/* Search */}
          <Link href="/docs/v1/search" className="block h-full">
            <div className="h-full rounded-2xl bg-tekk-darkest border border-tekk-dark p-4 hover:border-tekk-primary/50 transition-colors">
              <h3 className="font-instrument font-medium text-lg text-white">
                Search
              </h3>
              <p className="font-inter text-sm text-white/60 mt-2">
                Retrieve web links or extract full page content via streaming.
              </p>
            </div>
          </Link>

          {/* Lens */}
          <Link href="/docs/v1/lens" className="block h-full">
            <div className="h-full rounded-2xl bg-tekk-darkest border border-tekk-dark p-4 hover:border-tekk-primary/50 transition-colors">
              <h3 className="font-instrument font-medium text-lg text-white">
                Lens
              </h3>
              <p className="font-inter text-sm text-white/60 mt-2">
                Quick, surface-level research with citations for instant answers.
              </p>
            </div>
          </Link>

          {/* DeepLens */}
          <Link href="/docs/v1/deeplens" className="block h-full">
            <div className="h-full rounded-2xl bg-tekk-darkest border border-tekk-dark p-4 hover:border-tekk-primary/50 transition-colors">
              <h3 className="font-instrument font-medium text-lg text-white">
                DeepLens
              </h3>
              <p className="font-inter text-sm text-white/60 mt-2">
                Iterative, deep-dive research for complex topics.
              </p>
            </div>
          </Link>

          {/* ReportLens */}
          <Link href="/docs/v1/reportlens" className="block h-full">
            <div className="h-full rounded-2xl bg-tekk-darkest border border-tekk-dark p-4 hover:border-tekk-primary/50 transition-colors">
              <h3 className="font-instrument font-medium text-lg text-white">
                ReportLens
              </h3>
              <p className="font-inter text-sm text-white/60 mt-2">
                Generate and download comprehensive Markdown reports.
              </p>
            </div>
          </Link>

           {/* Tek */}
           <Link href="/docs/v1/tek" className="block h-full">
            <div className="h-full rounded-2xl bg-tekk-darkest border border-tekk-dark p-4 hover:border-tekk-primary/50 transition-colors">
              <h3 className="font-instrument font-medium text-lg text-white">
                Tek
              </h3>
              <p className="font-inter text-sm text-white/60 mt-2">
                Fast, standard language model for conversational tasks.
              </p>
            </div>
          </Link>

           {/* Tek Pro */}
           <Link href="/docs/v1/tek-pro" className="block h-full">
            <div className="h-full rounded-2xl bg-tekk-darkest border border-tekk-dark p-4 hover:border-tekk-primary/50 transition-colors">
              <h3 className="font-instrument font-medium text-lg text-white">
                Tek Pro
              </h3>
              <p className="font-inter text-sm text-white/60 mt-2">
                Advanced reasoning agent for complex problem solving.
              </p>
            </div>
          </Link>

        </div>
      </section>
    </main>
  );
};

export default DocsHome;
