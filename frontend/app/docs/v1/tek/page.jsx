"use client";
import React from "react";
import { CodeBlock } from "@/components/ui/code-block";

const TekDocs = () => {
  return (
    <main className="flex flex-col h-full w-full mx-auto max-w-5xl bg-tekk-bg text-white p-6 gap-6">
      <section className="space-y-4">
        <h1 className="font-instrument font-medium text-3xl text-white">Tek API</h1>
        <p className="font-inter text-white/80">
          Tek is our advanced reasoning model. It uses a graph-based agentic approach to "think" before answering, 
          allowing it to perform research, verification, and complex multi-step reasoning.
        </p>

        {/* Chat Completion Endpoint */}
        <div className="rounded-2xl bg-tekk-darkest border border-tekk-dark overflow-hidden">
          <div className="p-6 border-b border-tekk-dark">
            <h2 className="font-instrument font-medium text-xl text-white">Chat Completion</h2>
            <p className="font-inter text-white/80 text-sm mt-2">
              Generate a reasoned response. The model may take longer to respond as it formulates its thoughts.
            </p>
            <div className="mt-4 flex items-center gap-2 text-sm font-mono">
              <span className="px-2 py-1 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">POST</span>
              <span className="text-white/60">/tek/chat-completion</span>
            </div>
          </div>
          
          <div className="p-6 space-y-4 bg-tekk-bg/50">
            <div>
              <h3 className="text-sm font-medium text-white mb-2">Request Body</h3>
              <CodeBlock
                language="json"
                filename="payload.json"
                code={`{
  "query": "string"
}`}
              />
            </div>

            <div>
              <h3 className="text-sm font-medium text-white mb-2">Example Request</h3>
              <CodeBlock
                language="bash"
                filename="curl.sh"
                code={`curl -X POST "https://api.tekkscope.com/tek/chat-completion" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "Explain the concept of entropy"
  }'`}
              />
            </div>

            <div>
              <h3 className="text-sm font-medium text-white mb-2">Response</h3>
              <CodeBlock
                language="json"
                filename="response.json"
                code={`{
  "response": "Entropy is a measure of disorder..."
}`}
              />
            </div>
          </div>
        </div>

        {/* Streaming Endpoint */}
        <div className="rounded-2xl bg-tekk-darkest border border-tekk-dark overflow-hidden">
          <div className="p-6 border-b border-tekk-dark">
            <h2 className="font-instrument font-medium text-xl text-white">Stream Thinking & Response</h2>
            <p className="font-inter text-white/80 text-sm mt-2">
              Stream the model's thought process (thinking events) followed by the final response. 
              This provides visibility into the agent's actions.
            </p>
            <div className="mt-4 flex items-center gap-2 text-sm font-mono">
              <span className="px-2 py-1 rounded bg-green-500/20 text-green-400 border border-green-500/30">GET</span>
              <span className="text-white/60">/tek/chat-completion/stream</span>
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
  "https://api.tekkscope.com/tek/chat-completion/stream?query=complex+question&token=YOUR_API_KEY"
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === "thinking") {
    // Shows the model's internal reasoning phase
    console.log("Thinking:", data.content);
  } else if (data.type === "response") {
    // The actual answer content
    console.log("Response:", data.content);
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

export default TekDocs;
