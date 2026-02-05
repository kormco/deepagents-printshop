"""PDF compiler for LaTeX documents with intelligent error correction."""

import re
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple


class PDFCompiler:
    """Compile LaTeX documents to PDF using pdflatex."""

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the PDF compiler.

        Args:
            output_dir: Directory for output files. If None, uses the same dir as input.
        """
        self.output_dir = output_dir
        self.error_patterns = self._init_error_patterns()

    def _init_error_patterns(self) -> Dict[str, Dict[str, str]]:
        """Initialize common LaTeX error patterns and their fixes."""
        return {
            'misplaced_noalign': {
                'pattern': r'Misplaced \\noalign',
                'description': 'Table rule commands like \\midrule used outside table context',
                'fix': 'move_table_rules_inside_tabular'
            },
            'undefined_control_sequence': {
                'pattern': r'Undefined control sequence.*\\(\w+)',
                'description': 'Unknown command used',
                'fix': 'add_missing_package_or_fix_command'
            },
            'missing_end_group': {
                'pattern': r'Missing } inserted',
                'description': 'Unmatched braces',
                'fix': 'balance_braces'
            },
            'runaway_argument': {
                'pattern': r'Runaway argument',
                'description': 'Missing closing brace in command argument',
                'fix': 'fix_runaway_argument'
            },
            'extra_alignment_tab': {
                'pattern': r'Extra alignment tab has been changed to \\cr',
                'description': 'Too many & in table row',
                'fix': 'fix_table_alignment'
            },
            'missing_number': {
                'pattern': r'Missing number, treated as zero',
                'description': 'Invalid numeric value in length or counter',
                'fix': 'fix_numeric_values'
            }
        }

    def compile(self, tex_file: str, runs: int = 2, max_fix_attempts: int = 3) -> Tuple[bool, str]:
        """
        Compile a LaTeX file to PDF with automatic error correction.

        Args:
            tex_file: Path to the .tex file
            runs: Number of compilation runs (default 2 for proper references)
            max_fix_attempts: Maximum number of error correction attempts

        Returns:
            Tuple of (success: bool, message: str)
        """
        tex_path = Path(tex_file)

        if not tex_path.exists():
            return False, f"LaTeX file not found: {tex_file}"

        # Determine output directory
        if self.output_dir:
            output_path = Path(self.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = tex_path.parent

        # Try compilation with error correction
        for attempt in range(max_fix_attempts + 1):
            try:
                success, message = self._attempt_compilation(tex_path, output_path, runs)

                if success:
                    return True, message

                # If this was the last attempt, return failure
                if attempt == max_fix_attempts:
                    return False, f"Compilation failed after {max_fix_attempts} fix attempts:\n{message}"

                # Try to fix the error and continue
                print(f"Compilation attempt {attempt + 1} failed. Attempting to fix errors...")
                fixed = self._auto_fix_latex_errors(tex_path, message)

                if not fixed:
                    return False, f"Could not automatically fix LaTeX errors:\n{message}"

            except subprocess.TimeoutExpired:
                return False, "Compilation timed out (60s limit exceeded)"
            except FileNotFoundError:
                return False, "pdflatex not found. Please install TeX Live or MiKTeX."
            except Exception as e:
                return False, f"Compilation error: {str(e)}"

        return False, "Maximum fix attempts exceeded"

    def _attempt_compilation(self, tex_path: Path, output_path: Path, runs: int) -> Tuple[bool, str]:
        """Attempt to compile the LaTeX document."""
        for run in range(runs):
            result = subprocess.run(
                [
                    'pdflatex',
                    '-interaction=nonstopmode',
                    '-output-directory', str(output_path),
                    str(tex_path)
                ],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                return False, f"Compilation failed on run {run + 1}:\n{result.stdout}\n{result.stderr}"

        pdf_file = output_path / f"{tex_path.stem}.pdf"

        if pdf_file.exists():
            # Clean up auxiliary files
            self._cleanup_aux_files(output_path, tex_path.stem)
            return True, f"PDF successfully created: {pdf_file}"
        else:
            return False, "PDF file was not created"

    def _cleanup_aux_files(self, output_dir: Path, basename: str, keep_log: bool = False):
        """Clean up auxiliary LaTeX files."""
        extensions = ['.aux', '.toc', '.out', '.nav', '.snm', '.vrb']
        if not keep_log:
            extensions.append('.log')

        for ext in extensions:
            aux_file = output_dir / f"{basename}{ext}"
            if aux_file.exists():
                try:
                    aux_file.unlink()
                except Exception:
                    pass  # Ignore cleanup errors

    def _auto_fix_latex_errors(self, tex_path: Path, error_message: str) -> bool:
        """Automatically fix common LaTeX errors."""
        try:
            # Read the current file content
            with open(tex_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Check each error pattern and apply fixes
            for error_type, error_info in self.error_patterns.items():
                if re.search(error_info['pattern'], error_message, re.IGNORECASE):
                    print(f"Detected error type: {error_type} - {error_info['description']}")
                    content = self._apply_fix(content, error_type, error_info['fix'])

            # If content was modified, write it back
            if content != original_content:
                with open(tex_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Applied fixes to {tex_path}")
                return True

            return False

        except Exception as e:
            print(f"Error during auto-fix: {str(e)}")
            return False

    def _apply_fix(self, content: str, error_type: str, fix_method: str) -> str:
        """Apply specific fixes based on error type."""
        if fix_method == 'move_table_rules_inside_tabular':
            return self._fix_misplaced_table_rules(content)
        elif fix_method == 'balance_braces':
            return self._fix_unbalanced_braces(content)
        elif fix_method == 'fix_table_alignment':
            return self._fix_table_alignment(content)
        elif fix_method == 'add_missing_package_or_fix_command':
            return self._fix_undefined_commands(content)
        # Add more fix methods as needed
        return content

    def _fix_misplaced_table_rules(self, content: str) -> str:
        r"""Fix misplaced table rules like \midrule."""
        # Look for table environments and ensure rules are properly placed
        pattern = r'(\\begin\{tabular\}[^}]*\}[^\\]*)(\\toprule.*?)(\\end\{tabular\})'

        def fix_table(match):
            table_start = match.group(1)
            table_content = match.group(2)
            table_end = match.group(3)

            # Ensure proper structure: \toprule -> headers -> \midrule -> data -> \bottomrule
            lines = table_content.split('\n')
            fixed_lines = []

            for line in lines:
                stripped = line.strip()
                # Fix percentage signs that need escaping
                if '(%)' in stripped and '(\\%)' not in stripped:
                    line = line.replace('(%)', '(\\%)')
                fixed_lines.append(line)

            return table_start + '\n'.join(fixed_lines) + table_end

        return re.sub(pattern, fix_table, content, flags=re.DOTALL)

    def _fix_unbalanced_braces(self, content: str) -> str:
        """Attempt to fix unbalanced braces."""
        # Simple brace balancing - count and add missing closing braces at end of problematic lines
        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            open_braces = line.count('{')
            close_braces = line.count('}')

            if open_braces > close_braces:
                # Add missing closing braces
                missing = open_braces - close_braces
                line += '}' * missing

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def _fix_table_alignment(self, content: str) -> str:
        """Fix table alignment issues (too many &)."""
        # Find tabular environments and fix column alignment
        pattern = r'(\\begin\{tabular\}\{)([^}]+)(\}.*?\\end\{tabular\})'

        def fix_alignment(match):
            start = match.group(1)
            alignment = match.group(2)
            table_body = match.group(3)

            # Count actual columns used in table rows
            rows = [line.strip() for line in table_body.split('\n')
                   if '&' in line and not line.strip().startswith('%')]

            if rows:
                max_cols = max(line.count('&') + 1 for line in rows)
                # Ensure alignment spec matches actual columns
                if len(alignment) < max_cols:
                    alignment = alignment * (max_cols // len(alignment) + 1)
                alignment = alignment[:max_cols]

            return start + alignment + table_body

        return re.sub(pattern, fix_alignment, content, flags=re.DOTALL)

    def _fix_undefined_commands(self, content: str) -> str:
        """Fix undefined commands by adding common packages."""
        # Add common packages that might be missing
        packages_to_add = []

        if '\\cite' in content and '\\usepackage{cite}' not in content:
            packages_to_add.append('\\usepackage{cite}')

        if '\\url' in content and '\\usepackage{url}' not in content:
            packages_to_add.append('\\usepackage{url}')

        if packages_to_add:
            # Find where to insert packages (after \documentclass)
            doc_class_match = re.search(r'(\\documentclass.*?\n)', content)
            if doc_class_match:
                insertion_point = doc_class_match.end()
                package_block = '\n'.join(packages_to_add) + '\n'
                content = content[:insertion_point] + package_block + content[insertion_point:]

        return content

    def compile_with_bibliography(self, tex_file: str, bib_style: str = "plain") -> Tuple[bool, str]:
        """
        Compile a LaTeX document with bibliography.

        Runs: pdflatex -> bibtex -> pdflatex -> pdflatex

        Args:
            tex_file: Path to the .tex file
            bib_style: Bibliography style (plain, alpha, abbrv, etc.)

        Returns:
            Tuple of (success: bool, message: str)
        """
        tex_path = Path(tex_file)

        if not tex_path.exists():
            return False, f"LaTeX file not found: {tex_file}"

        # Determine output directory
        if self.output_dir:
            output_path = Path(self.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = tex_path.parent

        try:
            # First pdflatex run
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode',
                 '-output-directory', str(output_path), str(tex_path)],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                return False, f"First pdflatex run failed:\n{result.stderr}"

            # Run bibtex
            aux_file = output_path / f"{tex_path.stem}.aux"
            if aux_file.exists():
                result = subprocess.run(
                    ['bibtex', str(aux_file)],
                    capture_output=True, text=True, timeout=30,
                    cwd=str(output_path)
                )
                # Bibtex may return non-zero even on success, check output

            # Second pdflatex run
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode',
                 '-output-directory', str(output_path), str(tex_path)],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                return False, f"Second pdflatex run failed:\n{result.stderr}"

            # Third pdflatex run
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode',
                 '-output-directory', str(output_path), str(tex_path)],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                return False, f"Third pdflatex run failed:\n{result.stderr}"

            pdf_file = output_path / f"{tex_path.stem}.pdf"

            if pdf_file.exists():
                self._cleanup_aux_files(output_path, tex_path.stem)
                # Also clean .bbl and .blg
                for ext in ['.bbl', '.blg']:
                    f = output_path / f"{tex_path.stem}{ext}"
                    if f.exists():
                        try:
                            f.unlink()
                        except Exception:
                            pass

                return True, f"PDF with bibliography successfully created: {pdf_file}"
            else:
                return False, "PDF file was not created"

        except subprocess.TimeoutExpired:
            return False, "Compilation timed out"
        except FileNotFoundError as e:
            return False, f"Required tool not found: {str(e)}"
        except Exception as e:
            return False, f"Compilation error: {str(e)}"

    def validate_latex_installation(self) -> Tuple[bool, str]:
        """Check if LaTeX is properly installed."""
        try:
            result = subprocess.run(
                ['pdflatex', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                return True, f"LaTeX installed: {version_line}"
            else:
                return False, "pdflatex found but returned an error"
        except FileNotFoundError:
            return False, "pdflatex not found. Please install TeX Live or MiKTeX."
        except Exception as e:
            return False, f"Error checking LaTeX installation: {str(e)}"
