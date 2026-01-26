'use client';
//================ IMPORTS ================//
import React from 'react';
import { ExternalLink } from 'lucide-react';


//================ CONFIG ================//
export const MarkdownComponents = {
  h1: ({ children, ...props }) => (
    <h1
      className="text-3xl font-bold text-white mt-8 mb-4 pb-2 border-b border-tekk-dark first:mt-0"
      {...props}
    >
      {children}
    </h1>
  ),

  h2: ({ children, ...props }) => (
    <h2
      className="text-2xl font-semibold text-white mt-6 mb-3 pb-2 border-b border-tekk-dark/50"
      {...props}
    >
      {children}
    </h2>
  ),

  h3: ({ children, ...props }) => (
    <h3
      className="text-xl font-semibold text-white mt-5 mb-2"
      {...props}
    >
      {children}
    </h3>
  ),

  h4: ({ children, ...props }) => (
    <h4
      className="text-lg font-medium text-white mt-4 mb-2"
      {...props}
    >
      {children}
    </h4>
  ),

  h5: ({ children, ...props }) => (
    <h5
      className="text-base font-medium text-white mt-3 mb-2"
      {...props}
    >
      {children}
    </h5>
  ),

  h6: ({ children, ...props }) => (
    <h6
      className="text-sm font-medium text-white/90 mt-3 mb-2"
      {...props}
    >
      {children}
    </h6>
  ),

  p: ({ children, ...props }) => (
    <p
      className="text-white/90 leading-relaxed mb-4"
      {...props}
    >
      {children}
    </p>
  ),

  code: ({ node, inline, className, children, ...props }) => {
    const match = /language-(\w+)/.exec(className || '');
    const language = match ? match[1] : '';

    if (!inline && language) {
      const { CodeBlock } = require('@/components/ui/code-block');
      const codeString = String(children).replace(/\n$/, '');

      return (
        <CodeBlock
          language={language}
          filename={`code.${language}`}
          code={codeString}
        />
      );
    }

    if (!inline) {
      const codeString = String(children).replace(/\n$/, '');
      const isJson = codeString.trim().startsWith('{') || codeString.trim().startsWith('[');

      try {
        if (!isJson) throw new Error('not JSON');
        JSON.parse(codeString);
        const { CodeBlock } = require('@/components/ui/code-block');

        return (
          <CodeBlock
            language="json"
            filename="code.json"
            code={codeString}
          />
        );
      } catch (e) {
        return (
          <code
            className="bg-tekk-darkest text-tekk-primary px-1.5 py-0.5 rounded text-sm font-mono block my-2 p-2"
            {...props}
          >
            {children}
          </code>
        );
      }
    }


  },

  ul: ({ children, ...props }) => (
    <ul
      className="list-disc list-outside ml-6 mb-4 space-y-1 text-white/90"
      {...props}
    >
      {children}
    </ul>
  ),

  ol: ({ children, ...props }) => (
    <ol
      className="list-decimal list-outside ml-6 mb-4 space-y-1 text-white/90"
      {...props}
    >
      {children}
    </ol>
  ),

  li: ({ children, ...props }) => (
    <li
      className="leading-relaxed"
      {...props}
    >
      {children}
    </li>
  ),

  blockquote: ({ children, ...props }) => (
    <blockquote
      className="border-l-4 border-tekk-primary bg-tekk-dark/30 pl-4 py-2 my-4 italic text-white/80"
      {...props}
    >
      {children}
    </blockquote>
  ),

  table: ({ children, ...props }) => (
    <div className="my-4 overflow-x-auto">
      <table
        className="min-w-full border border-tekk-dark rounded-lg overflow-hidden"
        {...props}
      >
        {children}
      </table>
    </div>
  ),

  thead: ({ children, ...props }) => (
    <thead
      className="bg-tekk-dark"
      {...props}
    >
      {children}
    </thead>
  ),

  tbody: ({ children, ...props }) => (
    <tbody
      className="divide-y divide-tekk-dark"
      {...props}
    >
      {children}
    </tbody>
  ),

  tr: ({ children, ...props }) => (
    <tr
      className="hover:bg-tekk-dark/30 transition-colors"
      {...props}
    >
      {children}
    </tr>
  ),

  th: ({ children, ...props }) => (
    <th
      className="px-4 py-2 text-left text-sm font-semibold text-white border-r border-tekk-dark last:border-r-0"
      {...props}
    >
      {children}
    </th>
  ),

  td: ({ children, ...props }) => (
    <td
      className="px-4 py-2 text-sm text-white/90 border-r border-tekk-dark last:border-r-0"
      {...props}
    >
      {children}
    </td>
  ),

  a: ({ children, href, ...props }) => {
    const isExternal = href && (href.startsWith('http://') || href.startsWith('https://'));

    return (
      <a
        href={href}
        className="text-tekk-primary hover:text-tekk-primary/80 underline inline-flex items-center gap-1 transition-colors"
        target={isExternal ? '_blank' : undefined}
        rel={isExternal ? 'noopener noreferrer' : undefined}
        {...props}
      >
        {children}
        {isExternal && <ExternalLink size={12} className="inline" />}
      </a>
    );
  },

  hr: ({ ...props }) => (
    <hr
      className="border-t border-tekk-dark my-6"
      {...props}
    />
  ),

  strong: ({ children, ...props }) => (
    <strong
      className="font-semibold text-white"
      {...props}
    >
      {children}
    </strong>
  ),

  em: ({ children, ...props }) => (
    <em
      className="italic text-white/90"
      {...props}
    >
      {children}
    </em>
  ),
};

//================ EXPORTS ================//
export default MarkdownComponents;
