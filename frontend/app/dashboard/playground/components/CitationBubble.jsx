'use client';
//================ IMPORTS ================//
import React from 'react';
import { motion } from 'framer-motion';

//================ COMPONENT ================//
const CitationBubble = ({ text, citations = [] }) => {
  //================ STATE & HOOKS ================//
  const markers = Array.from(String(text || '').matchAll(/\[(\d+)\]/g)).map(m => parseInt(m[1], 10));
  const uniqueMarkers = Array.from(new Set(markers)).filter(n => Number.isFinite(n));
  const items = uniqueMarkers.length > 0
    ? uniqueMarkers.map(n => ({ n, src: citations[n - 1] }))
    : citations.slice(0, 5).map((src, idx) => ({ n: idx + 1, src }));

  //================ HELPER ================//
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

  if (!items.length) return null;

  //================ RENDER ================//
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="mt-3 rounded-2xl bg-tekk-primary/10 border border-tekk-primary/30 px-3 py-2"
    >
      <div className="text-xs text-white/70 mb-1">Citations</div>
      <div className="flex flex-wrap gap-2">
        {items.map(({ n, src }, i) => {
          const title = (src && src.title) ? String(src.title).slice(0, 60) : `Source ${n}`;
          const [host, href] = getHostHref(src && src.url);
          return (
            <motion.div
              key={`${n}-${i}`}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 * i, duration: 0.2 }}
              className="text-xs px-2 py-1 rounded-full bg-tekk-primary/20 border border-tekk-primary/40"
            >
              <span className="font-semibold mr-1">[{n}]</span>
              {href ? (
                <a href={href} target="_blank" rel="noreferrer" className="text-tekk-primary underline">
                  {host || title}
                </a>
              ) : (
                <span>{title}</span>
              )}
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
};

//================ EXPORTS ================//
export default CitationBubble;