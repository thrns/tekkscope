"""
Report generation utilities for converting markdown to various formats (PDF, DOCX).

All libraries are pure Python with no system dependencies required:
- PDF: Uses reportlab (pure Python, no system libraries needed)
- DOCX: Uses python-docx (pure Python)
- MD: No dependencies

Imports are lazy-loaded to prevent import errors from breaking the server.
"""
import os
from io import BytesIO
import re


def clean_text_for_pdf(text: str) -> str:
    """Clean text for PDF generation - remove markdown syntax and escape special chars"""
    # Remove markdown formatting and convert to HTML
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)  # Bold
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)  # Italic  
    text = re.sub(r'`(.+?)`', r'<font face="Courier">\1</font>', text)  # Code
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)  # Links (keep text only)
    
    # Remove LaTeX math (can't render in PDF easily)
    text = re.sub(r'\$\$.*?\$\$', '[Math Formula]', text, flags=re.DOTALL)
    text = re.sub(r'\$([^\$]+)\$', '[Formula]', text)
    
    # Remove citations like [1], [2], etc. but keep them visible
    text = re.sub(r'\[(\d+)\]', r'[\1]', text)
    
    # Escape XML special chars in text content only, preserving HTML tags
    # Use regex to identify HTML tags and protect them while escaping text content
    # Pattern matches HTML tags: <tag> or </tag> or <tag attr="value">
    html_tag_pattern = r'<[^>]+>'
    
    # Split text into HTML tags and text content
    parts = []
    last_end = 0
    
    for match in re.finditer(html_tag_pattern, text):
        # Add text before the tag (if any)
        if match.start() > last_end:
            text_content = text[last_end:match.start()]
            if text_content:
                parts.append(('text', text_content))
        
        # Add the HTML tag (unescaped)
        parts.append(('tag', match.group(0)))
        last_end = match.end()
    
    # Add remaining text after last tag (if any)
    if last_end < len(text):
        text_content = text[last_end:]
        if text_content:
            parts.append(('text', text_content))
    
    # If no HTML tags found, treat entire text as text content
    if not parts:
        parts.append(('text', text))
    
    # Rebuild text, escaping only text content
    result_parts = []
    for part_type, content in parts:
        if part_type == 'tag':
            # HTML tags are added as-is (they're already valid)
            result_parts.append(content)
        else:
            # Escape XML special chars in text content only
            # Must escape & first to avoid double-escaping
            escaped = content.replace('&', '&amp;')
            escaped = escaped.replace('<', '&lt;')
            escaped = escaped.replace('>', '&gt;')
            result_parts.append(escaped)
    
    return ''.join(result_parts)


def markdown_to_pdf(markdown_content: str, title: str = "Research Report") -> bytes:
    """
    Convert markdown content to PDF using reportlab (pure Python, no system dependencies).
    
    Args:
        markdown_content: The markdown text to convert
        title: Title of the report
        
    Returns:
        bytes: PDF file as bytes
        
    Raises:
        ImportError: If reportlab is not installed
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
        from reportlab.lib import colors
    except ImportError as e:
        raise ImportError(
            f"PDF generation dependencies are missing: {str(e)}\n"
            "Install with: pip install reportlab"
        )
    
    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Container for PDF elements
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER,
    )
    
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=20,
    )
    
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=10,
        spaceBefore=15,
    )
    
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=8,
        spaceBefore=12,
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leading=14,
    )
    
    # Add title
    story.append(Paragraph(clean_text_for_pdf(title), title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Parse markdown line by line
    lines = markdown_content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            story.append(Spacer(1, 0.1*inch))
            i += 1
            continue
        
        # Headers
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            text = line.lstrip('#').strip()
            text = clean_text_for_pdf(text)
            
            if level == 1:
                style = h1_style
            elif level == 2:
                style = h2_style
            else:
                style = h3_style
            
            story.append(Paragraph(text, style))
            story.append(Spacer(1, 0.1*inch))
        
        # Lists
        elif line.startswith(('- ', '* ', '+ ')) or re.match(r'^\d+\.', line):
            text = re.sub(r'^[\-\*\+]\s+|\d+\.\s+', '', line)
            text = clean_text_for_pdf(text)
            story.append(Paragraph(f"• {text}", body_style))
        
        # Regular paragraphs
        else:
            text = clean_text_for_pdf(line)
            # Only add if there's actual content
            if text.strip():
                story.append(Paragraph(text, body_style))
                story.append(Spacer(1, 0.1*inch))
        
        i += 1
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def markdown_to_docx(markdown_content: str, title: str = "Research Report") -> bytes:
    """
    Convert markdown content to DOCX using python-docx.
    
    Args:
        markdown_content: The markdown text to convert
        title: Title of the report
        
    Returns:
        bytes: DOCX file as bytes
        
    Raises:
        ImportError: If python-docx is not installed
    """
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError as e:
        raise ImportError(
            f"DOCX generation dependency is missing: {str(e)}\n"
            "Install with: pip install python-docx"
        )
    
    doc = Document()
    
    # Set document margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
    
    # Add title
    title_para = doc.add_heading(title, 0)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_para.runs[0]
    title_run.font.size = Pt(24)
    title_run.font.color.rgb = RGBColor(26, 26, 26)
    
    # Add a blank line
    doc.add_paragraph()
    
    # Parse markdown line by line
    lines = markdown_content.split('\n')
    in_code_block = False
    code_lines = []
    in_list = False
    list_items = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Handle code blocks
        if line.strip().startswith('```'):
            if in_code_block:
                # End code block
                code_text = '\n'.join(code_lines)
                para = doc.add_paragraph(code_text)
                para.style = 'Normal'
                para_format = para.paragraph_format
                para_format.left_indent = Inches(0.5)
                
                # Style code text
                for run in para.runs:
                    run.font.name = 'Courier New'
                    run.font.size = Pt(9)
                
                code_lines = []
                in_code_block = False
            else:
                # Start code block
                in_code_block = True
            i += 1
            continue
        
        if in_code_block:
            code_lines.append(line)
            i += 1
            continue
        
        # Handle headers
        if line.startswith('# ') and not line.startswith('## '):
            doc.add_heading(line[2:].strip(), 1)
        elif line.startswith('## ') and not line.startswith('### '):
            doc.add_heading(line[3:].strip(), 2)
        elif line.startswith('### ') and not line.startswith('#### '):
            doc.add_heading(line[4:].strip(), 3)
        elif line.startswith('#### '):
            doc.add_heading(line[5:].strip(), 4)
        
        # Handle lists
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            text = line.strip()[2:].strip()
            para = doc.add_paragraph(text, style='List Bullet')
        elif line.strip() and line.strip()[0].isdigit() and '. ' in line:
            # Numbered list
            text = line.strip().split('. ', 1)[1] if '. ' in line else line.strip()
            para = doc.add_paragraph(text, style='List Number')
        
        # Handle blockquotes
        elif line.strip().startswith('>'):
            text = line.strip()[1:].strip()
            para = doc.add_paragraph(text)
            para_format = para.paragraph_format
            para_format.left_indent = Inches(0.5)
            for run in para.runs:
                run.font.italic = True
                run.font.color.rgb = RGBColor(85, 85, 85)
        
        # Handle regular paragraphs
        elif line.strip():
            # Basic inline formatting
            text = line.strip()
            
            # Handle bold
            parts = []
            current = ""
            j = 0
            while j < len(text):
                if text[j:j+2] == '**':
                    if current:
                        parts.append(('normal', current))
                        current = ""
                    # Find closing **
                    end = text.find('**', j+2)
                    if end != -1:
                        parts.append(('bold', text[j+2:end]))
                        j = end + 2
                        continue
                current += text[j]
                j += 1
            if current:
                parts.append(('normal', current))
            
            # Add paragraph with formatting
            if parts:
                para = doc.add_paragraph()
                for style, content in parts:
                    run = para.add_run(content)
                    if style == 'bold':
                        run.bold = True
            else:
                doc.add_paragraph(text)
        
        i += 1
    
    # Save to bytes
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.read()


def generate_report_file(
    markdown_content: str,
    file_format: str = "pdf",
    title: str = "Research Report"
) -> bytes:
    """
    Generate a report file in the specified format.
    
    Args:
        markdown_content: The markdown content to convert
        file_format: The output format ('pdf', 'docx', or 'md')
        title: Title of the report
        
    Returns:
        bytes: File content as bytes
        
    Raises:
        ValueError: If file_format is not supported
    """
    file_format = file_format.lower()
    
    if file_format == "pdf":
        return markdown_to_pdf(markdown_content, title)
    elif file_format == "docx":
        return markdown_to_docx(markdown_content, title)
    elif file_format == "md" or file_format == "markdown":
        return markdown_content.encode('utf-8')
    else:
        raise ValueError(f"Unsupported file format: {file_format}. Supported formats: pdf, docx, md")

