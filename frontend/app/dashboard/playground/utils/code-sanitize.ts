/**
 * Sanitizes markdown text to prevent issues where a code fence (``` or ~~~)
 * is immediately followed by characters common in markdown structural elements
 * (e.g., '#' for headings, '*' for lists) on the same line.
 *
 * This can happen when a user intends to close a code block and start a new
 * markdown element, but accidentally types them on the same line.
 * For example, ` ```#### heading ` would be treated by a GFM parser as an
 * opening code fence with "#### heading" as its info string. This function
 * aims to correct such an input to ` ```\n#### heading `, aligning with the
 * likely user intent.
 *
 * @param markdown The raw markdown string.
 * @returns The sanitized markdown string.
 */
export function separateAmbiguousFences(markdown: string): string {
    if (typeof markdown !== 'string' || !markdown) {
      return markdown;
    }
  
    // Step 1: Fix inline fence beginnings like ```#### heading
    const leadingFenceRegex = /(^|\n)([ \t]{0,3})(```|~~~)([#*+\-•>])([^\n]*)(\n|$)/gm;
    markdown = markdown.replace(
      leadingFenceRegex,
      '$1$2$3\n$2$4$5$6'
    );
  
    // Step 2: Fix trailing fences like `}```` on the same line
    const trailingFenceRegex = /([^\n`]+)```/g;
    markdown = markdown.replace(trailingFenceRegex, (match, code) => {
      if (code.trim().length === 0) return match;
      return code + '\n```';
    });
  
    return markdown;
  }
  
  // Example Usage:
  // const rawMarkdown = "```sql\nSELECT * FROM Customers;\n```#### What this example does:\n\nAnd ```* A list item";
  // const sanitized = separateAmbiguousFences(rawMarkdown);
  // console.log(sanitized);
  // Output:
  // ```sql
  // SELECT * FROM Customers;
  // ```
  // #### What this example does:
  //
  // And ```
  // * A list item
  
  // const rawMarkdown2 = "  ```> A quote";
  // const sanitized2 = separateAmbiguousFences(rawMarkdown2);
  // console.log(sanitized2);
  // Output:
  //   ```
  //   > A quote
  
  // const rawMarkdown3 = "```python\nprint('hello')\n```"; // Should remain unchanged
  // const sanitized3 = separateAmbiguousFences(rawMarkdown3);
  // console.log(sanitized3);
  // Output:
  // ```python
  // print('hello')
  // ```

export function normalizeIndentation(code: string): string {
    const lines = code.split('\n');
  
    // Detect min leading spaces (ignore empty lines)
    const minIndent = lines
      .filter(line => line.trim() !== '')
      .reduce((min, line) => {
        const match = line.match(/^(\s*)/);
        const spaces = match ? match[0].length : 0;
        return min === null ? spaces : Math.min(min, spaces);
      }, null as number | null);
  
    // Strip minIndent from all lines
    if (minIndent !== null && minIndent > 0) {
      return lines.map(line => line.startsWith(' '.repeat(minIndent)) ? line.slice(minIndent) : line).join('\n');
    }
    // 🚨 All lines are flat — try auto-indenting if language is structured (Java/Python)
    const isStructuredCode = code.includes('{') || code.includes('}');
    if (isStructuredCode) {
        let indentLevel = 0;
        return lines
        .map(line => {
            const trimmed = line.trim();
            if (trimmed === '') return '';
            if (trimmed.startsWith('}')) indentLevel = Math.max(0, indentLevel - 1);
            const result = '    '.repeat(indentLevel) + trimmed;
            if (trimmed.endsWith('{')) indentLevel += 1;
            return result;
        })
        .join('\n');
    }

  
    return code;
}
  

export function enforceStructuralNewlines(text: string): string {
    if (typeof text !== 'string' || !text.trim()) return text;
  
    let cleaned = text;
  
    // Ensure code fences are on their own line (start and end)
    cleaned = cleaned.replace(/([^\n])(```|~~~)/g, '$1\n$2'); // Before
    cleaned = cleaned.replace(/(```|~~~)([^\n])/g, '$1\n$2'); // After
  
    // Ensure code fences followed by heading/list/quote go to next line
    cleaned = cleaned.replace(/(```|~~~)([#*+\-•>])/g, '$1\n$2');
  
    // Ensure closing brace followed by token is split to a new line
    cleaned = cleaned.replace(/(\})\s*(?=[A-Za-z#])/g, '$1\n');
  
    // Force `else` or `catch` to a new line after closing brace
    cleaned = cleaned.replace(/\}\s*(else|catch)/g, '}\n$1');
  
    // Fix return stuck in comment or same line
    cleaned = cleaned.replace(/(\/\/[^\n]*)(return|throw)/g, '$1\n$2');
  
    // Make sure lone return or throw starts on new line when stuck to comment
    cleaned = cleaned.replace(/([^\n])\s+(return|throw)\b/g, '$1\n$2');
  
    // Optional: Normalize multiple blank lines to max 2
    cleaned = cleaned.replace(/\n{3,}/g, '\n\n');
  
    return cleaned;
  }
  