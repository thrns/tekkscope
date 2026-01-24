'use client';
//================ IMPORTS ================//
import React, { useEffect, useState } from 'react';
import MarkdownStream from './MarkdownStream';
import CitationBubble from './CitationBubble';
import { CodeBlock } from '@/components/ui/code-block';

//================ COMPONENT ================//
const MessageBubble = ({ message }) => {
  //================ STATE & HOOKS ================//
  const role = message.role;
  const content = message.content;
  const mode = message.meta?.mode;

  const baseClass = role === 'user'
    ? 'max-w-2xl rounded-2xl bg-tekk-primary px-4 py-2 text-black'
    : 'max-w-2xl rounded-2xl px-4 py-2 text-white/90';

  const [streamDone, setStreamDone] = useState(false);

  //================ EFFECTS ================//
  useEffect(() => {
    setStreamDone(false);
  }, [content]);

  //================ HELPER ================//
  const renderContent = () => {
    // Handle raw mode: display JSON in code editor
    if ((message.meta?.viewMode === 'structured' || mode === 'nlts') && content && typeof content === 'object') {
      try {
        const jsonString = JSON.stringify(content, null, 2);
        return (
          <CodeBlock
            language="json"
            filename="response.json"
            code={jsonString}
          />
        );
      } catch (e) {
        // Fallback if JSON.stringify fails
        return (
          <CodeBlock
            language="text"
            filename="response.txt"
            code={String(content)}
          />
        );
      }
    }

    // Handle download links for reportlens
    if (message.meta?.download) {
      const { download_url, file_format, filename, research_id } = message.meta.download;
      return (
        <div className="space-y-3">
          <div className="text-sm opacity-90">
            ✅ Research report generated successfully!
          </div>
          <a
            href={download_url}
            download={filename}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 bg-tekk-primary text-black rounded-lg hover:bg-tekk-primary/90 transition-colors font-medium"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            Download Report ({file_format.toUpperCase()})
          </a>
          <div className="text-xs opacity-70">
            File: {filename} • Format: {file_format.toUpperCase()}
          </div>
        </div>
      );
    }

    if (mode === 'search_content' && typeof content === 'string') {
      try {
        const parsed = JSON.parse(content);
        const data = Array.isArray(parsed) ? { results: parsed } : parsed;
        if (data && Array.isArray(data.results)) {
          return (
            <div className="space-y-2">
              {data.results.map((r, idx) => (
                <div key={idx} className="text-sm space-y-1 border-b border-white mb-2">
                  {r.title && <div className="font-medium">{r.title}</div>}
                  {r.url && (
                    <a href={r.url} target="_blank" rel="noreferrer" className="text-tekk-primary underline">
                      {r.url}
                    </a>
                  )}
                  {r.content && <div className="opacity-80">{String(r.content).slice(0, 240)}...</div>}
                  {r.metadata && (
                    <div className="text-xs opacity-70">
                      {r.metadata.font && <span>Font: {r.metadata.font}{Array.isArray(r.metadata.colors) && r.metadata.colors.length ? ' • ' : ''}</span>}
                      {Array.isArray(r.metadata.colors) && r.metadata.colors.length > 0 && <span>Colors: {r.metadata.colors.join(', ')}</span>}
                    </div>
                  )}
                  {Array.isArray(r.internal_links) && r.internal_links.length > 0 && (
                    <div className="text-xs opacity-80">
                      <span className="mr-1">Internal links:</span>
                      {r.internal_links.slice(0, 3).map((l, i) => (
                        <a key={i} href={l.url} target="_blank" rel="noreferrer" className="text-tekk-primary underline mr-2">
                          {l.text || l.url}
                        </a>
                      ))}
                      {r.internal_links.length > 3 && <span>+{r.internal_links.length - 3} more</span>}
                    </div>
                  )}
                  {Array.isArray(r.external_links) && r.external_links.length > 0 && (
                    <div className="text-xs opacity-80">
                      <span className="mr-1">External links:</span>
                      {r.external_links.slice(0, 3).map((l, i) => (
                        <a key={i} href={l.url} target="_blank" rel="noreferrer" className="text-tekk-primary underline mr-2">
                          {l.text || l.url}
                        </a>
                      ))}
                      {r.external_links.length > 3 && <span>+{r.external_links.length - 3} more</span>}
                    </div>
                  )}
                </div>
              ))}
            </div>
          );
        }
      } catch { }
      const lines = content.split(/\n+/).map((l) => l.trim()).filter(Boolean);
      const items = [];
      const urlRegex = /https?:\/\/\S+/g;
      for (const line of lines) {
        const urls = line.match(urlRegex);
        if (!urls) continue;
        for (const u of urls) {
          items.push({ title: '', url: u, content: line.replace(u, '').trim() });
        }
      }
      if (items.length > 0) {
        return (
          <div className="space-y-2">
            {items.map((r, idx) => (
              <div key={idx} className="text-sm">
                {r.title && <div className="font-medium">{r.title}</div>}
                {r.url && (
                  <a href={r.url} target="_blank" rel="noreferrer" className="text-tekk-primary underline">
                    {r.url}
                  </a>
                )}
                {r.content && <div className="opacity-80">{String(r.content).slice(0, 240)}...</div>}
              </div>
            ))}
          </div>
        );
      }
    }
    if (mode === 'search_links' && typeof content === 'string') {
      try {
        const parsed = JSON.parse(content);
        const data = Array.isArray(parsed) ? { results: parsed } : parsed;
        if (data && Array.isArray(data.results)) {
          return (
            <div className="space-y-2">
              {data.results.map((r, idx) => (
                <div key={idx} className="text-sm space-y-1">
                  {r.title && <div className="font-medium">{r.title}</div>}
                  {r.url && (
                    <a href={r.url} target="_blank" rel="noreferrer" className="text-tekk-primary underline">
                      {r.url}
                    </a>
                  )}
                  {r.content && <div className="opacity-80">{r.content.slice(0, 240)}...  more ({r.content.length})</div>}
                  {r.metadata && (
                    <div className="text-xs opacity-70">
                      {r.metadata.font && <span>Font: {r.metadata.font}{Array.isArray(r.metadata.colors) && r.metadata.colors.length ? ' • ' : ''}</span>}
                      {Array.isArray(r.metadata.colors) && r.metadata.colors.length > 0 && <span>Colors: {r.metadata.colors.join(', ')}</span>}
                    </div>
                  )}
                  {Array.isArray(r.internal_links) && r.internal_links.length > 0 && (
                    <div className="text-xs opacity-80">
                      <span className="mr-1">Internal links:</span>
                      {r.internal_links.slice(0, 3).map((l, i) => (
                        <a key={i} href={l.url} target="_blank" rel="noreferrer" className="text-tekk-primary underline mr-2">
                          {l.text || l.url}
                        </a>
                      ))}
                      {r.internal_links.length > 3 && <span>+{r.internal_links.length - 3} more</span>}
                    </div>
                  )}
                  {Array.isArray(r.external_links) && r.external_links.length > 0 && (
                    <div className="text-xs opacity-80">
                      <span className="mr-1">External links:</span>
                      {r.external_links.slice(0, 3).map((l, i) => (
                        <a key={i} href={l.url} target="_blank" rel="noreferrer" className="text-tekk-primary underline mr-2">
                          {l.text || l.url}
                        </a>
                      ))}
                      {r.external_links.length > 3 && <span>+{r.external_links.length - 3} more</span>}
                    </div>
                  )}
                </div>
              ))}
            </div>
          );
        }
      } catch { }
    }
    if (Array.isArray(content)) {
      return (
        <div className="space-y-2">
          {content.map((r, idx) => (
            <div key={idx} className="text-sm space-y-1">
              {r.title && <div className="font-medium">{r.title}</div>}
              {r.url && (
                <a href={r.url} target="_blank" rel="noreferrer" className="text-tekk-primary underline">
                  {r.url}
                </a>
              )}
              {r.content && <div className="opacity-80">{String(r.content).slice(0, 240)}...</div>}
              {r.metadata && (
                <div className="text-xs opacity-70">
                  {r.metadata.font && <span>Font: {r.metadata.font}{Array.isArray(r.metadata.colors) && r.metadata.colors.length ? ' • ' : ''}</span>}
                  {Array.isArray(r.metadata.colors) && r.metadata.colors.length > 0 && <span>Colors: {r.metadata.colors.join(', ')}</span>}
                </div>
              )}
              {Array.isArray(r.internal_links) && r.internal_links.length > 0 && (
                <div className="text-xs opacity-80">
                  <span className="mr-1">Internal links:</span>
                  {r.internal_links.slice(0, 3).map((l, i) => (
                    <a key={i} href={l.url} target="_blank" rel="noreferrer" className="text-tekk-primary underline mr-2">
                      {l.text || l.url}
                    </a>
                  ))}
                  {r.internal_links.length > 3 && <span>+{r.internal_links.length - 3} more</span>}
                </div>
              )}
              {Array.isArray(r.external_links) && r.external_links.length > 0 && (
                <div className="text-xs opacity-80">
                  <span className="mr-1">External links:</span>
                  {r.external_links.slice(0, 3).map((l, i) => (
                    <a key={i} href={l.url} target="_blank" rel="noreferrer" className="text-tekk-primary underline mr-2">
                      {l.text || l.url}
                    </a>
                  ))}
                  {r.external_links.length > 3 && <span>+{r.external_links.length - 3} more</span>}
                </div>
              )}
            </div>
          ))}
        </div>
      );
    }
    if (typeof content === 'string') {
      return (
        <>
          <MarkdownStream content={content} onComplete={() => setStreamDone(true)} />
          {streamDone && Array.isArray(message.meta?.citations) && message.meta.citations.length > 0 && (
            <CitationBubble text={content} citations={message.meta.citations} />
          )}
        </>
      );
    }
    if (content && typeof content === 'object') {
      // Search content and links modes: list of results
      if (Array.isArray(content.results)) {
        console.log('Search results:', content.results);
        return (
          <div className="space-y-2">
            {content.results.map((r, idx) => (
              <div key={idx} className="text-sm space-y-1">
                {r.title && <div className="font-medium">{r.title}</div>}
                {r.url && (
                  <a href={r.url} target="_blank" rel="noreferrer" className="text-tekk-bg underline">
                    {r.url}
                  </a>
                )}
                {r.content && <div className="opacity-80">{String(r.content).slice(0, 240)}...</div>}
                {r.metadata && (
                  <div className="text-xs opacity-70">
                    {r.metadata.font && <span>Font: {r.metadata.font}{Array.isArray(r.metadata.colors) && r.metadata.colors.length ? ' • ' : ''}</span>}
                    {Array.isArray(r.metadata.colors) && r.metadata.colors.length > 0 && <span>Colors: {r.metadata.colors.join(', ')}</span>}
                  </div>
                )}
                {Array.isArray(r.internal_links) && r.internal_links.length > 0 && (
                  <div className="text-xs opacity-80">
                    <span className="mr-1">Internal links:</span>
                    {r.internal_links.slice(0, 3).map((l, i) => (
                      <a key={i} href={l.url} target="_blank" rel="noreferrer" className="text-tekk-bg underline mr-2">
                        {l.text || l.url}
                      </a>
                    ))}
                    {r.internal_links.length > 3 && <span>+{r.internal_links.length - 3} more</span>}
                  </div>
                )}
                {Array.isArray(r.external_links) && r.external_links.length > 0 && (
                  <div className="text-xs opacity-80">
                    <span className="mr-1">External links:</span>
                    {r.external_links.slice(0, 3).map((l, i) => (
                      <a key={i} href={l.url} target="_blank" rel="noreferrer" className="text-tekk-bg underline mr-2">
                        {l.text || l.url}
                      </a>
                    ))}
                    {r.external_links.length > 3 && <span>+{r.external_links.length - 3} more</span>}
                  </div>
                )}
              </div>
            ))}
          </div>
        );
      }
      // Fallback: stringify lite
      try {
        const pretty = JSON.stringify(content, null, 2);
        const citations = message.meta?.citations || content.citations;
        return (
          <>
            <pre className="text-xs opacity-80">{pretty}</pre>
            {Array.isArray(citations) && citations.length > 0 && (
              <CitationBubble text={pretty} citations={citations} />
            )}
          </>
        );
      } catch {
        const str = String(content);
        return (
          <>
            <pre className="text-xs opacity-80">{str}</pre>
            {Array.isArray(message.meta?.citations) && message.meta.citations.length > 0 && (
              <CitationBubble text={str} citations={message.meta.citations} />
            )}
          </>
        );
      }
    }
    return null;
  };

  //================ RENDER ================//
  return (
    <div className={`${baseClass} `}>
      {renderContent()}
    </div>
  );
};

//================ EXPORTS ================//
export default MessageBubble;