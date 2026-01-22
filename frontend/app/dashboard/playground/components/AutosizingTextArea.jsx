'use client';
//================ IMPORTS ================//
import React, { useEffect, useRef, forwardRef } from 'react';
import { cn } from '@/lib/utils';

/**
 * AutosizingTextArea
 * - Auto-sizes up to `maxLines` (default: 18)
 * - Press Enter to submit, Shift+Enter for newline
 * - Dark theme-friendly styles, configurable via `className`
 * - Minimal scrollbar by default; full hide with `hideScrollbar`
 */
//================ COMPONENT ================//
const AutosizingTextArea = forwardRef(function AutosizingTextArea(
  {
    value,
    onChange,
    placeholder,
    className,
    maxLines = 18,
    minLines = 1,
    disabled,
    onEnter,
    hideScrollbar = false,
    ...props
  },
  ref
) {
  //================ STATE & HOOKS ================//
  const innerRef = useRef(null);

  //================ EFFECTS ================//
  useEffect(() => {
    const el = innerRef.current;
    if (!el) return;
    el.style.height = 'auto';

    const computed = window.getComputedStyle(el);
    const lineHeight = parseFloat(computed.lineHeight) || 24;
    const paddingTop = parseFloat(computed.paddingTop) || 0;
    const paddingBottom = parseFloat(computed.paddingBottom) || 0;
    const borderTop = parseFloat(computed.borderTopWidth) || 0;
    const borderBottom = parseFloat(computed.borderBottomWidth) || 0;
    const maxHeight = lineHeight * maxLines + paddingTop + paddingBottom + borderTop + borderBottom;

    const nextHeight = Math.min(el.scrollHeight, maxHeight);
    el.style.height = `${nextHeight}px`;
    el.style.overflowY = el.scrollHeight > maxHeight ? 'auto' : 'hidden';
  }, [value, maxLines]);

  //================ HANDLERS ================//
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && onEnter) {
      e.preventDefault();
      onEnter();
    }
  };

  //================ RENDER ================//
  return (
    <>
      <textarea
        ref={(node) => {
          innerRef.current = node;
          if (typeof ref === 'function') ref(node);
          else if (ref && typeof ref === 'object') ref.current = node;
        }}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        rows={minLines}
        className={cn(
          'w-full bg-transparent text-foreground placeholder:text-muted-foreground rounded-2xl p-4 leading-6',
          'focus:outline-none resize-none border-none focus:ring-0',
          'autosize-textarea',
          hideScrollbar && 'autosize-no-scrollbar',
          className
        )}
        {...props}
      />
      <style jsx>{`
        /* Minimal scrollbar styling */
        .autosize-textarea {
          scrollbar-width: thin; /* Firefox */
          scrollbar-color: rgba(0,0,0,0.2) transparent; /* Firefox (light) */
        }
        .autosize-textarea::-webkit-scrollbar {
          width: 4px; /* WebKit */
          height: 4px;
        }
        .autosize-textarea::-webkit-scrollbar-thumb {
          background-color: rgba(0,0,0,0.2); /* Light theme default */
          border-radius: 9999px;
        }
        .autosize-textarea::-webkit-scrollbar-track {
          background: transparent;
        }

        /* Fully hide scrollbar when requested */
        .autosize-no-scrollbar {
          scrollbar-width: none; /* Firefox */
        }
        .autosize-no-scrollbar::-webkit-scrollbar {
          width: 0px; /* WebKit */
          height: 0px;
        }

        /* Dark mode overrides */
        :global(.dark) .autosize-textarea {
          scrollbar-color: rgba(255,255,255,0.15) transparent; /* Firefox (dark) */
        }
        :global(.dark) .autosize-textarea::-webkit-scrollbar-thumb {
          background-color: rgba(255,255,255,0.15); /* WebKit (dark) */
        }
      `}</style>
    </>
  );
});

//================ EXPORTS ================//
export default AutosizingTextArea;