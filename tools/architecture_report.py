"""Architecture analysis tool."""

from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.common import (
    PROJECT_ROOT,
    REPORTS_DIR,
    iter_python_files,
    module_name,
    parse_module,
    rel,
    utc_now_iso,
    write_json,
    write_text,
)

LAYER_MAP = {
    "ui": "Presentation (PySide6)",
    "app": "Application Layer",
    "core": "Core / DI",
    "processing": "Processing Pipeline",
    "segmentation": "Segmentation",
    "noise": "Noise Reduction",
    "upscale": "Upscaling",
    "styles": "Presets",
    "utils": "Utilities",
    "pipeline": "Batch Orchestration",
    "enhancer": "Enhancement Facade",
    "config": "Configuration",
    "cli": "CLI Entry",
    "main": "Main Entry",
    "tests": "Tests",
    "tools": "Analysis Tools",
}


def _layer_for_module(mod: str) -> str:
    root = mod.split(".")[0]
    return LAYER_MAP.get(root, "Other")


def _analyze_file(path) -> dict[str, object]:
    tree = parse_module(path)
    if tree is None:
        return {"classes": [], "functions": [], "lines": 0}
    classes: list[str] = []
    functions: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            functions.append(node.name)
    line_count = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    return {"classes": classes, "functions": functions, "lines": line_count}


def build_architecture_report() -> dict[str, object]:
    """Scan project and build architecture report."""
    files = iter_python_files()
    layers: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    total_lines = 0
    total_classes = 0
    total_functions = 0

    for path in files:
        mod = module_name(path)
        layer = _layer_for_module(mod)
        info = _analyze_file(path)
        total_lines += int(info["lines"])
        total_classes += len(info["classes"])
        total_functions += len(info["functions"])
        layers[layer].append(
            {
                "module": mod,
                "file": rel(path),
                "lines": info["lines"],
                "classes": info["classes"],
                "functions": info["functions"],
            }
        )

    layer_summary = {
        layer: {
            "modules": len(mods),
            "lines": sum(int(m["lines"]) for m in mods),
        }
        for layer, mods in sorted(layers.items())
    }

    return {
        "generated_at": utc_now_iso(),
        "project_root": rel(PROJECT_ROOT),
        "totals": {
            "files": len(files),
            "lines": total_lines,
            "classes": total_classes,
            "functions": total_functions,
            "layers": len(layers),
        },
        "layer_summary": layer_summary,
        "layers": {layer: mods for layer, mods in sorted(layers.items())},
    }


def render_markdown(report: dict[str, object]) -> str:
    """Render architecture markdown."""
    totals = report["totals"]
    lines = [
        "# Architecture Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Totals",
        "",
        f"- Python files: **{totals['files']}**",
        f"- Lines of code: **{totals['lines']}**",
        f"- Classes: **{totals['classes']}**",
        f"- Functions: **{totals['functions']}**",
        f"- Layers: **{totals['layers']}**",
        "",
        "## Layer Summary",
        "",
        "| Layer | Modules | Lines |",
        "|-------|---------|-------|",
    ]
    for layer, summary in report["layer_summary"].items():
        lines.append(f"| {layer} | {summary['modules']} | {summary['lines']} |")
    lines.append("")
    lines.append("## Module Inventory")
    lines.append("")
    for layer, mods in report["layers"].items():
        lines.append(f"### {layer}")
        lines.append("")
        for mod in mods:
            classes = ", ".join(f"`{c}`" for c in mod["classes"]) or "—"
            lines.append(f"- `{mod['module']}` ({mod['lines']} lines) — classes: {classes}")
        lines.append("")
    lines.extend(
        [
            "## Architecture Diagram",
            "",
            "```mermaid",
            "flowchart TB",
            "    UI[ui - PySide6] --> APP[app - Controller]",
            "    APP --> PIPE[pipeline - Batch]",
            "    PIPE --> ENH[enhancer - Facade]",
            "    ENH --> PROC[processing - Stages]",
            "    PROC --> SEG[segmentation]",
            "    PROC --> STY[styles]",
            "    CORE[core - DI] --> PROC",
            "    CORE --> SEG",
            "    UTILS[utils] --> PIPE",
            "    CONFIG[config] --> CORE",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    """CLI entry for architecture report."""
    report = build_architecture_report()
    out_dir = REPORTS_DIR
    write_json(out_dir / "architecture_report.json", report)
    write_text(out_dir / "architecture_report.md", render_markdown(report))
    print(f"Architecture report written to {out_dir / 'architecture_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
