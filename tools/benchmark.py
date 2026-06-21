"""Performance benchmark tool."""

from __future__ import annotations

import statistics
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np

from tools.common import REPORTS_DIR, add_project_root_to_path, utc_now_iso, write_json, write_text


@dataclass
class BenchmarkResult:
    """Single benchmark measurement."""

    name: str
    seconds: float
    details: dict[str, object]


def _bench_enhance(size: tuple[int, int], iterations: int = 2) -> BenchmarkResult:
    add_project_root_to_path()
    from enhancer import ImageEnhancer
    from styles.iphone import IPHONE_PRO

    enhancer = ImageEnhancer(IPHONE_PRO)
    h, w = size
    image = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
    timings: list[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        enhancer.enhance(image)
        timings.append(time.perf_counter() - t0)
    elapsed = statistics.mean(timings)
    return BenchmarkResult(
        name=f"enhance_{w}x{h}",
        seconds=round(elapsed, 4),
        details={"width": w, "height": h, "iterations": iterations, "samples": timings},
    )


def _bench_stage_pipeline(iterations: int = 2) -> BenchmarkResult:
    add_project_root_to_path()
    from core.container import get_container
    from processing.context import ProcessingContext
    from styles.iphone import IPHONE_PRO

    container = get_container()
    pipeline = container.build_pipeline(IPHONE_PRO)
    image = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    timings: list[float] = []
    for _ in range(iterations):
        ctx = ProcessingContext(image=image.copy(), original=image.copy(), preset=IPHONE_PRO)
        t0 = time.perf_counter()
        pipeline.run(ctx)
        timings.append(time.perf_counter() - t0)
    elapsed = statistics.mean(timings)
    return BenchmarkResult(
        name="stage_pipeline_1280x720",
        seconds=round(elapsed, 4),
        details={"iterations": iterations, "samples": timings},
    )


def _bench_segmentation(iterations: int = 3) -> BenchmarkResult:
    add_project_root_to_path()
    from segmentation.segmenter import SceneSegmenter

    segmenter = SceneSegmenter()
    image = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
    timings: list[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        segmenter.segment(image)
        timings.append(time.perf_counter() - t0)
    elapsed = statistics.mean(timings)
    return BenchmarkResult(
        name="segmentation_800x600",
        seconds=round(elapsed, 4),
        details={"iterations": iterations, "samples": timings},
    )


def run_benchmarks() -> dict[str, object]:
    """Execute all benchmarks and return structured report."""
    results = [
        _bench_enhance((480, 640)),
        _bench_enhance((1080, 1920)),
        _bench_stage_pipeline(),
        _bench_segmentation(),
    ]
    total = round(sum(r.seconds for r in results), 4)
    return {
        "generated_at": utc_now_iso(),
        "total_seconds": total,
        "benchmarks": [asdict(r) for r in results],
    }


def render_markdown(report: dict[str, object]) -> str:
    """Render benchmark markdown."""
    lines = [
        "# Benchmark Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "| Benchmark | Seconds |",
        "|-----------|---------|",
    ]
    for item in report["benchmarks"]:
        lines.append(f"| {item['name']} | {item['seconds']:.4f} |")
    lines.extend(["", f"**Total:** {report['total_seconds']:.4f}s", ""])
    return "\n".join(lines)


def main() -> int:
    """CLI entry for benchmark tool."""
    report = run_benchmarks()
    out_dir = REPORTS_DIR
    write_json(out_dir / "benchmark.json", report)
    write_text(out_dir / "benchmark.md", render_markdown(report))
    print(f"Benchmark report written to {out_dir / 'benchmark.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
