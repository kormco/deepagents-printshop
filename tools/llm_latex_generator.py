"""LLM-Based LaTeX Generator that uses Claude for intelligent document generation."""

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import anthropic


@dataclass
class LaTeXGenerationRequest:
    """Request for LaTeX document generation."""
    title: str
    author: str
    content_sections: List[Dict]  # List of {title, content, type}
    tables: List[Dict] = None  # List of {caption, data, format}
    figures: List[Dict] = None  # List of {path, caption, width}
    requirements: List[str] = None  # Special requirements

    def __post_init__(self):
        if self.tables is None:
            self.tables = []
        if self.figures is None:
            self.figures = []
        if self.requirements is None:
            self.requirements = []


@dataclass
class LaTeXGenerationResult:
    """Result of LaTeX generation."""
    success: bool
    latex_content: str
    warnings: List[str]
    improvements_made: List[str]
    error_message: Optional[str] = None


class LLMLaTeXGenerator:
    """
    LLM-based LaTeX generator that uses Claude to intelligently create
    LaTeX documents with proper error handling and edge case management.

    This replaces the deterministic template-based approach with an
    intelligent system that can reason about LaTeX structure and syntax.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Anthropic API key."""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def generate_document(self, request: LaTeXGenerationRequest,
                          validate: bool = True) -> LaTeXGenerationResult:
        """
        Generate a complete LaTeX document using LLM reasoning.

        Args:
            request: LaTeX generation request with content and requirements
            validate: Whether to validate and fix LaTeX syntax

        Returns:
            LaTeXGenerationResult with generated LaTeX and metadata
        """
        print("📝 Generating LaTeX document with LLM reasoning...")

        # Step 1: Generate initial LaTeX
        latex_content = self._generate_initial_latex(request)

        if not latex_content:
            return LaTeXGenerationResult(
                success=False,
                latex_content="",
                warnings=[],
                improvements_made=[],
                error_message="Failed to generate initial LaTeX"
            )

        # Step 2: Validate and fix syntax if requested
        warnings = []
        improvements_made = []

        if validate:
            print("🔍 Validating and improving LaTeX syntax...")
            latex_content, validation_warnings, fixes = self._validate_and_fix_latex(
                latex_content, request
            )
            warnings.extend(validation_warnings)
            improvements_made.extend(fixes)

        return LaTeXGenerationResult(
            success=True,
            latex_content=latex_content,
            warnings=warnings,
            improvements_made=improvements_made
        )

    def _generate_initial_latex(self, request: LaTeXGenerationRequest) -> str:
        """Generate initial LaTeX document using Claude."""
        # Build the generation prompt
        prompt = self._build_generation_prompt(request)

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=16000,  # Increased for complex documents with many figures
                temperature=0.2,  # Lower temperature for more consistent LaTeX
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract LaTeX from response
            latex_content = self._extract_latex_from_response(response.content[0].text)
            print(f"✅ Generated {len(latex_content)} characters of LaTeX")
            return latex_content

        except Exception as e:
            print(f"❌ Error generating LaTeX: {e}")
            return ""

    def _build_generation_prompt(self, request: LaTeXGenerationRequest) -> str:
        """Build the prompt for LaTeX generation."""
        # Prepare content sections summary
        sections_summary = "\n".join([
            f"- {sec.get('title', 'Untitled')}: {len(sec.get('content', ''))} characters"
            for sec in request.content_sections
        ])

        # Prepare tables summary
        tables_summary = "\n".join([
            f"- {table.get('caption', 'Untitled table')}"
            for table in request.tables
        ]) if request.tables else "No tables"

        # Prepare figures summary
        figures_summary = "\n".join([
            f"- {fig.get('caption', 'Untitled figure')}: {fig.get('path', 'no path')}"
            for fig in request.figures
        ]) if request.figures else "No figures"

        # Build requirements
        requirements_text = "\n".join([
            f"- {req}" for req in request.requirements
        ]) if request.requirements else "Standard research document formatting"

        prompt = f"""You are a LaTeX document generation expert. Generate a complete, professional LaTeX document based on the following specifications.

**CRITICAL REQUIREMENTS:**
1. Generate COMPLETE, VALID LaTeX that compiles without errors
2. Use ONLY packages that are commonly available in TeX Live
3. Escape ALL special LaTeX characters properly (%, $, &, #, _, {{, }}, etc.)
4. Include proper document structure: preamble, \\begin{{document}}, content, \\end{{document}}
5. Use proper spacing and formatting for readability
6. Include table of contents if document has multiple sections
7. Add page numbers and basic header/footer

**Document Specifications:**
Title: {request.title}
Author: {request.author}

**Content Sections:**
{sections_summary}

**Tables:**
{tables_summary}

**Figures:**
{figures_summary}

**Special Requirements:**
{requirements_text}

**Content Details:**
"""

        # Add detailed content for each section
        for i, section in enumerate(request.content_sections, 1):
            prompt += f"\n\n--- Section {i}: {section.get('title', 'Untitled')} ---\n"
            prompt += section.get('content', '')

        # Add table data
        if request.tables:
            prompt += "\n\n**Table Data:**\n"
            for table in request.tables:
                prompt += f"\nTable: {table.get('caption', 'Untitled')}\n"
                prompt += f"Data: {json.dumps(table.get('data', []))}\n"

        # Add figure information with explicit LaTeX code
        if request.figures:
            prompt += "\n\n**FIGURES - MUST INCLUDE ALL:**\n"
            prompt += "You MUST include \\includegraphics for each figure listed below.\n\n"
            for fig in request.figures:
                default_width = '0.8\\textwidth'
                path = fig.get('path', 'unknown')
                caption = fig.get('caption', 'Untitled')
                width = fig.get('width', default_width)
                placement = fig.get('placement', '')
                prompt += f"Figure: {caption}\n"
                prompt += f"  Placement hint: {placement}\n" if placement else ""
                prompt += "  USE THIS EXACT CODE:\n"
                prompt += "  \\begin{figure}[H]\n"
                prompt += "  \\centering\n"
                prompt += f"  \\includegraphics[width={width}]{{{path}}}\n"
                prompt += f"  \\caption{{{caption}}}\n"
                prompt += "  \\end{figure}\n\n"

        prompt += """

**Output Instructions:**
Generate a COMPLETE LaTeX document with the following structure:

1. Preamble with necessary packages (use standard packages only)
2. Document metadata (title, author, date)
3. \\begin{document}
4. Title page with \\maketitle
5. Table of contents (if multiple sections)
6. All content sections with proper formatting
7. All tables with proper booktabs formatting
8. **ALL FIGURES using \\includegraphics - DO NOT SKIP ANY**
9. \\end{document}

**CRITICAL - FIGURES:**
- You MUST include ALL figures listed above using \\includegraphics
- Use the EXACT paths provided (e.g., ../sample_content/magazine/images/filename.png)
- Include \\usepackage{graphicx} in the preamble
- Use [H] placement specifier (requires \\usepackage{float})

**IMPORTANT:**
- Escape special characters: % → \\%, $ → \\$, & → \\&, # → \\#, _ → \\_, { → \\{, } → \\}
- Use \\section{}, \\subsection{}, etc. for structure
- Use [H] placement for tables/figures to avoid floating issues
- Include \\usepackage{hyperref} for clickable links
- Include \\usepackage{graphicx} for images
- Include \\usepackage{float} for [H] placement

**ATTRIBUTION REQUIREMENT:**
- Include "Generated by DeepAgents PrintShop" attribution at the end of the document
- For magazines: Add it on the back cover or last page footer
- For reports: Add it as a small footer note on the last page
- Example: \\textit{{Generated by DeepAgents PrintShop}} or in a footnote

Return ONLY the complete LaTeX code, no explanations or markdown code blocks.
"""

        return prompt

    def _extract_latex_from_response(self, response_text: str) -> str:
        """Extract LaTeX code from Claude's response."""
        # Remove markdown code blocks if present
        if "```latex" in response_text:
            start = response_text.find("```latex") + 8
            end = response_text.find("```", start)
            return response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            return response_text[start:end].strip()
        else:
            return response_text.strip()

    def _validate_and_fix_latex(self, latex_content: str,
                                request: LaTeXGenerationRequest) -> Tuple[str, List[str], List[str]]:
        """
        Validate LaTeX syntax and fix common issues using LLM reasoning.

        Returns:
            Tuple of (fixed_latex, warnings, improvements_made)
        """
        validation_prompt = f"""You are a LaTeX syntax validator and fixer. Analyze this LaTeX document and fix any issues.

**LaTeX Document to Validate:**
```latex
{latex_content}
```

**Validation Checklist:**
1. Proper document structure (\\documentclass, \\begin{{document}}, \\end{{document}})
2. All special characters properly escaped
3. All environments properly closed
4. Package usage is correct and packages exist
5. No syntax errors
6. Proper use of math mode
7. Figure and table references are valid
8. No orphaned braces or brackets

**Your Task:**
1. Identify any syntax errors or issues
2. Fix all issues while preserving the document's intent
3. List what improvements you made

**Output Format:**
First, list any issues you found as JSON:
{{"issues": ["issue1", "issue2"]}}

Then provide the CORRECTED LaTeX code (complete document).
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                temperature=0.1,  # Very low temperature for precise fixes
                messages=[{
                    "role": "user",
                    "content": validation_prompt
                }]
            )

            response_text = response.content[0].text

            # Extract issues
            warnings = []
            if '"issues":' in response_text:
                try:
                    start = response_text.find('{')
                    end = response_text.find('}', start) + 1
                    issues_json = json.loads(response_text[start:end])
                    warnings = issues_json.get('issues', [])
                except (json.JSONDecodeError, ValueError):
                    warnings = ["Unable to parse validation issues"]

            # Extract fixed LaTeX
            fixed_latex = self._extract_latex_from_response(response_text)

            # If extraction failed, return original
            if not fixed_latex or len(fixed_latex) < len(latex_content) * 0.5:
                print("⚠️ Validation fix failed, using original LaTeX")
                return latex_content, warnings, []

            improvements = [f"Fixed {len(warnings)} LaTeX issues"] if warnings else []
            print(f"✅ Validated and fixed {len(warnings)} issues")

            return fixed_latex, warnings, improvements

        except Exception as e:
            print(f"⚠️ Validation error: {e}, using original LaTeX")
            return latex_content, [f"Validation failed: {str(e)}"], []

    def apply_visual_qa_fixes(self, latex_content: str,
                             issues: List[str]) -> Tuple[str, bool, List[str]]:
        """
        Apply fixes to LaTeX based on Visual QA feedback using targeted patches.

        Instead of regenerating the entire document (which causes truncation),
        this method generates specific patches to apply to the preamble.

        Args:
            latex_content: Current LaTeX document
            issues: List of issues found by Visual QA

        Returns:
            Tuple of (fixed_latex, success, fixes_applied)
        """
        print(f"🔧 Applying {len(issues)} Visual QA fixes to LaTeX...")

        # Build the fix prompt - ask for PATCHES not full document
        issues_text = "\n".join([f"- {issue}" for issue in issues])

        # Extract just the preamble for context (much smaller)
        begin_doc_pos = latex_content.find('\\begin{document}')
        if begin_doc_pos == -1:
            print("❌ Could not find \\begin{document}")
            return latex_content, False, []

        preamble = latex_content[:begin_doc_pos]

        fix_prompt = f"""You are a LaTeX document improvement specialist. Generate ONLY the LaTeX commands needed to fix these visual issues.

**Current Preamble (for context):**
```latex
{preamble[:3000]}...
```

**Issues to Fix:**
{issues_text}

**Your Task:**
Generate a small block of LaTeX commands that should be INSERTED just before \\begin{{document}} to fix these issues.

**Available Fixes (use these patterns):**
- Table spacing: \\renewcommand{{\\arraystretch}}{{1.2}}
- Table column padding: \\setlength{{\\tabcolsep}}{{6pt}}
- Line spacing: \\linespread{{1.1}}
- Paragraph spacing: \\setlength{{\\parskip}}{{0.5em plus 0.1em minus 0.05em}}
- Header height: \\setlength{{\\headheight}}{{14.5pt}}
- Top margin adjustment: \\addtolength{{\\topmargin}}{{-2.5pt}}

**Rules:**
- Output ONLY the LaTeX commands to add (no explanations)
- Do NOT include \\documentclass, \\begin{{document}}, etc.
- Do NOT use microtype, setspace, or longtabu packages
- Keep it minimal - only what's needed for the issues
- If no fix is needed, output: % No fixes required

**Output Format:**
```latex
% Visual QA Fixes
<your commands here>
```
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,  # Small output - just patches
                temperature=0.1,
                messages=[{
                    "role": "user",
                    "content": fix_prompt
                }]
            )

            response_text = response.content[0].text

            # Extract LaTeX commands from response
            if '```latex' in response_text:
                start = response_text.find('```latex') + 8
                end = response_text.find('```', start)
                patch_content = response_text[start:end].strip()
            elif '```' in response_text:
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                patch_content = response_text[start:end].strip()
            else:
                patch_content = response_text.strip()

            # Skip if no fixes needed
            if not patch_content or 'No fixes required' in patch_content:
                print("ℹ️ No Visual QA fixes needed")
                return latex_content, True, ["No fixes required"]

            # Validate patch doesn't contain dangerous commands
            dangerous_patterns = ['\\documentclass', '\\begin{document}', '\\end{document}']
            for pattern in dangerous_patterns:
                if pattern in patch_content:
                    print(f"❌ Patch contains invalid command: {pattern}")
                    return latex_content, False, []

            # Insert patch before \begin{document}
            fixed_latex = (
                latex_content[:begin_doc_pos] +
                f"\n% Visual QA Fixes\n{patch_content}\n\n" +
                latex_content[begin_doc_pos:]
            )

            # Validate the result
            if fixed_latex.count('\\begin{') != fixed_latex.count('\\end{'):
                print("❌ Fix created unmatched environments")
                return latex_content, False, []

            fixes_applied = [f"Applied patch: {patch_content[:100]}..."]
            print("✅ Successfully applied Visual QA patch")

            return fixed_latex, True, fixes_applied

        except Exception as e:
            print(f"❌ Error applying Visual QA fixes: {e}")
            return latex_content, False, []

    def complete_truncated_document(self, latex_content: str, max_attempts: int = 3) -> Tuple[str, bool]:
        """
        Complete a truncated LaTeX document by generating only the missing ending.

        Instead of regenerating the entire document, this method:
        1. Sends only the last portion of the document for context
        2. Asks the LLM to complete from where it was cut off
        3. Appends the completion to the original

        Args:
            latex_content: Truncated LaTeX document (missing \\end{document})
            max_attempts: Maximum completion attempts

        Returns:
            Tuple of (completed_latex, success)
        """
        print("🔧 Completing truncated document...")

        # Find a good cut point - end of a complete line or environment
        cut_point = len(latex_content)
        for marker in ['\n\\end{', '\n\\section', '\n\\subsection', '\n\n']:
            last_pos = latex_content.rfind(marker)
            if last_pos > len(latex_content) - 2000 and last_pos > 0:
                # Found a good cut point near the end
                cut_point = last_pos + len(marker.split('\n')[0]) + 1 if '\n' in marker else last_pos
                break

        # If we found incomplete environments, cut before them
        last_begin = latex_content.rfind('\\begin{')
        if last_begin > cut_point - 500:
            # There's an unclosed environment - cut before it
            cut_point = last_begin

        # Get the truncated portion we're keeping
        keep_text = latex_content[:cut_point]
        context_size = 4000
        context_for_llm = keep_text[-context_size:] if len(keep_text) > context_size else keep_text

        for attempt in range(1, max_attempts + 1):
            print(f"   Completion attempt {attempt}/{max_attempts}...")

            completion_prompt = f"""You are completing a LaTeX document that was truncated mid-generation.

**END OF THE TRUNCATED DOCUMENT (last part before cut-off):**
```latex
{context_for_llm}
```

**Your Task:**
Generate ONLY the remaining content needed to properly end this document.

**Requirements:**
1. Close any open environments (multicols, figure, tikzpicture, itemize, etc.)
2. Add any remaining content sections if appropriate
3. End with \\end{{document}}
4. Make sure all braces and environments are balanced
5. Keep it concise - just complete what's missing

**CRITICAL:**
- Do NOT repeat content that's already in the document
- Start your output from exactly where the document was cut off
- Include ONLY the completion, not the full document
- The output should seamlessly continue from the last line shown above

Return ONLY the LaTeX completion code, no explanations."""

            try:
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4000,  # Enough for completion, not full document
                    temperature=0.1,
                    messages=[{
                        "role": "user",
                        "content": completion_prompt
                    }]
                )

                completion = response.content[0].text.strip()

                # Clean up the completion - remove markdown code blocks if present
                if '```latex' in completion:
                    completion = completion.split('```latex', 1)[1]
                    if '```' in completion:
                        completion = completion.split('```')[0]
                elif '```' in completion:
                    completion = completion.split('```')[1] if completion.startswith('```') else completion
                    if '```' in completion:
                        completion = completion.split('```')[0]

                completion = completion.strip()

                # Validate completion has \end{document}
                if '\\end{document}' not in completion:
                    print(f"   ❌ Attempt {attempt}: Completion missing \\end{{document}}")
                    continue

                # Combine original (truncated to cut point) with completion
                completed_latex = keep_text + '\n' + completion

                # Verify the result has proper structure
                if '\\begin{document}' in completed_latex and '\\end{document}' in completed_latex:
                    print(f"   ✅ Document completed successfully ({len(completion)} chars added)")
                    return completed_latex, True

            except Exception as e:
                print(f"   ❌ Attempt {attempt} failed: {e}")
                continue

        print(f"❌ Document completion failed after {max_attempts} attempts")
        return latex_content, False

    def self_correct_compilation_errors(self, latex_content: str,
                                       compilation_error: str,
                                       max_attempts: int = 3) -> Tuple[str, bool, List[str]]:
        """
        Self-correct LaTeX based on compilation errors using LLM reasoning.

        This implements a feedback loop where the LLM:
        1. Receives the LaTeX that failed to compile
        2. Analyzes the compilation error
        3. Generates a corrected version
        4. Returns for re-compilation

        Args:
            latex_content: LaTeX that failed to compile
            compilation_error: Error message from pdflatex
            max_attempts: Maximum self-correction attempts

        Returns:
            Tuple of (corrected_latex, success, corrections_made)
        """
        print("🤖 LLM Self-Correction: Analyzing compilation error...")

        corrections_made = []
        current_latex = latex_content

        for attempt in range(1, max_attempts + 1):
            print(f"   Attempt {attempt}/{max_attempts}: Analyzing error...")

            correction_prompt = f"""You are a LaTeX debugging expert. A LaTeX document failed to compile and you need to fix it.

**LaTeX Document (FAILED TO COMPILE):**
```latex
{current_latex}
```

**Compilation Error:**
```
{compilation_error}
```

**Your Task:**
1. **Analyze the error carefully** - understand what went wrong
2. **Identify the root cause** - is it a package issue, syntax error, or incompatibility?
3. **Generate a corrected version** that will compile successfully
4. **Use ONLY reliable, standard LaTeX techniques**

**Common Error Fixes:**
- "auto expansion is only possible with scalable fonts" → REMOVE microtype package or disable expansion
- "File X.sty not found" → REMOVE that package and use alternative approach
- "Missing \\begin{{document}}" → Fix document structure
- "Too many }}" or "Missing }}" → Fix brace matching
- Package conflicts → Remove conflicting packages

**Critical Rules:**
- If a package causes errors, REMOVE it entirely and use manual commands instead
- If microtype fails, remove it and use \\linespread{{}} for spacing
- If setspace fails, use \\setlength{{\\baselineskip}}{{}} instead
- Preserve ALL document content
- Focus on making it COMPILE, not perfection
- Use simple, proven LaTeX commands

**IMPORTANT: The corrected LaTeX MUST compile without errors.**

Return ONLY the COMPLETE CORRECTED LaTeX document, no explanations.
"""

            try:
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=8000,
                    temperature=0.1,
                    messages=[{
                        "role": "user",
                        "content": correction_prompt
                    }]
                )

                corrected_latex = self._extract_latex_from_response(response.content[0].text)

                # Validate correction
                if not corrected_latex or len(corrected_latex) < len(latex_content) * 0.5:
                    print(f"   ❌ Attempt {attempt} generated invalid LaTeX")
                    continue

                # Check basic structure
                if '\\begin{document}' not in corrected_latex or '\\end{document}' not in corrected_latex:
                    print(f"   ❌ Attempt {attempt} missing document structure")
                    continue

                corrections_made.append(f"Attempt {attempt}: Fixed compilation error")
                print(f"   ✅ Attempt {attempt}: Generated corrected LaTeX")

                return corrected_latex, True, corrections_made

            except Exception as e:
                print(f"   ❌ Attempt {attempt} failed: {e}")
                continue

        # All attempts failed
        print(f"❌ Self-correction failed after {max_attempts} attempts")
        return latex_content, False, corrections_made
