"use client";
import React from "react";
import { CodeBlock } from "@/components/ui/code-block";

const DeepLensDocs = () => {
  return (
    <main className="flex flex-col h-full w-full mx-auto max-w-5xl bg-tekk-bg text-white p-6 gap-6">
      <section className="space-y-4">
        <h1 className="font-instrument font-medium text-3xl text-white">
          DeepLens API
        </h1>
        <p className="font-inter text-white/80">
          DeepLens performs in-depth, iterative research. It explores a topic by
          generating follow-up questions, performing multiple rounds of
          searching, and synthesizing a comprehensive answer with citations.
        </p>

        {/* Detailed Research Endpoint */}
        <div className="rounded-2xl bg-tekk-darkest border border-tekk-dark overflow-hidden">
          <div className="p-6 border-b border-tekk-dark">
            <h2 className="font-instrument font-medium text-xl text-white">
              Detailed Research
            </h2>
            <p className="font-inter text-white/80 text-sm mt-2">
              Start a deep research task. This process can take longer than
              standard requests due to the iterative nature.
            </p>
            <div className="mt-4 flex items-center gap-2 text-sm font-mono">
              <span className="px-2 py-1 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                POST
              </span>
              <span className="text-white/60">/deeplens/research</span>
            </div>
          </div>

          <div className="p-6 space-y-4 bg-tekk-bg/50">
            <div>
              <h3 className="text-sm font-medium text-white mb-2">
                Request Body
              </h3>
              <CodeBlock
                language="json"
                filename="payload.json"
                code={`{
  "query": "string",
  "settings": {
    "max_results": 10,      // Optional. Results per iteration.
    "iteration_depth": 3    // Optional. How many rounds of research to perform.
  }
}`}
              />
            </div>

            <div>
              <h3 className="text-sm font-medium text-white mb-2">
                Example Request
              </h3>
              <CodeBlock
                language="bash"
                filename="curl.sh"
                code={`curl -X POST "https://api.tekkscope.com/deeplens/research" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "impact of quantum computing on cryptography",
    "settings": { "iteration_depth": 3 }
  }'`}
              />
            </div>

            <div>
              <h3 className="text-sm font-medium text-white mb-2">Response</h3>
              <CodeBlock
                language="json"
                filename="response.json"
                code={`{
  "result": {
    "summary": "Detailed explanation of quantum threats...",
    "findings": [...],
    "sources": [...]
  }
}`}
              />
            </div>
          </div>
        </div>

        {/* Streaming Endpoint */}
        <div className="rounded-2xl bg-tekk-darkest border border-tekk-dark overflow-hidden">
          <div className="p-6 border-b border-tekk-dark">
            <h2 className="font-instrument font-medium text-xl text-white">
              Stream Deep Research
            </h2>
            <p className="font-inter text-white/80 text-sm mt-2">
              Watch the research unfold step-by-step. This is highly recommended
              for DeepLens due to the longer latency.
            </p>
            <div className="mt-4 flex items-center gap-2 text-sm font-mono">
              <span className="px-2 py-1 rounded bg-green-500/20 text-green-400 border border-green-500/30">
                GET
              </span>
              <span className="text-white/60">/deeplens/research/stream</span>
            </div>
          </div>

          <div className="p-6 space-y-4 bg-tekk-bg/50">
            <div>
              <h3 className="text-sm font-medium text-white mb-2">
                Query Parameters
              </h3>
              <ul className="space-y-2 text-sm text-white/80 font-mono">
                <li>
                  <span className="text-tekk-primary">query</span> (string) -
                  Required
                </li>
              </ul>
            </div>

            <div>
              <h3 className="text-sm font-medium text-white mb-2">
                Example Request
              </h3>
              <CodeBlock
                language="javascript"
                filename="stream.js"
                code={`const eventSource = new EventSource(
  "https://api.tekkscope.com/deeplens/research/stream?query=quantum+cryptography&token=YOUR_API_KEY"
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === "thinking") {
    // Provides detailed updates: "urls_preview", "calling_detailed_research", etc.
    console.log("Phase:", data.content.phase);
  } else if (data.type === "response") {
    // The final answer or citations
    console.log("Data:", data.content);
  }
};`}
              />
            </div>
          </div>
        </div>
      </section>
    </main>
  );
};

export default DeepLensDocs;
