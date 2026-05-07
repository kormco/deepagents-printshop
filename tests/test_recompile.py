"""Tests for tools.recompile — the skill's PDF recompile entrypoint.

Tests cover discovery and handoff manifest refresh; actual pdflatex invocation
is mocked so the suite stays portable.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import recompile  # noqa: E402


class TestResolveRunDir:
    def test_accepts_explicit_directory(self, tmp_path):
        assert recompile.resolve_run_dir(str(tmp_path)) == tmp_path.resolve()

    def test_rejects_missing_run(self):
        with pytest.raises(FileNotFoundError):
            recompile.resolve_run_dir("definitely-does-not-exist-1234")


class TestDiscoverTexFile:
    def test_picks_only_tex_file(self, tmp_path):
        (tmp_path / "resume.tex").write_text("\\documentclass{article}\n")
        assert recompile.discover_tex_file(tmp_path, None).name == "resume.tex"

    def test_skips_fix_candidates(self, tmp_path):
        (tmp_path / "resume.tex").write_text("\\documentclass{article}\n")
        (tmp_path / "resume.fix1.tex").write_text("garbage")
        assert recompile.discover_tex_file(tmp_path, None).name == "resume.tex"

    def test_requires_explicit_source_when_ambiguous(self, tmp_path):
        (tmp_path / "resume.tex").write_text("a")
        (tmp_path / "magazine.tex").write_text("b")
        with pytest.raises(RuntimeError):
            recompile.discover_tex_file(tmp_path, None)

    def test_explicit_source_picks_match(self, tmp_path):
        (tmp_path / "resume.tex").write_text("a")
        (tmp_path / "magazine.tex").write_text("b")
        assert recompile.discover_tex_file(tmp_path, "magazine").name == "magazine.tex"


class TestUpdateHandoff:
    def test_no_op_when_manifest_missing(self, tmp_path):
        recompile.update_handoff(tmp_path, tmp_path / "x.pdf")
        assert not (tmp_path / "handoff.json").exists()

    def test_refreshes_pdf_state(self, tmp_path):
        manifest_path = tmp_path / "handoff.json"
        manifest_path.write_text(json.dumps({"pdf_exists": False, "pdf_path": ""}))
        pdf_path = tmp_path / "resume.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake")

        with patch.object(recompile, "count_pdf_pages", return_value=2):
            recompile.update_handoff(tmp_path, pdf_path)

        manifest = json.loads(manifest_path.read_text())
        assert manifest["pdf_exists"] is True
        assert manifest["page_count"] == 2
        assert "last_recompile" in manifest


class TestRecompileFlow:
    def test_calls_compiler_and_returns_pdf_path(self, tmp_path):
        tex_path = tmp_path / "resume.tex"
        tex_path.write_text("\\documentclass{article}\n\\begin{document}hi\\end{document}\n")

        with patch("tools.recompile.PDFCompiler") as MockCompiler:
            MockCompiler.return_value.compile.return_value = (True, "ok")
            success, message, pdf = recompile.recompile(
                str(tmp_path), content_source="resume", update_handoff_manifest=False
            )

        assert success is True
        assert message == "ok"
        assert pdf == tmp_path / "resume.pdf"
        MockCompiler.assert_called_once_with(output_dir=str(tmp_path.resolve()))
