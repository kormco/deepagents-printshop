"""
Sample Content Scaffold

When the pipeline is run from a directory that does not have
`artifacts/sample_content/<content_source>/` set up, this helper copies the
packaged sample content (text files only) into the user's CWD so the rest of
the pipeline (which expects CWD-relative paths) can proceed.

Images are not shipped in the wheel to keep package size small. Instead, this
module downloads them on demand from the GitHub repo on first run. Override the
ref with the PRINTSHOP_IMAGES_REF env var (defaults to "main").
"""

import os
import shutil
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List

# Packaged sample content lives next to the `tools/` package — see
# pyproject.toml [tool.hatch.build.targets.wheel] include patterns.
PACKAGED_SAMPLE_ROOT = Path(__file__).parent.parent / "artifacts" / "sample_content"

GITHUB_REPO = "kormco/deepagents-printshop"
DEFAULT_REF = "main"

# Image filenames per content type. Kept here (not in a manifest file) so the
# scaffold script remains self-contained. Update this when adding/removing
# sample images in artifacts/sample_content/<type>/images/.
IMAGE_BUNDLE: Dict[str, List[str]] = {
    "magazine": [
        "adoption_chart.png",
        "cost_comparison.png",
        "cover-image.jpg",
        "fake-barcode.png",
        "framework_comparison.png",
        "image2.jpg",
        "image3.png",
        "image4.jpg",
        "image5.png",
        "image6.jpg",
        "image7.png",
        "model_performance.png",
    ],
    "research_report": [
        "performance_comparison.png",
    ],
    "ieee_conference": [],
}


def ensure_sample_content(content_source: str, download_images: bool = True) -> Path:
    """Ensure ./artifacts/sample_content/<content_source>/ exists in CWD.

    If the CWD copy is missing, scaffold it from the packaged sample. If
    download_images is True, also fetches any missing images from GitHub.
    Returns the resolved CWD path. Raises FileNotFoundError if no sample is
    available (neither in CWD nor in the package).
    """
    cwd_path = Path("artifacts/sample_content") / content_source
    needs_scaffold = not cwd_path.exists()

    if needs_scaffold:
        packaged_path = PACKAGED_SAMPLE_ROOT / content_source
        if not packaged_path.exists():
            raise FileNotFoundError(
                f"No sample content found for '{content_source}'. Looked in:\n"
                f"  - {cwd_path.resolve()} (CWD)\n"
                f"  - {packaged_path} (packaged)\n"
                f"Create artifacts/sample_content/{content_source}/ with a config.md "
                f"and section markdown files, or pick a content type that ships with "
                f"the package."
            )
        cwd_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(packaged_path, cwd_path)
        print(f"[scaffold] Initialized {cwd_path} from packaged sample.")

    if download_images:
        _download_missing_images(content_source, cwd_path / "images")

    return cwd_path


def _download_missing_images(content_source: str, images_dir: Path) -> None:
    """Download any images listed in IMAGE_BUNDLE that aren't already on disk."""
    expected = IMAGE_BUNDLE.get(content_source, [])
    if not expected:
        return

    images_dir.mkdir(parents=True, exist_ok=True)
    missing = [name for name in expected if not (images_dir / name).exists()]
    if not missing:
        return

    ref = os.environ.get("PRINTSHOP_IMAGES_REF", DEFAULT_REF)
    base_url = (
        f"https://raw.githubusercontent.com/{GITHUB_REPO}/{ref}/"
        f"artifacts/sample_content/{content_source}/images"
    )
    print(f"[scaffold] Downloading {len(missing)} sample image(s) for '{content_source}' from {GITHUB_REPO}@{ref}...")

    failures = []
    for name in missing:
        url = f"{base_url}/{name}"
        target = images_dir / name
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "deepagents-printshop-scaffold"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(target, "wb") as fh:
                shutil.copyfileobj(resp, fh)
            print(f"  ok  {name} ({target.stat().st_size:,} bytes)")
        except (urllib.error.URLError, OSError) as e:
            failures.append((name, str(e)))
            print(f"  err {name}: {e}")
            if target.exists():
                target.unlink()

    if failures:
        print(
            f"[scaffold] {len(failures)} image(s) failed to download. The pipeline will "
            f"continue but figures referencing them will be broken. Re-run with network "
            f"access, or copy them manually from "
            f"https://github.com/{GITHUB_REPO}/tree/{ref}/artifacts/sample_content/{content_source}/images"
        )
