"""Recompile a printshop run's .tex file to PDF.

Used by the /printshop-review Claude Code skill after the user accepts a fix.
Wraps PDFCompiler so the skill never has to drive pdflatex directly and gets
the same multi-pass + regex-fix behavior as the autonomous pipeline.

Usage:
    python -m tools.recompile <run_id_or_dir> [--content-source NAME] [--update-handoff]
    python -m tools.recompile artifacts/output/abc12345
    python -m tools.recompile abc12345 --content-source resume
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Make the project root importable when invoked as `python tools/recompile.py`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.pdf_compiler import PDFCompiler  # noqa: E402


def resolve_run_dir(run_id_or_dir: str) -> Path:
    """Accept either a run_id (e.g. abc12345) or a path under artifacts/output/."""
    candidate = Path(run_id_or_dir)
    if candidate.is_dir():
        return candidate.resolve()
    default = PROJECT_ROOT / "artifacts" / "output" / run_id_or_dir
    if default.is_dir():
        return default.resolve()
    raise FileNotFoundError(
        f"Could not locate run directory for {run_id_or_dir!r}. "
        f"Tried {candidate} and {default}."
    )


def discover_tex_file(run_dir: Path, content_source: Optional[str]) -> Path:
    """Find the .tex file to compile inside a run directory."""
    if content_source:
        explicit = run_dir / f"{content_source}.tex"
        if explicit.exists():
            return explicit
        raise FileNotFoundError(f"{explicit} does not exist")

    tex_files = sorted(run_dir.glob("*.tex"))
    # Skip throwaway candidate fixes like research_report.fix1.tex
    tex_files = [p for p in tex_files if ".fix" not in p.stem]
    if not tex_files:
        raise FileNotFoundError(f"No .tex files in {run_dir}")
    if len(tex_files) > 1:
        names = ", ".join(p.name for p in tex_files)
        raise RuntimeError(
            f"Multiple .tex files in {run_dir} ({names}). "
            f"Pass --content-source to disambiguate."
        )
    return tex_files[0]


def count_pdf_pages(pdf_path: Path) -> Optional[int]:
    """Best-effort page count, or None if no reader is available."""
    try:
        from pdf2image.pdf2image import pdfinfo_from_path  # type: ignore

        return int(pdfinfo_from_path(str(pdf_path)).get("Pages", 0)) or None
    except Exception:
        pass
    try:
        from pypdf import PdfReader  # type: ignore

        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        return None


def update_handoff(run_dir: Path, pdf_path: Path) -> None:
    """Refresh page count + timestamp in handoff.json if it exists."""
    manifest_path = run_dir / "handoff.json"
    if not manifest_path.exists():
        return
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"warn: could not update {manifest_path}: {e}")
        return

    manifest["pdf_exists"] = pdf_path.exists()
    manifest["pdf_path"] = str(pdf_path)
    if pdf_path.exists():
        manifest["page_count"] = count_pdf_pages(pdf_path)
    manifest["last_recompile"] = datetime.now().isoformat()

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def recompile(
    run_id_or_dir: str,
    content_source: Optional[str] = None,
    update_handoff_manifest: bool = True,
) -> Tuple[bool, str, Path]:
    """Recompile the .tex inside the given run directory.

    Returns (success, message, pdf_path).
    """
    run_dir = resolve_run_dir(run_id_or_dir)
    tex_path = discover_tex_file(run_dir, content_source)
    pdf_path = tex_path.with_suffix(".pdf")

    compiler = PDFCompiler(output_dir=str(run_dir))
    success, message = compiler.compile(str(tex_path))

    if update_handoff_manifest:
        update_handoff(run_dir, pdf_path)

    return success, message, pdf_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recompile a printshop run's .tex to PDF.",
    )
    parser.add_argument(
        "run",
        help="Run id (e.g. abc12345) or path to a run directory under artifacts/output/.",
    )
    parser.add_argument(
        "--content-source",
        default=None,
        help="Override the .tex stem (e.g. 'resume', 'magazine'). "
        "Auto-detected when only one .tex file is present.",
    )
    parser.add_argument(
        "--no-update-handoff",
        dest="update_handoff",
        action="store_false",
        help="Skip refreshing handoff.json after a successful recompile.",
    )
    args = parser.parse_args()

    try:
        success, message, pdf_path = recompile(
            args.run,
            content_source=args.content_source,
            update_handoff_manifest=args.update_handoff,
        )
    except (FileNotFoundError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if success:
        print(f"PDF compiled: {pdf_path}")
        return 0
    print(f"compilation failed: {message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
