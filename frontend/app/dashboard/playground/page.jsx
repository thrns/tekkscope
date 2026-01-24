"use client";
//================ IMPORTS ================//
import {
  PlaygroundProvider,
  usePlayground,
} from "@/app/contexts/PlaygroundContext";

import LLMInput from "./components/LLMInput";

import MessageBubble from './components/MessageBubble';

//================ SUB-COMPONENTS ================//
const PlaygroundContent = () => {
  //================ STATE & HOOKS ================//
  const {
    messages,
    loading,
    thinking,
    scrollRef,
    inputRef,
    inputValue,
    setInputValue,
    handleSend,
    mode,
    connectionStatus,
    thinkingFeed,

  } = usePlayground();

  //================ RENDER ================//
  return (
    <div className="flex h-full max-h-[95vh] w-full flex-col bg-tekk-bg text-white relative">

      <div className="mx-auto flex h-full w-full max-w-5xl flex-col px-4 sm:px-6">
        <div
          ref={scrollRef}
          className="flex flex-1 flex-col gap-4 overflow-y-auto rounded-2xl p-4"
        >
          {messages.length === 0 && !loading && !thinking ? (
            <div className="flex flex-1 items-center justify-center">
              <h1 className=" text-3xl font-instrument font-medium text-white/50">Hey, let's test few models out!</h1>
            </div>
          ) : (
            messages.map((m, i) => (
              <div
                key={i}
                className={
                  m.role === "user" ? "flex justify-end" : "flex justify-start"
                }
              >
                <MessageBubble message={m} />
              </div>
            ))
          )}
          {thinking && (
            <div className="flex justify-start mt-4">
              <div className="max-w-2xl rounded-2xl bg-tekk-dark px-4 py-2 text-white/70 animate-pulse delay-100">
                {(() => {
                  const t = thinking;
                  const humanize = (phase) => {
                    switch (phase) {
                      case 'router': return 'Thinking...';
                      case 'agent': return 'Drafting a response…';
                      case 'tools': return 'Thinking...';
                      case 'urls_preview': return 'Collecting sources…';
                      case 'summarizing': return 'Summarizing findings…';
                      case 'compiling_report': return 'Compiling the report…';
                      case 'finalizing': return 'Finalizing the response…';
                      case 'search': return 'Searching the web…';
                      case 'visiting': return 'Visiting page…';
                      case 'scraped': return 'Reading page…';
                      default: return 'Thinking…';
                    }
                  };
                  const asString = (val) => typeof val === 'string' && val.trim().length > 0;
                  const firstHost = (links) => {
                    try {
                      if (!Array.isArray(links) || links.length === 0) return '';
                      const u = links[0]?.url;
                      if (!u || typeof u !== 'string') return '';
                      const normalized = /^https?:\/\//i.test(u) ? u : `https://${u}`;
                      return new URL(normalized).hostname;
                    } catch { return ''; }
                  };
                  if (t && typeof t === 'object') {
                    const phase = t.phase || t.stage;
                    const previewCandidates = [t.url, t.narrative, t.text_preview, t.summary, t.answer];
                    let preview = previewCandidates.find(asString) || firstHost(t.links_preview) || '';
                    const line = [humanize(phase), preview].filter(Boolean).join(' ');
                    return (
                      <div>
                        <p className="text-sm italic">{line || 'Thinking…'}</p>
                        {Array.isArray(thinkingFeed) && thinkingFeed.length > 0 && (
                          <div className="mt-2 max-h-40 overflow-y-auto space-y-1">
                            {thinkingFeed.slice(-15).map((e, idx) => (
                              <div key={idx} className="text-xs text-white/70">
                                <span className="mr-2 font-medium">{e.phase}</span>
                                <span className="mr-2">{String(e.message).slice(0, 160)}</span>
                                {e.host && e.href && (
                                  <a href={e.href} target="_blank" rel="noreferrer" className="text-tekk-primary underline">
                                    {e.host}
                                  </a>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  }
                  return <p className="text-sm italic">{String(t || 'Thinking…')}</p>;
                })()}
              </div>
            </div>
          )}
          {loading && !thinking && (
            <div className="flex justify-start mt-4">
              <div className="max-w-2xl rounded-2xl bg-tekk-dark px-4 py-2 text-white/70 animate-pulse">
                <p className="text-sm italic">Processing...</p>
              </div>
            </div>
          )}
        </div>

        {connectionStatus === 'error' && (
          <div className="w-full max-w-5xl mx-auto mb-2">
            <div className="rounded-2xl bg-red-900/40 border border-red-400/40 p-2 text-xs text-red-200">
              Stream connection error
            </div>
          </div>
        )}

        <div className="flex justify-center">
          <LLMInput
            inputRef={inputRef}
            inputValue={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onSend={handleSend}
            loading={loading}
            className="mt-4"
          />
        </div>
      </div>
    </div>
  );
};

//================ MAIN COMPONENT ================//
const PlaygroundPage = () => (
  <PlaygroundProvider>
    <PlaygroundContent />
  </PlaygroundProvider>
);

//================ EXPORTS ================//
export default PlaygroundPage;
