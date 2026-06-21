"""Code quality analysis tool."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.common import (
    PROJECT_ROOT,
    REPORTS_DIR,
    iter_python_files,
    rel,
    utc_now_iso,
    write_json,
    write_text,
)


def _function_has_type_hints(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    if node.returns is not None:
        return True
    return any(arg.annotation is not None for arg in node.args.args)


def _analyze_ast_quality(files: list[Path]) -> dict[str, object]:
    total_functions = 0
    typed_functions = 0
    documented_functions = 0
    documented_classes = 0
    total_classes = 0
    todo_count = 0
    pass_count = 0

    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_functions += 1
                if _function_has_type_hints(node):
                    typed_functions += 1
                if ast.get_docstring(node):
                    documented_functions += 1
            elif isinstance(node, ast.ClassDef):
                total_classes += 1
                if ast.get_docstring(node):
                    documented_classes += 1
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, str) and "TODO" in node.value.value.upper():
                    todo_count += 1
            elif isinstance(node, ast.Pass):
                pass_count += 1

    def pct(num: int, den: int) -> float:
        return round((num / den) * 100, 1) if den else 100.0

    return {
        "functions": total_functions,
        "classes": total_classes,
        "type_hint_coverage_pct": pct(typed_functions, total_functions),
        "function_doc_coverage_pct": pct(documented_functions, total_functions),
        "class_doc_coverage_pct": pct(documented_classes, total_classes),
        "todo_comments": todo_count,
        "pass_statements": pass_count,
    }


def _run_pytest() -> dict[str, object]:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no", "-m", "not performance"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=180,
        )
        return {
            "ok": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _run_ruff() -> dict[str, object]:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "ruff", "check", ".", "--ignore", "E501"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        issues = [line for line in proc.stdout.splitlines() if line.strip()]
        return {
            "ok": proc.returncode == 0,
            "exit_code": proc.returncode,
            "issue_count": len(issues),
            "issues": issues[:20],
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _count_tests() -> dict[str, int]:
    test_files = list((PROJECT_ROOT / "tests").glob("test_*.py"))
    test_functions = 0
    for path in test_files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test_"):
                    test_functions += 1
    return {"test_files": len(test_files), "test_functions": test_functions}


def build_quality_report() -> dict[str, object]:
    """Build code quality report."""
    source_files = [p for p in iter_python_files() if not rel(p).startswith("tests/")]
    test_stats = _count_tests()
    ast_quality = _analyze_ast_quality(source_files)
    pytest_result = _run_pytest()
    ruff_result = _run_ruff()

    score = 100
    if not pytest_result.get("ok"):
        score -= 30
    if not ruff_result.get("ok"):
        score -= 10
    if ast_quality["type_hint_coverage_pct"] < 70:
        score -= 10
    if ast_quality["function_doc_coverage_pct"] < 50:
        score -= 5
    if ast_quality["todo_comments"] > 0:
        score -= 5

    return {
        "generated_at": utc_now_iso(),
        "source_files": len(source_files),
        "tests": test_stats,
        "ast_quality": ast_quality,
        "pytest": pytest_result,
        "ruff": ruff_result,
        "quality_score": max(0, score),
    }


def render_markdown(report: dict[str, object]) -> str:
    """Render quality markdown."""
    aq = report["ast_quality"]
    tests = report["tests"]
    lines = [
        "# Quality Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        f"## Quality Score: **{report['quality_score']}/100**",
        "",
        "## Test Suite",
        "",
        f"- Test files: **{tests['test_files']}**",
        f"- Test functions: **{tests['test_functions']}**",
        f"- Pytest: **{'PASS' if report['pytest'].get('ok') else 'FAIL'}**",
    ]
    if report["pytest"].get("stdout"):
        lines.append(f"- Output: `{report['pytest']['stdout']}`")
    lines.extend(
        [
            "",
            "## Static Analysis",
            "",
            f"- Ruff: **{'PASS' if report['ruff'].get('ok') else 'FAIL'}**",
            f"- Ruff issues: **{report['ruff'].get('issue_count', 0)}**",
            "",
            "## Code Metrics",
            "",
            f"- Source files: **{report['source_files']}**",
            f"- Type hint coverage: **{aq['type_hint_coverage_pct']}%**",
            f"- Function docstrings: **{aq['function_doc_coverage_pct']}%**",
            f"- Class docstrings: **{aq['class_doc_coverage_pct']}%**",
            f"- TODO comments: **{aq['todo_comments']}**",
            f"- Pass statements: **{aq['pass_statements']}**",
            "",
        ]
    )
    if report["ruff"].get("issues"):
        lines.append("### Sample Ruff Issues")
        lines.append("")
        for issue in report["ruff"]["issues"][:10]:
            lines.append(f"- `{issue}`")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    """CLI entry for quality report."""
    report = build_quality_report()
    out_dir = REPORTS_DIR
    write_json(out_dir / "quality_report.json", report)
    write_text(out_dir / "quality_report.md", render_markdown(report))
    print(f"Quality report written to {out_dir / 'quality_report.md'}")
    return 0 if report["pytest"].get("ok") and report["ruff"].get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
