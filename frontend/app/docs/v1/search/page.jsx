"use client";
import React from "react";
import { CodeBlock } from "@/components/ui/code-block";

const SearchDocs = () => {
  return (
    <main className="flex flex-col h-full w-full mx-auto max-w-5xl bg-tekk-bg text-white p-6 gap-6">
      <section className="space-y-4">
        <h1 className="font-instrument font-medium text-3xl text-white">Search API</h1>
        <p className="font-inter text-white/80">
          The Search API allows you to programmatically retrieve search results from the web. 
          It supports retrieving direct links or full content extraction via streaming.
        </p>

        {/* Links Endpoint */}
        <div className="rounded-2xl bg-tekk-darkest border border-tekk-dark overflow-hidden">
          <div className="p-6 border-b border-tekk-dark">
            <h2 className="font-instrument font-medium text-xl text-white">Get Search Links</h2>
            <p className="font-inter text-white/80 text-sm mt-2">
              Retrieve a list of search results (links and titles) for a given query.
            </p>
            <div className="mt-4 flex items-center gap-2 text-sm font-mono">
              <span className="px-2 py-1 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">POST</span>
              <span className="text-white/60">/search/links</span>
            </div>
          </div>
          
          <div className="p-6 space-y-4 bg-tekk-bg/50">
            <div>
              <h3 className="text-sm font-medium text-white mb-2">Request Body</h3>
              <CodeBlock
                language="json"
                filename="payload.json"
                code={`{
  "query": "string",           // Required. The search query.
  "num_results": 10,           // Optional. Default: 10.
  "n_queries": 3,              // Optional. Number of sub-queries for enhanced search.
  "enhanced_search": false     // Optional. Use LLM to generate better queries.
}`}
              />
            </div>

            <div>
              <h3 className="text-sm font-medium text-white mb-2">Example Request</h3>
              <CodeBlock
                language="bash"
                filename="curl.sh"
                code={`curl -X POST "https://api.tekkscope.com/search/links" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "latest advancements in nuclear fusion",
    "num_results": 5,
    "enhanced_search": true
  }'`}
              />
            </div>

            <div>
              <h3 className="text-sm font-medium text-white mb-2">Response</h3>
              <CodeBlock
                language="json"
                filename="response.json"
                code={`{
  "results": [
    {
      "title": "Nuclear Fusion Breakthrough...",
      "url": "https://example.com/fusion-news"
    },
    ...
  ]
}`}
              />
            </div>
          </div>
        </div>

        {/* Content Stream Endpoint */}
        <div className="rounded-2xl bg-tekk-darkest border border-tekk-dark overflow-hidden">
          <div className="p-6 border-b border-tekk-dark">
            <h2 className="font-instrument font-medium text-xl text-white">Stream Content Extraction</h2>
            <p className="font-inter text-white/80 text-sm mt-2">
              Perform a search and stream back extracted text content from the visited pages.
              Useful for RAG pipelines or deep analysis.
            </p>
            <div className="mt-4 flex items-center gap-2 text-sm font-mono">
              <span className="px-2 py-1 rounded bg-green-500/20 text-green-400 border border-green-500/30">GET</span>
              <span className="text-white/60">/search/content/stream</span>
            </div>
          </div>

          <div className="p-6 space-y-4 bg-tekk-bg/50">
             <div>
              <h3 className="text-sm font-medium text-white mb-2">Query Parameters</h3>
              <ul className="space-y-2 text-sm text-white/80 font-mono">
                <li><span className="text-tekk-primary">query</span> (string) - Required</li>
                <li><span className="text-tekk-primary">num_results</span> (int) - Default: 8</li>
                <li><span className="text-tekk-primary">enhanced_search</span> (bool) - Default: false</li>
              </ul>
            </div>

            <div>
              <h3 className="text-sm font-medium text-white mb-2">Example Request</h3>
              <CodeBlock
                language="javascript"
                filename="stream.js"
                code={`const response = await fetch(
  "https://api.tekkscope.com/search/content/stream?query=ai+news",
  { headers: { Authorization: "Bearer YOUR_API_KEY" } }
);

const reader = response.body.getReader();
// Read SSE frames from reader and close on [END_OF_STREAM].`}
              />
            </div>
          </div>
        </div>

      </section>
    </main>
  );
};

export default SearchDocs;
