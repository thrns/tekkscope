"""
Prompt enhancement utilities to guide LLMs toward ideal token output ranges.
"""


def enhance_lens_prompt(query: str) -> str:
    """
    Add length guidance for lens mode (150-400 tokens ideal).
    
    Args:
        query: The user's research query
        
    Returns:
        Enhanced query with length guidance
    """
    return f"""Provide a concise but comprehensive summary covering the key points about: {query}

Guidelines:
- Aim for 150-400 tokens (approximately 3-6 bullet points or 1-2 paragraphs)
- Include the most important facts and overview
- Be clear and direct
- Focus on answering the core question efficiently

For mathematical formulas, ALWAYS use proper LaTeX syntax:
- Inline math: $formula$ (e.g., $\\int f(x) dx$, $\\omega$, $\\tau$)
- Display math: $$formula$$ on separate lines
- Do NOT use brackets [ ] or parentheses ( ) for math expressions
- Example: Use $\\int_{{a}}^{{b}} f(x) dx$ NOT [ \\int_{{a}}^{{b}} f(x) dx ]"""


def enhance_deeplens_prompt(query: str) -> str:
    """
    Add length guidance for deeplens mode (900-2500 tokens ideal).
    
    Args:
        query: The user's research query
        
    Returns:
        Enhanced query with length guidance
    """
    return f"""Provide a detailed analysis with multiple sections about: {query}

Guidelines:
- Aim for 900-2500 tokens (detailed explanations with 3-6 sections)
- Include comparisons, pros/cons, and in-depth analysis
- Provide context, examples, and supporting evidence
- Cover multiple perspectives and viewpoints
- Structure your response with clear sections and subsections

For mathematical formulas, ALWAYS use proper LaTeX syntax:
- Inline math: $formula$ (e.g., $\\int f(x) dx$, $\\omega$, $\\tau$)
- Display math: $$formula$$ on separate lines
- Do NOT use brackets [ ] or parentheses ( ) for math expressions
- Example: Use $\\int_{{a}}^{{b}} f(x) dx$ NOT [ \\int_{{a}}^{{b}} f(x) dx ]"""


def enhance_reportlens_prompt(query: str) -> str:
    """
    Add length guidance for reportlens mode (3000-8000 tokens ideal).
    
    Args:
        query: The user's research query
        
    Returns:
        Enhanced query with length guidance
    """
    return f"""Generate a comprehensive, professional research report about: {query}

Guidelines:
- Aim for 3000-8000 tokens (full research report format)
- Include: Executive summary, 5-15 sections with detailed subsections
- Provide multi-source citations and references throughout
- Add detailed analysis with SPECIFIC data, metrics, statistics, and evidence
- Include methodology, findings, recommendations, and actionable insights
- Structure as a deliverable-ready professional document
- Use confident, authoritative tone - write as an expert consultant
- NEVER use apologetic language: "Sorry", "Unable to access sources", "Limited information"
- Focus on analytical insights and practical implications, not generic definitions
- Include comparative analysis, case studies, or industry benchmarks where relevant
- Present data in tables or structured formats where appropriate
- Cite specific examples and concrete evidence from research
- Use proper markdown formatting with headings, lists, and tables

For mathematical formulas, ALWAYS use proper LaTeX syntax:
- Inline math: $formula$ (e.g., $\\int f(x) dx$, $\\omega$, $\\tau$)
- Display math: $$formula$$ on separate lines for complex equations
- Do NOT use brackets [ ] or parentheses ( ) for math expressions
- Example: Use $\\int_{{a}}^{{b}} f(x) dx = F(b) - F(a)$ NOT [ \\int_{{a}}^{{b}} f(x) dx = F(b) - F(a) ]

Write as a professional analyst delivering high-value, actionable insights."""

