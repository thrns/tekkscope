"use client";
import React from "react";
import { CodeBlock } from "@/components/ui/code-block";

const ReportLensDocs = () => {
  return (
    <main className="flex flex-col h-full w-full mx-auto max-w-5xl bg-tekk-bg text-white p-6 gap-6">
      <section className="space-y-4">
        <h1 className="font-instrument font-medium text-3xl text-white">ReportLens API</h1>
        <p className="font-inter text-white/80">
          ReportLens is a specialized service for generating comprehensive, structured reports. 
          It performs extensive research and compiles the findings into a downloadable Markdown document.
        </p>

        {/* Generate Report Endpoint */}
        <div className="rounded-2xl bg-tekk-darkest border border-tekk-dark overflow-hidden">
          <div className="p-6 border-b border-tekk-dark">
            <h2 className="font-instrument font-medium text-xl text-white">Generate Report</h2>
            <p className="font-inter text-white/80 text-sm mt-2">
              Trigger the report generation process. Returns a URL to the generated file upon completion.
            </p>
            <div className="mt-4 flex items-center gap-2 text-sm font-mono">
              <span className="px-2 py-1 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">POST</span>
              <span className="text-white/60">/reportlens/research</span>
            </div>
          </div>
          
          <div className="p-6 space-y-4 bg-tekk-bg/50">
            <div>
              <h3 className="text-sm font-medium text-white mb-2">Request Body</h3>
              <CodeBlock
                language="json"
                filename="payload.json"
                code={`{
  "query": "string",
  "settings": {
    "max_results": 12,      // Optional.
    "iteration_depth": 4    // Optional. Depth of research.
  }
}`}
              />
            </div>

            <div>
              <h3 className="text-sm font-medium text-white mb-2">Example Request</h3>
              <CodeBlock
                language="bash"
                filename="curl.sh"
                code={`curl -X POST "https://api.tekkscope.com/reportlens/research" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "Market analysis of electric vehicles in Europe 2024"
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
    "summary": "Short summary of the report...",
    "download_url": "https://storage.tekkscope.com/reports/...",
    "formatted_findings": "# Full Markdown Content..."
  }
}`}
              />
            </div>
          </div>
        </div>

        {/* Streaming Endpoint */}
        <div className="rounded-2xl bg-tekk-darkest border border-tekk-dark overflow-hidden">
          <div className="p-6 border-b border-tekk-dark">
            <h2 className="font-instrument font-medium text-xl text-white">Stream Report Generation</h2>
            <p className="font-inter text-white/80 text-sm mt-2">
              Monitor the report creation progress. The final message usually contains the download URL.
            </p>
            <div className="mt-4 flex items-center gap-2 text-sm font-mono">
              <span className="px-2 py-1 rounded bg-green-500/20 text-green-400 border border-green-500/30">GET</span>
              <span className="text-white/60">/reportlens/research/stream</span>
            </div>
          </div>

          <div className="p-6 space-y-4 bg-tekk-bg/50">
             <div>
              <h3 className="text-sm font-medium text-white mb-2">Query Parameters</h3>
              <ul className="space-y-2 text-sm text-white/80 font-mono">
                <li><span className="text-tekk-primary">query</span> (string) - Required</li>
              </ul>
            </div>

            <div>
              <h3 className="text-sm font-medium text-white mb-2">Example Request</h3>
              <CodeBlock
                language="javascript"
                filename="stream.js"
                code={`const eventSource = new EventSource(
  "https://api.tekkscope.com/reportlens/research/stream?query=ev+market+analysis&token=YOUR_API_KEY"
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === "thinking") {
    console.log("Status:", data.content.phase);
  } else if (data.type === "response") {
    // Checks if content is a URL
    if (data.content.startsWith("http")) {
        console.log("Download Report:", data.content);
    } else {
        // Or partial content updates
        console.log("Content:", data.content);
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

export default ReportLensDocs;
