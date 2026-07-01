"""
MkDocs hook: inject source-of-truth content into docs pages.

- Home page (index.md): rendered from README.md
- Category index pages: rendered from their category source files
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent
ISSUES_DIR = REPO_ROOT / "issues"


def _read_source(path: Path) -> str:
    """Read a markdown file, stripping the first h1 heading."""
    if not path.exists():
        return ""
    text = path.read_text()
    return re.sub(r"^#[^\n]*\n+", "", text)


def on_page_markdown(markdown, page, **kwargs):  # noqa: ARG001
    src = page.file.src_path

    # Home page: inject from README.md
    if src == "index.md":
        readme = (REPO_ROOT / "README.md").read_text()
        readme = re.sub(r"^#[^\n]*\n+", "", readme)
        return readme

    # Troubleshooting category index: inject from issues/<category>/index.md if present
    parts = Path(src).parts
    if len(parts) >= 2 and parts[0] == "troubleshooting":
        issue_src = ISSUES_DIR / Path(*parts[1:])
        if issue_src.exists():
            return issue_src.read_text()

    return markdown
