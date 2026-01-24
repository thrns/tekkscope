'use client';
//================ IMPORTS ================//
import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import '../styles/research-markdown.css';
import { remarkComprehensiveFix, remarkCleanTextNodes } from '../utils/remark-sanitize';
import { MarkdownComponents } from './MarkdownComponents';

//================ COMPONENT ================//
const MarkdownStream = ({ content, onComplete }) => {
  //================ STATE & HOOKS ================//
  const [displayed, setDisplayed] = useState('');
  const animatingRef = useRef(false);
  const bufferRef = useRef('');

  //================ EFFECTS ================//
  useEffect(() => {
    const next = typeof content === 'string' ? content : '';
    bufferRef.current = next;
    if (next.length <= displayed.length) {
      setDisplayed(next);
      if (typeof onComplete === 'function') onComplete();
      return;
    }
    if (animatingRef.current) return;
    animatingRef.current = true;
    let i = displayed.length;
    const step = () => {
      const buf = bufferRef.current;
      if (i >= buf.length) {
        animatingRef.current = false;
        if (typeof onComplete === 'function') onComplete();
        return;
      }
      i += 2;
      setDisplayed(buf.slice(0, i));
      requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [content]);

  //================ HELPER ================//
  const preprocessedContent = remarkComprehensiveFix()(displayed);

  //================ RENDER ================//
  return (
    <ReactMarkdown
      remarkPlugins={[
        remarkMath,
        remarkGfm,
        remarkCleanTextNodes
      ]}
      rehypePlugins={[
        rehypeKatex
      ]}
      components={MarkdownComponents}
    >
      {preprocessedContent}
    </ReactMarkdown>
  );
};

//================ EXPORTS ================//
export default MarkdownStream;
