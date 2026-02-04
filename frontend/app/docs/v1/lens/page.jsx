"use client";
import React from "react";
import { CodeBlock } from "@/components/ui/code-block";

const LensDocs = () => {
  return (
    <main className="flex flex-col h-full w-full mx-auto max-w-5xl bg-tekk-bg text-white p-6 gap-6">
      <section className="space-y-4">
        <h1 className="font-instrument font-medium text-3xl text-white">
          Lens API
        </h1>
        <p className="font-inter text-white/80">
          Lens is designed for quick, surface-level research. It performs a
          search, aggregates results, and provides a concise summary with
          citations. Ideal for "What is..." or "Who is..." style questions.
        </p>

        {/* Standard Research Endpoint */}
        <div className="rounded-2xl bg-tekk-darkest border border-tekk-dark overflow-hidden">
          <div className="p-6 border-b border-tekk-dark">
            <h2 className="font-instrument font-medium text-xl text-white">
              Quick Research
            </h2>
            <p className="font-inter text-white/80 text-sm mt-2">
              Get a quick summary and citations for a topic.
            </p>
            <div className="mt-4 flex items-center gap-2 text-sm font-mono">
              <span className="px-2 py-1 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                POST
              </span>
              <span className="text-white/60">/lens/research</span>
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
    "max_results": 5  // Optional. Number of search results to analyze.
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
                code={`curl -X POST "https://api.tekkscope.com/lens/research" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "summary of the latest spacex launch",
    "settings": { "max_results": 5 }
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
    "summary": "SpaceX successfully launched...",
    "sources": [
      { "title": "SpaceX Launch", "url": "https://..." },
      ...
    ]
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
              Stream Quick Research
            </h2>
            <p className="font-inter text-white/80 text-sm mt-2">
              Stream the research process and results in real-time.
            </p>
            <div className="mt-4 flex items-center gap-2 text-sm font-mono">
              <span className="px-2 py-1 rounded bg-green-500/20 text-green-400 border border-green-500/30">
                GET
              </span>
              <span className="text-white/60">/lens/research/stream</span>
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
  "https://api.tekkscope.com/lens/research/stream?query=spacex+launch&token=YOUR_API_KEY"
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === "thinking") {
    // Updates on search progress
    console.log("Thinking:", data.content);
  } else if (data.type === "response") {
    // Streamed content chunks or citations
    if (data.content.citations) {
        console.log("Sources:", data.content.citations);
    } else {
        process.stdout.write(data.content); 
    }
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

export default LensDocs;
