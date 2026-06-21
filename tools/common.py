"""Shared utilities for project analysis tools."""

from __future__ import annotations

import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

SKIP_DIRS = {
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "dist",
    "venv",
    ".venv",
    "node_modules",
    "reports",
}


def ensure_reports_dir() -> Path:
    """Create reports directory if missing."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iter_python_files(root: Path | None = None) -> list[Path]:
    """Collect project Python source files."""
    base = root or PROJECT_ROOT
    files: list[Path] = []
    for path in sorted(base.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def rel(path: Path) -> str:
    """Return path relative to project root."""
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_source(path: Path) -> str:
    """Read file text with UTF-8 fallback."""
    return path.read_text(encoding="utf-8", errors="replace")


def parse_module(path: Path) -> ast.Module | None:
    """Parse Python file into AST."""
    try:
        return ast.parse(read_source(path), filename=str(path))
    except SyntaxError:
        return None


def module_name(path: Path) -> str:
    """Convert file path to dotted module name."""
    rel_path = path.relative_to(PROJECT_ROOT)
    parts = list(rel_path.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][:-3]
    return ".".join(parts)


def write_json(path: Path, data: object) -> None:
    """Write JSON report file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    """Write text report file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def add_project_root_to_path() -> None:
    """Ensure project root is importable."""
    root = str(PROJECT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
