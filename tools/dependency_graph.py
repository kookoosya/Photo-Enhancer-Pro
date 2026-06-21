"""Dependency graph analysis tool."""

from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.common import (
    REPORTS_DIR,
    iter_python_files,
    module_name,
    parse_module,
    rel,
    utc_now_iso,
    write_json,
    write_text,
)


def _extract_imports(tree: ast.Module, current_module: str) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


def _is_internal(module: str) -> bool:
    internal_roots = {
        "app",
        "cli",
        "config",
        "core",
        "enhancer",
        "main",
        "noise",
        "pipeline",
        "processing",
        "segmentation",
        "styles",
        "ui",
        "upscale",
        "utils",
        "tools",
        "tests",
    }
    root = module.split(".")[0]
    return root in internal_roots


def build_dependency_graph() -> dict[str, object]:
    """Analyze imports and build dependency graph."""
    files = iter_python_files()
    edges: list[dict[str, str]] = []
    modules: dict[str, dict[str, object]] = {}
    external_deps: set[str] = set()
    internal_edges: defaultdict[str, set[str]] = defaultdict(set)

    for path in files:
        tree = parse_module(path)
        if tree is None:
            continue
        mod = module_name(path)
        imports = _extract_imports(tree, mod)
        modules[mod] = {
            "file": rel(path),
            "import_count": len(imports),
        }
        for imp in sorted(imports):
            if _is_internal(imp):
                internal_edges[mod].add(imp)
                edges.append({"source": mod, "target": imp, "type": "internal"})
            else:
                external_deps.add(imp)
                edges.append({"source": mod, "target": imp, "type": "external"})

    return {
        "generated_at": utc_now_iso(),
        "module_count": len(modules),
        "edge_count": len(edges),
        "external_dependencies": sorted(external_deps),
        "modules": modules,
        "edges": edges,
        "internal_adjacency": {k: sorted(v) for k, v in sorted(internal_edges.items())},
    }


def render_dot(report: dict[str, object]) -> str:
    """Render Graphviz DOT for internal dependencies."""
    lines = [
        "digraph dependencies {",
        '  rankdir=LR;',
        '  node [shape=box, style=rounded, fontname="Segoe UI"];',
    ]
    seen_nodes: set[str] = set()
    for edge in report["edges"]:
        if edge["type"] != "internal":
            continue
        src, dst = edge["source"], edge["target"]
        if src not in seen_nodes:
            lines.append(f'  "{src}";')
            seen_nodes.add(src)
        if dst not in seen_nodes:
            lines.append(f'  "{dst}";')
            seen_nodes.add(dst)
        lines.append(f'  "{src}" -> "{dst}";')
    lines.append("}")
    return "\n".join(lines)


def render_markdown(report: dict[str, object]) -> str:
    """Render dependency markdown report."""
    lines = [
        "# Dependency Graph Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        f"- Modules: **{report['module_count']}**",
        f"- Edges: **{report['edge_count']}**",
        "",
        "## External Dependencies",
        "",
    ]
    for dep in report["external_dependencies"]:
        lines.append(f"- `{dep}`")
    lines.extend(["", "## Internal Adjacency", ""])
    for mod, deps in report["internal_adjacency"].items():
        if not deps:
            continue
        lines.append(f"### `{mod}`")
        for dep in deps:
            lines.append(f"- → `{dep}`")
        lines.append("")
    lines.append("## Graphviz")
    lines.append("")
    lines.append("See `dependency_graph.dot` for visualization.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    """CLI entry for dependency graph tool."""
    report = build_dependency_graph()
    out_dir = REPORTS_DIR
    write_json(out_dir / "dependency_graph.json", report)
    write_text(out_dir / "dependency_graph.dot", render_dot(report))
    write_text(out_dir / "dependency_graph.md", render_markdown(report))
    print(f"Dependency graph written to {out_dir / 'dependency_graph.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
