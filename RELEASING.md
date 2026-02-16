# Releasing deepagents-printshop

## Prerequisites

Install the build and publish tools:

```bash
pip install build twine
```

You'll need a PyPI API token. Create one at https://pypi.org/manage/account/token/ and store it as:
- **Local**: `~/.pypirc` (see below)
- **GitHub Actions**: Repository secret `PYPI_API_TOKEN`

```ini
# ~/.pypirc (for manual uploads only — never commit this)
[pypi]
username = __token__
password = pypi-YOUR-TOKEN-HERE
```

## Automated Release (Recommended)

Push a version tag and GitHub Actions handles the rest:

```bash
# 1. Update version in pyproject.toml
#    e.g., version = "0.2.0"

# 2. Commit the version bump
git add pyproject.toml
git commit -m "Bump version to 0.2.0"

# 3. Tag and push
git tag v0.2.0
git push origin main --tags
```

The `publish.yml` workflow will:
1. Run lint and tests
2. Build the sdist and wheel
3. Run the filesize and content checks
4. Publish to PyPI

If any check fails, the release is aborted and nothing is uploaded.

## Manual Release

### Step 1 — Version Bump

Edit `pyproject.toml`:

```toml
version = "0.2.0"
```

Follow [semver](https://semver.org/):
- **Patch** (0.1.1 → 0.1.2): Bug fixes, doc updates
- **Minor** (0.1.1 → 0.2.0): New features, new content types, pipeline improvements
- **Major** (0.1.1 → 1.0.0): Breaking API/CLI changes

### Step 2 — Rewrite README Links for PyPI

The README uses relative links (e.g., `deepagents-printshop-SAMPLE-research_report.pdf`) so they work when browsing the repo on any branch. PyPI can't resolve relative links, so they must be rewritten to absolute GitHub URLs before building.

Run the helper script:

```bash
python scripts/pypi_readme.py
```

This rewrites links in `README.md` like:
| Relative (repo) | Absolute (PyPI) |
|---|---|
| `deepagents-printshop-SAMPLE-research_report.pdf` | `https://raw.githubusercontent.com/kormco/deepagents-printshop/main/deepagents-printshop-SAMPLE-research_report.pdf` |
| `docs/pipeline-walkthrough/PIPELINE_WALKTHROUGH.md` | `https://github.com/kormco/deepagents-printshop/blob/main/docs/pipeline-walkthrough/PIPELINE_WALKTHROUGH.md` |

**Important:** Do NOT commit the rewritten README. The build reads it, then you restore the original:

```bash
python scripts/pypi_readme.py   # rewrite for PyPI
python -m build                  # build reads absolute URLs
git checkout README.md           # restore relative URLs
```

The automated workflow handles this automatically.

### Step 3 — Clean Build

```bash
rm -rf dist/ build/ *.egg-info
python -m build
```

This produces two files in `dist/`:
- `deepagents_printshop-0.2.0.tar.gz` (sdist)
- `deepagents_printshop-0.2.0-py3-none-any.whl` (wheel)

### Step 4 — Filesize Check

The wheel must stay under **1 MB**. If it's larger, binary files leaked into the package.

```bash
# Quick size check
ls -lh dist/

# Detailed: list wheel contents and flag anything suspicious
unzip -l dist/*.whl | tail -20

# Verify no PDFs, PNGs, or large data files snuck in
unzip -l dist/*.whl | grep -iE '\.(pdf|png|jpg|csv|json)' && echo "WARNING: binary/data files in wheel!" || echo "OK: no binary files"
```

**Size guidelines:**
| Artifact | Expected | Max |
|----------|----------|-----|
| Wheel (.whl) | ~60-100 KB | 1 MB |
| Sdist (.tar.gz) | ~100-300 KB | 5 MB |

If the sdist is over 5 MB, sample content or images are leaking in. Check the `[tool.hatch.build.targets.sdist]` exclude list in `pyproject.toml`.

### Step 5 — Twine Check

```bash
twine check dist/*
```

This validates:
- Package metadata is well-formed
- README renders correctly on PyPI
- No missing required fields

### Step 6 — Test Upload (Optional)

Upload to TestPyPI first to verify everything looks right:

```bash
twine upload --repository testpypi dist/*

# Verify the page
# https://test.pypi.org/project/deepagents-printshop/
```

### Step 7 — Publish

```bash
twine upload dist/*
```

### Step 8 — Tag and Restore README

```bash
git tag v0.2.0
git push origin main --tags
```

## Pre-Release Checklist

Run through this before every release:

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Lint is clean: `ruff check .`
- [ ] Version bumped in `pyproject.toml`
- [ ] README links rewritten for PyPI: `python scripts/pypi_readme.py`
- [ ] `python -m build` succeeds
- [ ] Wheel is under 1 MB
- [ ] `twine check dist/*` passes
- [ ] No binary files in wheel (`unzip -l dist/*.whl`)
- [ ] Sdist is under 5 MB
- [ ] README restored after build: `git checkout README.md`
- [ ] Git working tree is clean
- [ ] Tagged with `v{version}`

## What Gets Packaged

**Included in wheel** (installed by `pip install`):
- `agents/` — Pipeline agents (orchestrator, content editor, latex specialist, visual QA)
- `tools/` — Shared tools (LaTeX generator, PDF compiler, content type loader, visual QA)

**Excluded from wheel:**
- `content_types/` — Type definitions (bundled separately or user-provided)
- `artifacts/` — Sample content, generated output, reports
- `*.pdf`, `*.png` — Sample documents and screenshots
- `tests/`, `docs/`, config files

**Excluded from sdist** (via pyproject.toml):
- `*.pdf` — Sample PDFs in project root
- `artifacts/output/` — Generated pipeline output
- `artifacts/reviewed_content/` — Intermediate versions
- `artifacts/agent_reports/` — Pipeline reports
- `dist/` — Previous builds

## Troubleshooting

**Wheel too large:**
Check `[tool.hatch.build.targets.wheel]` in `pyproject.toml`. Only `agents` and `tools` should be listed in `packages`.

**"File already exists" on upload:**
PyPI doesn't allow re-uploading the same version. Bump the version number.

**README doesn't render on PyPI:**
PyPI only supports a subset of markdown. Avoid HTML tags, relative image links, and complex tables. Run `twine check dist/*` to catch rendering issues before upload.

**Missing content_types at runtime:**
The `content_types/` directory is not packaged in the wheel. Users must either:
1. Clone the repo and run from source, or
2. Provide their own `content_types/` directory
This is by design — content types are configuration, not code.
