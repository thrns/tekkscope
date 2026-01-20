'use client';

//================ IMPORTS ================//
import { createContext, useContext, useState, useRef, useEffect, useMemo } from 'react';
import { useApiKeys } from '@/app/contexts/ApiKeysContext';

//================ CONTEXT CREATION ================//
const PlaygroundContext = createContext();

//================ CUSTOM HOOK ================//
export const usePlayground = () => {
  const context = useContext(PlaygroundContext);
  if (!context) {
    throw new Error('usePlayground must be used within a PlaygroundProvider');
  }
  return context;
};

//================ CONSTANTS ================//
const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_DOMAIN || 'http://localhost:8000';

//================ PROVIDER COMPONENT ================//
export const PlaygroundProvider = ({ children }) => {
  //================ STATE & HOOKS ================//
  const { apiKeys } = useApiKeys();
  const [selectedApiKey, setSelectedApiKey] = useState('');
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [progressEvents, setProgressEvents] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('closed'); // open | closed | error
  const [mode, setMode] = useState('lens');
  const [enhancedSearch, setEnhancedSearch] = useState(false);
  const [viewMode, setViewMode] = useState('stream'); // 'stream' | 'structured'
  const inputRef = useRef(null);
  const scrollRef = useRef(null);
  const eventSourceRef = useRef(null);
  const pendingCitationsRef = useRef(null);

  //================ HELPERS ================//
  const appendChunk = (prev, chunk) => {
    const p = typeof prev === 'string' ? prev : '';
    const c = typeof chunk === 'string' ? chunk : '';
    if (!c) return p;
    const max = Math.min(p.length, c.length);
    for (let i = max; i > 0; i--) {
      if (p.endsWith(c.slice(0, i))) {
        return p + c.slice(i);
      }
    }
    return p + c;
  };

  const pushEvent = (payload) => {
    const ts = Date.now();
    const content = typeof payload === 'object' ? payload : { message: String(payload) };
    setProgressEvents((prev) => [...prev, { ts, ...content }]);
  };

  //================ EFFECTS ================//
  useEffect(() => {
    if (apiKeys && apiKeys.length > 0 && !selectedApiKey) {
      setSelectedApiKey(apiKeys[0].api_key);
    }
  }, [apiKeys, selectedApiKey]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  //================ HANDLERS ================//
  const connectStream = (url) => {
    let retries = 0;
    const maxRetries = 3;
    const open = () => new EventSource(url.toString());
    const attach = (es) => {
      eventSourceRef.current = es;
      setConnectionStatus('open');
      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const end = data === '[END_OF_STREAM]' || data?.content === '[END_OF_STREAM]';
          if (end) {
            setLoading(false);
            // Don't clear thinking immediately - let it fade out naturally
            setTimeout(() => setThinking(false), 1000);
            setConnectionStatus('closed');
            es.close();
            return;
          }
          if (data.type === 'thinking') {
            const c = data.content || {};
            // Always set thinking when we receive a thinking event in stream mode
            // This ensures the thinking bubble appears and updates
            setThinking(c && Object.keys(c).length > 0 ? c : { phase: 'thinking', message: 'Processing...' });
            pushEvent({ phase: c.phase, stage: c.stage, message: c.message, url: c.url, narrative: c.narrative, progress: c.progress, links_preview: c.links_preview });
          } else if (data.type === 'executive_summary') {
            // Handle executive summary as a distinct message part or meta update
            setMessages((prev) => {
              const newMessages = [...prev];
              const last = newMessages[newMessages.length - 1];
              if (last && last.role === 'assistant') {
                // Append or set executive summary
                last.meta = { ...(last.meta || {}), executive_summary: data.content };
              } else {
                newMessages.push({
                  role: 'assistant',
                  content: '',
                  meta: { executive_summary: data.content }
                });
              }
              return newMessages;
            });
          } else if (data.type === 'response') {
            setMessages((prev) => {
              const newMessages = [...prev];
              const last = newMessages[newMessages.length - 1];
              if (last && last.role === 'assistant') {
                // Handle citations
                if (data && data.content && typeof data.content === 'object' && Array.isArray(data.content.citations)) {
                  last.meta = { ...(last.meta || {}), citations: data.content.citations, viewMode: 'stream' };
                }
                // Handle download links
                else if (data && data.content && typeof data.content === 'object' && data.content.download) {
                  last.meta = { ...(last.meta || {}), download: data.content.download, viewMode: 'stream' };
                } else {
                  let piece = '';
                  if (typeof data.content === 'string') {
                    piece = data.content;
                  } else if (data.content && typeof data.content === 'object') {
                    if (typeof data.content.text === 'string') piece = data.content.text;
                    else if (typeof data.content.content === 'string') piece = data.content.content;
                  }
                  if (typeof data.content !== 'string') {
                    try { console.debug('[connectStream] non-string content', data.content); } catch { }
                  }
                  if (typeof last.content === 'string') {
                    last.content = appendChunk(last.content, piece);
                    // Attach buffered citations to this text bubble
                    if (Array.isArray(pendingCitationsRef.current)) {
                      last.meta = { ...(last.meta || {}), citations: pendingCitationsRef.current };
                      pendingCitationsRef.current = null;
                    }
                  } else {
                    const meta = Array.isArray(pendingCitationsRef.current) ? { citations: pendingCitationsRef.current } : undefined;
                    newMessages.push({ role: 'assistant', content: piece, ...(meta ? { meta } : {}) });
                    pendingCitationsRef.current = null;
                  }
                }
              } else {
                if (data && data.content && typeof data.content === 'object' && Array.isArray(data.content.citations)) {
                  pendingCitationsRef.current = data.content.citations;
                }
                let piece = '';
                if (typeof data.content === 'string') {
                  piece = data.content;
                } else if (data.content && typeof data.content === 'object') {
                  if (typeof data.content.text === 'string') piece = data.content.text;
                  else if (typeof data.content.content === 'string') piece = data.content.content;
                }
                if (typeof data.content !== 'string') {
                  try { console.debug('[connectStream] non-string content', data.content); } catch { }
                }
                const meta = Array.isArray(pendingCitationsRef.current) ? { citations: pendingCitationsRef.current } : undefined;
                newMessages.push({ role: 'assistant', content: piece, ...(meta ? { meta } : {}) });
                pendingCitationsRef.current = null;
              }
              return newMessages;
            });
          } else if (data.type === 'error') {
            pushEvent({ phase: 'error', message: data.content });
            setConnectionStatus('error');
          }
        } catch (e) {
          pushEvent({ phase: 'parse_error', message: String(e) });
        }
      };
      es.onerror = () => {
        setConnectionStatus('error');
        pushEvent({ phase: 'connection_error', message: 'Stream connection error' });
        try { es.close(); } catch { }
        if (retries < maxRetries) {
          retries += 1;
          const delays = [1500, 3000, 5000];
          const delay = delays[Math.min(retries - 1, delays.length - 1)];
          setTimeout(() => {
            const next = open();
            attach(next);
          }, delay);
        }
      };
      return es;
    };
    const es = open();
    return attach(es);
  };

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    if (!selectedApiKey) {
      setMessages((prev) => [
        ...prev,
        { role: 'user', content: inputValue },
        { role: 'assistant', content: 'Please select or generate an API Key to start.' },
      ]);
      setInputValue('');
      return;
    }

    const userMessage = { role: 'user', content: inputValue };
    setMessages((prev) => [
      ...prev,
      userMessage,
    ]);
    // Don't clear thinking immediately - let it show when streaming starts
    setProgressEvents([]);

    const currentInput = inputValue;
    setInputValue('');
    setLoading(true);
    // Set initial thinking state for stream mode
    if (viewMode === 'stream') {
      setThinking({ phase: 'initializing', message: 'Starting...' });
    }

    try {
      switch (mode) {
        case 'search_links': {
          // search_links is always POST, no stream endpoint
          const body = {
            query: currentInput,
            num_results: 8,
            n_queries: 3,
            enhanced_search: enhancedSearch,
          };
          const res = await fetch(`${BASE_URL}/search/links`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(selectedApiKey ? { Authorization: `Bearer ${selectedApiKey}` } : {}),
            },
            body: JSON.stringify(body),
          });

          if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
          }
          const data = await res.json();
          const payload = Array.isArray(data?.results) ? data.results : data;
          const content = viewMode === 'structured' ? data : (Array.isArray(payload) ? { results: payload } : payload);
          setMessages((prevMessages) => {
            const newMessages = [...prevMessages];
            const lastMessage = newMessages[newMessages.length - 1];
            if (!lastMessage || lastMessage.role !== 'assistant') {
              newMessages.push({ role: 'assistant', content, meta: { mode: 'search_links', viewMode } });
            } else {
              lastMessage.content = content;
              lastMessage.meta = { ...(lastMessage.meta || {}), mode: 'search_links', viewMode };
            }
            return newMessages;
          });
          break;
        }
        case 'search_content': {
          // search_content only has stream endpoint, so we'll use that for both modes
          // but mark the response appropriately
          const url = new URL(`${BASE_URL}/search/content`);
          url.searchParams.append('query', currentInput);
          url.searchParams.append('num_results', 8);
          url.searchParams.append('n_queries', 3);
          url.searchParams.append('enhanced_search', enhancedSearch);
          if (selectedApiKey) {
            url.searchParams.append('token', selectedApiKey);
          }
          const eventSource = new EventSource(url.toString());
          eventSourceRef.current = eventSource;
          eventSource.onmessage = (event) => {
            console.log(event.data);
            const data = JSON.parse(event.data);
            if (data === '[END_OF_STREAM]' || data?.content === '[END_OF_STREAM]') {
              setLoading(false);
              setThinking(false);
              eventSource.close();
              return;
            }
            if (data.type === 'thinking') {
              setThinking(data.content);
            } else if (data.type === 'response') {
              setMessages((prev) => {
                const newMessages = [...prev];
                const lastMessage = newMessages[newMessages.length - 1];
                const payload = data?.content;
                if (!lastMessage || lastMessage.role !== 'assistant') {
                  if (payload && typeof payload === 'object') {
                    newMessages.push({ role: 'assistant', content: Array.isArray(payload) ? { results: payload } : payload });
                  } else if (typeof payload === 'string') {
                    newMessages.push({ role: 'assistant', content: payload });
                  }
                } else {
                  if (payload && typeof payload === 'object') {
                    lastMessage.content = Array.isArray(payload) ? { results: payload } : payload;
                  } else if (typeof payload === 'string') {
                    if (typeof lastMessage.content === 'string') {
                      lastMessage.content = appendChunk(lastMessage.content, payload);
                    } else {
                      newMessages.push({ role: 'assistant', content: payload });
                    }
                  }
                }
                return newMessages;
              });
            } else if (data.type === 'error') {
              setMessages((prev) => {
                const newMessages = [...prev];
                // Add error message as a new assistant message
                newMessages.push({
                  role: 'assistant',
                  content: data.content || 'An error occurred',
                  meta: { error: true }
                });
                return newMessages;
              });
              setLoading(false);
              setThinking(false);
              eventSource.close();
            }
          };
          eventSource.onerror = () => {
            setLoading(false);
            setThinking(false);
            eventSource.close();
          };
          break;
        }

        case 'tek': {
          if (viewMode === 'structured') {
            // Structured mode: Use POST endpoint
            const res = await fetch(`${BASE_URL}/tek/chat-completion`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                ...(selectedApiKey ? { Authorization: `Bearer ${selectedApiKey}` } : {}),
              },
              body: JSON.stringify({ query: currentInput }),
            });

            if (!res.ok) {
              throw new Error(`HTTP error! status: ${res.status}`);
            }
            const data = await res.json();
            setMessages((prevMessages) => {
              const newMessages = [...prevMessages];
              const lastMessage = newMessages[newMessages.length - 1];
              if (!lastMessage || lastMessage.role !== 'assistant') {
                newMessages.push({ role: 'assistant', content: data, meta: { mode: 'tek', viewMode } });
              } else {
                lastMessage.content = data;
                lastMessage.meta = { ...(lastMessage.meta || {}), mode: 'tek', viewMode };
              }
              return newMessages;
            });
            setLoading(false);
            break;
          }
          // Stream mode: Use existing stream endpoint
          const url = new URL(`${BASE_URL}/tek/chat-completion/stream`);
          url.searchParams.append('query', currentInput);
          if (selectedApiKey) {
            url.searchParams.append('token', selectedApiKey);
          }
          let retries = 0;
          const maxRetries = 3;
          const open = () => new EventSource(url.toString());
          const attach = (eventSource) => {
            eventSourceRef.current = eventSource;
            eventSource.onmessage = (event) => {
              console.log(event.data);
              const data = JSON.parse(event.data);
              if (data === '[END_OF_STREAM]' || data?.content === '[END_OF_STREAM]') {
                setLoading(false);
                setThinking(false);
                eventSource.close();
                return;
              }
              if (data.type === 'thinking') {
                setThinking(data.content);
              } else if (data.type === 'response') {
                setMessages((prev) => {
                  const newMessages = [...prev];
                  const lastMessage = newMessages[newMessages.length - 1];
                  if (data && data.content && typeof data.content === 'object' && Array.isArray(data.content.citations)) {
                    if (lastMessage && lastMessage.role === 'assistant' && typeof lastMessage.content === 'string') {
                      lastMessage.meta = { ...(lastMessage.meta || {}), citations: data.content.citations };
                    } else {
                      pendingCitationsRef.current = data.content.citations;
                    }
                  }
                  if (data && data.content && typeof data.content === 'object' && Array.isArray(data.content.results)) {
                    // Stream structured search results as their own bubble
                    const payload = { results: data.content.results };
                    if (!lastMessage || lastMessage.role !== 'assistant' || (lastMessage && typeof lastMessage.content !== 'object')) {
                      newMessages.push({ role: 'assistant', content: payload });
                    } else {
                      lastMessage.content = payload;
                    }
                    return newMessages;
                  }
                  if (!lastMessage || lastMessage.role !== 'assistant') {
                    const piece = data.content;
                    let str = '';
                    if (typeof piece === 'string') str = piece;
                    else if (piece && typeof piece === 'object') {
                      if (typeof piece.text === 'string') str = piece.text;
                      else if (typeof piece.content === 'string') str = piece.content;
                    }
                    if (typeof data.content !== 'string') {
                      try { console.debug('[tek_pro] non-string content', data.content); } catch { }
                    }
                    const meta = Array.isArray(pendingCitationsRef.current) ? { citations: pendingCitationsRef.current } : undefined;
                    newMessages.push({ role: 'assistant', content: str, ...(meta ? { meta } : {}) });
                    pendingCitationsRef.current = null;
                  } else {
                    const piece = data.content;
                    let str = '';
                    if (typeof piece === 'string') str = piece;
                    else if (piece && typeof piece === 'object') {
                      if (typeof piece.text === 'string') str = piece.text;
                      else if (typeof piece.content === 'string') str = piece.content;
                    }
                    if (typeof data.content !== 'string') {
                      try { console.debug('[tek_pro] non-string content', data.content); } catch { }
                    }
                    if (typeof lastMessage.content === 'string') {
                      lastMessage.content = appendChunk(lastMessage.content, str);
                      if (Array.isArray(pendingCitationsRef.current)) {
                        lastMessage.meta = { ...(lastMessage.meta || {}), citations: pendingCitationsRef.current };
                        pendingCitationsRef.current = null;
                      }
                    } else {
                      const meta = Array.isArray(pendingCitationsRef.current) ? { citations: pendingCitationsRef.current } : undefined;
                      newMessages.push({ role: 'assistant', content: str, ...(meta ? { meta } : {}) });
                      pendingCitationsRef.current = null;
                    }
                  }
                  return newMessages;
                });
              }
            };
            eventSource.onerror = () => {
              try { eventSource.close(); } catch { }
              if (retries < maxRetries) {
                retries += 1;
                const delays = [1500, 3000, 5000];
                const delay = delays[Math.min(retries - 1, delays.length - 1)];
                setTimeout(() => {
                  attach(open());
                }, delay);
              }
            };
          };
          attach(open());
          break;
        }

        case 'lens': {
          if (viewMode === 'structured') {
            // Structured mode: Use POST endpoint
            const res = await fetch(`${BASE_URL}/lens/research`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                ...(selectedApiKey ? { Authorization: `Bearer ${selectedApiKey}` } : {}),
              },
              body: JSON.stringify({ query: currentInput }),
            });

            if (!res.ok) {
              throw new Error(`HTTP error! status: ${res.status}`);
            }
            const data = await res.json();
            setMessages((prevMessages) => {
              const newMessages = [...prevMessages];
              const lastMessage = newMessages[newMessages.length - 1];
              if (!lastMessage || lastMessage.role !== 'assistant') {
                newMessages.push({ role: 'assistant', content: data, meta: { mode: 'lens', viewMode } });
              } else {
                lastMessage.content = data;
                lastMessage.meta = { ...(lastMessage.meta || {}), mode: 'lens', viewMode };
              }
              return newMessages;
            });
            setLoading(false);
            break;
          }
          // Stream mode: Use existing stream endpoint
          const url = new URL(`${BASE_URL}/lens/research/stream`);
          url.searchParams.append('query', currentInput);
          if (selectedApiKey) url.searchParams.append('token', selectedApiKey);
          connectStream(url);
          break;
        }

        case 'deeplens': {
          if (viewMode === 'structured') {
            // Structured mode: Use POST endpoint
            const res = await fetch(`${BASE_URL}/deeplens/research`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                ...(selectedApiKey ? { Authorization: `Bearer ${selectedApiKey}` } : {}),
              },
              body: JSON.stringify({ query: currentInput }),
            });

            if (!res.ok) {
              throw new Error(`HTTP error! status: ${res.status}`);
            }
            const data = await res.json();
            setMessages((prevMessages) => {
              const newMessages = [...prevMessages];
              const lastMessage = newMessages[newMessages.length - 1];
              if (!lastMessage || lastMessage.role !== 'assistant') {
                newMessages.push({ role: 'assistant', content: data, meta: { mode: 'deeplens', viewMode } });
              } else {
                lastMessage.content = data;
                lastMessage.meta = { ...(lastMessage.meta || {}), mode: 'deeplens', viewMode };
              }
              return newMessages;
            });
            setLoading(false);
            break;
          }
          // Stream mode: Use existing stream endpoint
          const url = new URL(`${BASE_URL}/deeplens/research/stream`);
          url.searchParams.append('query', currentInput);
          if (selectedApiKey) url.searchParams.append('token', selectedApiKey);
          connectStream(url);
          break;
        }

        case 'reportlens': {
          if (viewMode === 'structured') {
            // Structured mode: Use POST endpoint
            const res = await fetch(`${BASE_URL}/reportlens/research`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                ...(selectedApiKey ? { Authorization: `Bearer ${selectedApiKey}` } : {}),
              },
              body: JSON.stringify({ query: currentInput, file_format: 'pdf' }),
            });

            if (!res.ok) {
              throw new Error(`HTTP error! status: ${res.status}`);
            }
            const data = await res.json();
            setMessages((prevMessages) => {
              const newMessages = [...prevMessages];
              const lastMessage = newMessages[newMessages.length - 1];
              if (!lastMessage || lastMessage.role !== 'assistant') {
                newMessages.push({ role: 'assistant', content: data, meta: { mode: 'reportlens', viewMode } });
              } else {
                lastMessage.content = data;
                lastMessage.meta = { ...(lastMessage.meta || {}), mode: 'reportlens', viewMode };
              }
              return newMessages;
            });
            setLoading(false);
            break;
          }
          // Stream mode: Use existing stream endpoint
          const url = new URL(`${BASE_URL}/reportlens/research/stream`);
          url.searchParams.append('query', currentInput);
          url.searchParams.append('file_format', 'pdf'); // Default to PDF format, supports: pdf, docx, md
          if (selectedApiKey) url.searchParams.append('token', selectedApiKey);
          connectStream(url);
          break;
        }

        case 'nlts': {
          // NLTS is always structured output
          const res = await fetch(`${BASE_URL}/nlts/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(selectedApiKey ? { Authorization: `Bearer ${selectedApiKey}` } : {}),
            },
            body: JSON.stringify({ query: currentInput }),
          });

          if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
          }
          const data = await res.json();
          setMessages((prevMessages) => {
            const newMessages = [...prevMessages];
            const lastMessage = newMessages[newMessages.length - 1];
            // We want to show the structured output
            const content = data.structured_output;
            if (!lastMessage || lastMessage.role !== 'assistant') {
              newMessages.push({ role: 'assistant', content, meta: { mode: 'nlts', viewMode: 'structured', ...data } });
            } else {
              lastMessage.content = content;
              lastMessage.meta = { ...(lastMessage.meta || {}), mode: 'nlts', viewMode: 'structured', ...data };
            }
            return newMessages;
          });
          setLoading(false);
          break;
        }

        default: {
          setMessages((prevMessages) => {
            const newMessages = [...prevMessages];
            const lastMessage = newMessages[newMessages.length - 1];
            if (lastMessage && lastMessage.role === 'assistant') {
              lastMessage.content = 'Unsupported mode';
            }
            return newMessages;
          });
          break;
        }
      }
    } catch (e) {
      const errorMessage = `Error: ${e.message}`;
      setMessages((prev) => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage && lastMessage.role === 'assistant') {
          lastMessage.content = errorMessage;
        }
        return newMessages;
      });
    } finally {
      const streamingModes = ['lens', 'deeplens', 'reportlens', 'tek', 'search_content'];
      if (!streamingModes.includes(mode)) {
        setLoading(false);
      }
    }
  };

  //================ MEMOIZED VALUES ================//
  const thinkingFeed = useMemo(() => {
    const isSensitive = (msg) => {
      const s = String(msg || '').toLowerCase();
      return (
        s.includes('advancedsearchsystem') ||
        s.includes('strategy') ||
        s.includes('registry') ||
        s.includes('llm_config') ||
        s.includes('thread')
      );
    };
    const mapPhase = (p) => {
      switch (p) {
        case 'setup': return 'preparing';
        case 'calling_quick_summary':
        case 'calling_detailed_research':
        case 'calling_deep_research':
        case 'calling_generate_report':
        case 'calling_research':
          return 'preparing';
        case 'init': return 'initializing';
        case 'question_generation': return 'planning';
        case 'parallel_search':
        case 'search':
        case 'search_complete': return 'search';
        case 'analysis':
        case 'analysis_complete': return 'analysis';
        case 'final_filtering':
        case 'filtering_complete': return 'filtering';
        case 'synthesis': return 'compiling';
        case 'generating_file': return 'generating';
        case 'uploading': return 'uploading';
        case 'finalizing': return 'finalizing';
        default: return p || 'progress';
      }
    };
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
    return progressEvents.slice(-100).map((e) => {
      const phaseRaw = e.phase || e.stage || 'progress';
      const phase = mapPhase(phaseRaw);
      let message = e.message || e.narrative || e.token || '';
      if (/^calling_/.test(phaseRaw)) {
        message = '';
      }
      if (phaseRaw === 'llm_token') {
        const preview = e.current_text ? String(e.current_text).slice(-120) : String(e.token || '').slice(0, 120);
        message = preview;
      }
      if (phaseRaw === 'setup') {
        // avoid model/provider names
        message = phase === 'preparing' ? 'Preparing model' : 'Setting up';
        try {
          message = String(message).replace(/model:\s*[^\s]+/ig, 'model');
        } catch { }
      }
      if (isSensitive(message)) return null;
      const rawUrl = e.url || (Array.isArray(e.links_preview) && e.links_preview[0]?.url);
      const [host, href] = getHostHref(rawUrl);
      return { ts: e.ts, phase, message, host, href };
    }).filter(Boolean);
  }, [progressEvents]);

  const value = {
    apiKeys,
    selectedApiKey,
    setSelectedApiKey,
    messages,
    setMessages,
    inputValue,
    setInputValue,
    loading,
    setLoading,
    thinking,
    mode,
    setMode,
    enhancedSearch,
    setEnhancedSearch,
    viewMode,
    setViewMode,
    inputRef,
    scrollRef,
    handleSend,
    progressEvents,
    connectionStatus,
    thinkingFeed,
  };

  //================ RENDER ================//
  return (
    <PlaygroundContext.Provider value={value}>
      {children}
    </PlaygroundContext.Provider>
  );
};
