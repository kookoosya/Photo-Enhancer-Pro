"""Master project report — runs all analysis tools."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Allow running as: python tools/project_report.py
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.architecture_report import build_architecture_report, render_markdown as arch_md
from tools.benchmark import render_markdown as bench_md, run_benchmarks
from tools.common import REPORTS_DIR, ensure_reports_dir, utc_now_iso, write_json, write_text
from tools.dependency_graph import build_dependency_graph, render_dot, render_markdown as dep_md
from tools.quality_report import build_quality_report, render_markdown as quality_md


def generate_project_report(skip_benchmark: bool = False) -> dict[str, object]:
    """Run all report generators and produce master summary."""
    ensure_reports_dir()
    started = time.perf_counter()
    sections: dict[str, object] = {}

    print("==> Architecture report")
    arch = build_architecture_report()
    write_json(REPORTS_DIR / "architecture_report.json", arch)
    write_text(REPORTS_DIR / "architecture_report.md", arch_md(arch))
    sections["architecture"] = {
        "files": arch["totals"]["files"],
        "lines": arch["totals"]["lines"],
        "layers": arch["totals"]["layers"],
    }

    print("==> Dependency graph")
    deps = build_dependency_graph()
    write_json(REPORTS_DIR / "dependency_graph.json", deps)
    write_text(REPORTS_DIR / "dependency_graph.dot", render_dot(deps))
    write_text(REPORTS_DIR / "dependency_graph.md", dep_md(deps))
    sections["dependencies"] = {
        "modules": deps["module_count"],
        "edges": deps["edge_count"],
        "external": len(deps["external_dependencies"]),
    }

    print("==> Quality report")
    quality = build_quality_report()
    write_json(REPORTS_DIR / "quality_report.json", quality)
    write_text(REPORTS_DIR / "quality_report.md", quality_md(quality))
    sections["quality"] = {
        "score": quality["quality_score"],
        "pytest_ok": quality["pytest"].get("ok"),
        "ruff_ok": quality["ruff"].get("ok"),
        "tests": quality["tests"],
    }

    if skip_benchmark:
        print("==> Benchmark skipped")
        sections["benchmark"] = {"skipped": True}
    else:
        print("==> Benchmark")
        bench = run_benchmarks()
        write_json(REPORTS_DIR / "benchmark.json", bench)
        write_text(REPORTS_DIR / "benchmark.md", bench_md(bench))
        sections["benchmark"] = {
            "total_seconds": bench["total_seconds"],
            "cases": len(bench["benchmarks"]),
        }

    elapsed = round(time.perf_counter() - started, 2)
    summary = {
        "generated_at": utc_now_iso(),
        "elapsed_seconds": elapsed,
        "sections": sections,
        "reports_dir": REPORTS_DIR.as_posix(),
        "status": "ok" if quality["pytest"].get("ok") else "degraded",
    }

    write_json(REPORTS_DIR / "project_report.json", summary)
    write_text(REPORTS_DIR / "PROJECT_REPORT.md", render_master_markdown(summary, sections))
    return summary


def render_master_markdown(summary: dict[str, object], sections: dict[str, object]) -> str:
    """Render master project report markdown."""
    arch = sections["architecture"]
    deps = sections["dependencies"]
    quality = sections["quality"]
    bench = sections.get("benchmark", {})

    lines = [
        "# Photo Enhancer Pro — Project Report",
        "",
        f"Generated: **{summary['generated_at']}**",
        f"Elapsed: **{summary['elapsed_seconds']}s**",
        f"Status: **{summary['status'].upper()}**",
        "",
        "## Summary",
        "",
        "| Area | Metric | Value |",
        "|------|--------|-------|",
        f"| Architecture | Python files | {arch['files']} |",
        f"| Architecture | Lines of code | {arch['lines']} |",
        f"| Architecture | Layers | {arch['layers']} |",
        f"| Dependencies | Modules | {deps['modules']} |",
        f"| Dependencies | External deps | {deps['external']} |",
        f"| Quality | Score | {quality['score']}/100 |",
        f"| Quality | Pytest | {'PASS' if quality['pytest_ok'] else 'FAIL'} |",
        f"| Quality | Ruff | {'PASS' if quality['ruff_ok'] else 'FAIL'} |",
        f"| Quality | Test functions | {quality['tests']['test_functions']} |",
    ]
    if bench.get("skipped"):
        lines.append("| Benchmark | Status | SKIPPED |")
    else:
        lines.append(f"| Benchmark | Total time | {bench.get('total_seconds', 0)}s |")
        lines.append(f"| Benchmark | Cases | {bench.get('cases', 0)} |")

    lines.extend(
        [
            "",
            "## Generated Reports",
            "",
            "- `reports/architecture_report.md`",
            "- `reports/dependency_graph.md`",
            "- `reports/dependency_graph.dot`",
            "- `reports/quality_report.md`",
            "- `reports/benchmark.md`",
            "- `reports/project_report.json`",
            "",
            "## Usage",
            "",
            "Run after every major change:",
            "",
            "```bash",
            "python tools/project_report.py",
            "```",
            "",
            "Options:",
            "",
            "```bash",
            "python tools/project_report.py --skip-benchmark",
            "python tools/project_report.py --benchmark-only",
            "python tools/project_report.py --quality-only",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    """CLI entry for master project report."""
    parser = argparse.ArgumentParser(description="Generate full Photo Enhancer Pro project report")
    parser.add_argument("--skip-benchmark", action="store_true", help="Skip performance benchmarks")
    parser.add_argument("--benchmark-only", action="store_true", help="Run only benchmarks")
    parser.add_argument("--quality-only", action="store_true", help="Run only quality report")
    parser.add_argument("--architecture-only", action="store_true", help="Run only architecture report")
    parser.add_argument("--dependencies-only", action="store_true", help="Run only dependency graph")
    args = parser.parse_args()

    if args.benchmark_only:
        from tools.benchmark import main as bench_main
        return bench_main()
    if args.quality_only:
        from tools.quality_report import main as quality_main
        return quality_main()
    if args.architecture_only:
        from tools.architecture_report import main as arch_main
        return arch_main()
    if args.dependencies_only:
        from tools.dependency_graph import main as dep_main
        return dep_main()

    summary = generate_project_report(skip_benchmark=args.skip_benchmark)
    print("")
    print(f"Project report complete -> {REPORTS_DIR / 'PROJECT_REPORT.md'}")
    print(json.dumps(summary["sections"], indent=2))
    return 0 if summary["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
