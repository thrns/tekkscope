"""Markdown formatter for research outputs with LaTeX support."""

import re
from typing import Optional


def unescape_latex(text: str) -> str:
    """
    Unescape LaTeX commands that may have been double-escaped.
    
    Converts \\command to \command within math delimiters.
    This fixes issues where LLMs generate escaped LaTeX like \\mathcal instead of \mathcal.
    
    Args:
        text: Markdown text potentially containing double-escaped LaTeX
        
    Returns:
        Text with properly unescaped LaTeX commands
    """
    if not text:
        return text
    
    # Fix double-escaped backslashes in display math ($$...$$)
    def fix_display_math(match):
        content = match.group(1)
        # Replace double backslashes with single backslashes
        # But preserve intentional double backslashes for line breaks (\\)
        content = re.sub(r'\\\\(?![\\])', r'\\', content)
        return f'$${content}$$'
    
    text = re.sub(r'\$\$(.*?)\$\$', fix_display_math, text, flags=re.DOTALL)
    
    # Fix double-escaped backslashes in inline math ($...$)
    def fix_inline_math(match):
        content = match.group(1)
        # Replace double backslashes with single backslashes
        content = re.sub(r'\\\\(?![\\])', r'\\', content)
        return f'${content}$'
    
    text = re.sub(r'\$([^$]+?)\$', fix_inline_math, text)
    
    return text


def format_math_expressions(text: str) -> str:
    """
    Ensure math expressions have proper spacing and formatting.
    
    - Inline math: $...$
    - Block math: $$...$$ on separate lines with blank lines before/after
    """
    if not text:
        return text
    
    # Protect already well-formatted block math
    text = re.sub(r'\n\n\$\$\n', '\n__BLOCK_MATH_START__\n', text)
    text = re.sub(r'\n\$\$\n\n', '\n__BLOCK_MATH_END__\n\n', text)
    
    # Fix block math that's not on separate lines
    # Add newlines before $$ if not already there
    text = re.sub(r'([^\n])\$\$', r'\1\n$$', text)
    # Add newlines after $$ if not already there
    text = re.sub(r'\$\$([^\n])', r'$$\n\1', text)
    
    # Ensure blank lines around block math
    text = re.sub(r'(?<!\n)\n\$\$\n', r'\n\n$$\n', text)
    text = re.sub(r'\n\$\$\n(?!\n)', r'\n$$\n\n', text)
    
    # Restore protected block math markers
    text = text.replace('__BLOCK_MATH_START__', '$$')
    text = text.replace('__BLOCK_MATH_END__', '$$')
    
    # Ensure inline math has proper spacing (no space inside delimiters)
    text = re.sub(r'\$\s+', r'$', text)
    text = re.sub(r'\s+\$', r'$', text)
    
    return text


def format_headings(text: str) -> str:
    """
    Ensure headings have proper # spacing and hierarchy.
    
    Format: # Title, ## Section, ### Subsection
    """
    if not text:
        return text
    
    # Ensure space after # symbols
    text = re.sub(r'^(#{1,6})([^\s#])', r'\1 \2', text, flags=re.MULTILINE)
    
    # Remove extra spaces after # symbols
    text = re.sub(r'^(#{1,6})\s{2,}', r'\1 ', text, flags=re.MULTILINE)
    
    # Ensure blank line before headings (except at start of document)
    text = re.sub(r'([^\n])\n(#{1,6}\s)', r'\1\n\n\2', text)
    
    # Ensure blank line after headings
    text = re.sub(r'(^#{1,6}\s[^\n]+)\n([^\n#])', r'\1\n\n\2', text, flags=re.MULTILINE)
    
    return text


def format_lists(text: str) -> str:
    """
    Ensure lists have proper indentation and formatting.
    
    - Bullet lists: -, *, +
    - Numbered lists: 1., 2., 3.
    """
    if not text:
        return text
    
    # Ensure space after list markers
    text = re.sub(r'^(\s*[-*+]|\d+\.)([^\s])', r'\1 \2', text, flags=re.MULTILINE)
    
    # Remove extra spaces after list markers
    text = re.sub(r'^(\s*[-*+]|\d+\.)\s{2,}', r'\1 ', text, flags=re.MULTILINE)
    
    # Ensure blank line before lists (except at start or after another list item)
    text = re.sub(r'([^\n])\n(\s*[-*+]|\d+\.)\s', r'\1\n\n\2 ', text)
    
    return text


def format_tables(text: str) -> str:
    """
    Ensure tables have proper markdown syntax with alignment.
    
    Format:
    | Header 1 | Header 2 |
    |----------|----------|
    | Cell 1   | Cell 2   |
    """
    if not text:
        return text
    
    # Ensure blank lines around tables
    # Detect table start (line with |)
    text = re.sub(r'([^\n])\n(\|[^\n]+\|)', r'\1\n\n\2', text)
    
    # Ensure blank line after tables
    lines = text.split('\n')
    result = []
    in_table = False
    
    for i, line in enumerate(lines):
        result.append(line)
        
        # Check if current line is a table row
        if '|' in line and line.strip().startswith('|'):
            in_table = True
        elif in_table and line.strip():
            # We were in a table, now we're not
            if '|' not in line:
                # Add blank line before this non-table line
                if i > 0 and result[-2].strip():
                    result.insert(-1, '')
                in_table = False
    
    return '\n'.join(result)


def format_code_blocks(text: str) -> str:
    """
    Ensure code blocks have proper triple backtick fencing with language tags.
    
    Format:
    ```python
    code here
    ```
    """
    if not text:
        return text
    
    # Ensure blank lines around code blocks
    text = re.sub(r'([^\n])\n```', r'\1\n\n```', text)
    text = re.sub(r'```\n([^\n])', r'```\n\n\1', text)
    
    # Ensure code fence is on its own line
    text = re.sub(r'([^\n])```', r'\1\n```', text)
    text = re.sub(r'```([^\n])', r'```\n\1', text)
    
    return text


def format_citations(text: str) -> str:
    """
    Ensure citations are properly formatted as [1], [2], etc.
    """
    if not text:
        return text
    
    # Ensure citations have proper spacing
    text = re.sub(r'\[\s*(\d+)\s*\]', r'[\1]', text)
    
    return text


def format_blockquotes(text: str) -> str:
    """
    Ensure blockquotes use > prefix consistently.
    """
    if not text:
        return text
    
    # Ensure space after > symbol
    text = re.sub(r'^>([^\s])', r'> \1', text, flags=re.MULTILINE)
    
    # Ensure blank line before blockquotes
    text = re.sub(r'([^\n])\n>', r'\1\n\n>', text)
    
    return text


def clean_extra_whitespace(text: str) -> str:
    """
    Clean up excessive whitespace while preserving intentional spacing.
    """
    if not text:
        return text
    
    # Remove trailing whitespace from lines
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
    
    # Limit consecutive blank lines to maximum of 2
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    
    # Remove spaces before newlines
    text = re.sub(r' +\n', '\n', text)
    
    return text


def format_research_output(text: str) -> str:
    """
    Main function to format all markdown elements in research output.
    
    Applies formatting for:
    - Math expressions (inline and block)
    - Headings
    - Lists
    - Tables
    - Code blocks
    - Citations
    - Blockquotes
    
    Args:
        text: Raw markdown text
        
    Returns:
        Formatted markdown text with proper LaTeX and markdown syntax
    """
    if not text or not isinstance(text, str):
        return text
    
    # Apply formatters in order
    # First, unescape any double-escaped LaTeX commands
    text = unescape_latex(text)
    text = format_math_expressions(text)
    text = format_code_blocks(text)
    text = format_headings(text)
    text = format_lists(text)
    text = format_tables(text)
    text = format_blockquotes(text)
    text = format_citations(text)
    text = clean_extra_whitespace(text)
    
    # Final cleanup: ensure document ends with single newline
    text = text.rstrip() + '\n'
    
    return text

