'use client';
//================ IMPORTS ================//
import React from 'react';

//================ COMPONENT ================//
const ProgressPanel = ({ events = [], status }) => {
  //================ RENDER ================//
  return (
    <div className="w-full max-w-5xl mx-auto mt-2">
      <div className="rounded-2xl bg-tekk-dark/70 border border-white/10 p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="text-sm font-medium text-white/80">Live Progress</div>
          <div className="text-xs text-white/60">
            {status === 'open' && <span className="animate-pulse">Streaming…</span>}
            {status === 'error' && <span className="text-red-400">Connection error</span>}
            {status === 'closed' && <span>Idle</span>}
          </div>
        </div>
        <div className="max-h-56 overflow-y-auto space-y-2">
          {events.length === 0 ? (
            <div className="text-xs text-white/50">No events yet</div>
          ) : (
            events.slice(-50).map((e, idx) => {
              const phase = e.phase || e.stage || 'progress';
              const message = e.message || e.narrative || e.token || '';
              const rawUrl = e.url || (Array.isArray(e.links_preview) && e.links_preview[0]?.url);
              const getHostHref = (u) => {
                try {
                  if (!u || typeof u !== 'string') return [null, null];
                  const normalized = /^https?:\/\//i.test(u) ? u : `https://${u}`;
                  const parsed = new URL(normalized);
                  return [parsed.hostname, normalized];
                } catch {
                  return [null, null];
                }
              };
              const [host, href] = getHostHref(rawUrl);
              const time = e.ts ? new Date(e.ts).toLocaleTimeString() : '';
              return (
                <div key={idx} className="text-xs text-white/80">
                  <span className="text-white/60 mr-2">{time}</span>
                  <span className="font-semibold mr-2">{phase}</span>
                  <span className="mr-2">{String(message).slice(0, 160)}</span>
                  {host && href && (
                    <a href={href} target="_blank" rel="noreferrer" className="text-tekk-primary underline">
                      {host}
                    </a>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

//================ EXPORTS ================//
export default ProgressPanel;