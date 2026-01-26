import { visit } from 'unist-util-visit';
import type { Root, Parent } from 'mdast';
import he from 'he';

/**
 * A comprehensive remark plugin that sanitizes and corrects common AI-generated markdown errors.
 * This version uses a simplified and more robust method of enforcing spacing around math
 * delimiters to prevent parsing errors.
 */
export function remarkComprehensiveFix() {
  const preprocessor = (markdown: string): string => {
    if (typeof markdown !== 'string') return markdown;

    let cleanedText = markdown;

    // --- STAGE 1: GLOBAL WHITESPACE NORMALIZATION ---
    cleanedText = cleanedText.replace(/\r\n?/g, '\n');
    // THE FIX IS HERE: This next line replaces non-breaking spaces (` `) with regular spaces.
    cleanedText = cleanedText.replace(/\u00A0/g, ' ');
    cleanedText = cleanedText.trim();

    // --- STAGE 2: ENFORCE SPACING AROUND DELIMITERS (THE ROBUST FIX) ---

    // Fix 1: Add space before $$ if not preceded by a space
    cleanedText = cleanedText.replace(/(?<!\s)\$\$/g, ' $$$$'); // Correct

    // Fix 2: Add space after $$ if followed by a non-space
    cleanedText = cleanedText.replace(/\$\$(?=\S)/g, '$$$$ '); // Correct

    // Fix 3: Ensure paragraph break after $$ block
    cleanedText = cleanedText.replace(/\$\$(\n)(?=[a-zA-Z0-9#*•-])/g, '$$$$\n\n'); // Correct

    // Fix 4: Enforce line breaks before/after display math
    cleanedText = cleanedText
    .replace(/(?<!\n)\$\$/g, '\n$$$$')           // Correct
    .replace(/\$\$(?!\n)/g, '$$$$\n')           // Correct
    .replace(/\$\$(\n)(?=\S)/g, '$$$$\n\n')     // Correct (though regex is same as Fix 3)
    .replace(/(?<=\S)(\n)\$\$/g, '\n\n$$$$');   // Correct



    // --- STAGE 3: PROTECT MATH EXPRESSIONS AND TABLES ---

    const protectedBlocks: string[] = [];
    const protectedPlaceholders: string[] = [];

    // Protect tables first (markdown tables with | delimiters)
    const tableRegex = /(?:^|\n)((?:\|[^\n]*\|(?:\n|$))+)/g;
    cleanedText = cleanedText.replace(tableRegex, (match) => {
      const placeholder = `__TABLE_BLOCK_${protectedBlocks.length}__`;
      protectedBlocks.push(match);
      protectedPlaceholders.push(placeholder);
      return placeholder;
    });

    // Protect display math
    cleanedText = cleanedText.replace(/\$\$([\s\S]*?)\$\$/g, (match) => {
      const placeholder = `__MATH_BLOCK_${protectedBlocks.length}__`;
      protectedBlocks.push(match);
      protectedPlaceholders.push(placeholder);
      return placeholder;
    });

    // Protect inline math. The negative lookahead (?!\$) is crucial to avoid
    // matching a `$` that is part of a `$$`.
    cleanedText = cleanedText.replace(/\$([^$]+?)\$(?!\$)/g, (match, content) => {
      if (content.trim() === '') return match;
      if (content.includes('$$') || (content.match(/\n/g) || []).length > 2) {
        return match;
      }
      if (/[\\{}^_=+\-*/()[\]|<>]/.test(content) || /\\[a-zA-Z]/.test(content)) {
        const placeholder = `__MATH_INLINE_${protectedBlocks.length}__`;
        protectedBlocks.push(match);
        protectedPlaceholders.push(placeholder);
        return placeholder;
      }
      return match;
    });

    // --- STAGE 4: FIX LISTS AND HEADINGS ---
    // These fixes can now run safely after all math is protected.

    cleanedText = cleanedText.replace(/^(\s*)([*•-]|\d+\.)\s+/gm, (match, indent, bullet) => {
      return `${indent}${bullet} `;
    });

    cleanedText = cleanedText.replace(/^(#+)([^\s#])/gm, (match, hashes, char) => {
      return `${hashes} ${char}`;
    });
    
    cleanedText = cleanedText.split('\n').map(line => {
      if (protectedPlaceholders.some(p => line.includes(p))) return line;
      return line.trimEnd();
    }).join('\n');

    // --- STAGE 5: RESTORE PROTECTED BLOCKS (TABLES AND MATH) ---
    
    protectedPlaceholders.forEach((placeholder, index) => {
        cleanedText = cleanedText.replace(placeholder, () => protectedBlocks[index]);
    });

    // Clean up any potential double spaces created by the spacing enforcement.
    cleanedText = cleanedText.replace(/  +/g, ' ');

    return cleanedText;
  };

  return preprocessor;
}

/**
 * A secondary plugin to clean the text content within the parsed tree.
 * It decodes HTML entities from non-math text nodes.
 */
export function remarkCleanTextNodes() {
    return (tree: Root) => {
      visit(tree, 'text', (node, _index, parent: Parent | undefined) => {
        if (parent && (parent.type === 'math' || parent.type === 'inlineMath')) {
          return; 
        }
        node.value = he.decode(node.value);
      });
    };
  }

export { remarkCleanTextNodes as remarkCleanText };