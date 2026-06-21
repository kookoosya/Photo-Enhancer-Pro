"""Command-line interface for Photo Enhancer Pro."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from config import get_config
from pipeline import ProcessingOptions, ProcessingPipeline
from styles import list_presets
from utils import setup_logging


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    config = get_config()
    parser = argparse.ArgumentParser(
        description="Photo Enhancer Pro — offline batch photo enhancement",
        prog="pep-cli",
    )
    parser.add_argument("input", type=Path, help="Input folder or ZIP archive")
    parser.add_argument("-o", "--output", type=Path, help="Output directory")
    parser.add_argument(
        "-p", "--preset",
        choices=list_presets(),
        default=config.default_preset,
        help="Enhancement preset",
    )
    parser.add_argument("--no-exif", action="store_true", help="Do not keep EXIF")
    parser.add_argument("--no-zip", action="store_true", help="Do not create ZIP")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    parser.add_argument("--upscale", action="store_true", help="Upscale images")
    parser.add_argument("--resize", type=int, default=0, help="Max dimension for resize")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--gui", action="store_true", help="Launch GUI instead")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.gui:
        from ui.app import run_app
        return run_app()

    level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level=level)

    if not args.input.exists():
        print(f"Error: Input not found: {args.input}", file=sys.stderr)
        return 1

    options = ProcessingOptions(
        preset_name=args.preset,
        output_dir=args.output,
        keep_exif=not args.no_exif,
        create_zip=not args.no_zip,
        overwrite_existing=args.overwrite,
        resize=args.resize > 0,
        resize_max=args.resize,
        upscale=args.upscale,
    )

    pipeline = ProcessingPipeline(options)

    def progress(info) -> None:
        pct = info.current / info.total * 100
        print(f"\r[{pct:5.1f}%] {info.filename} — ETA {info.estimated_remaining:.0f}s", end="")

    result = pipeline.run(args.input, progress_callback=progress)
    print()

    print(f"Processed: {result.processed}/{result.total}")
    print(f"Failed: {result.failed}")
    print(f"Output: {result.output_folder}")
    if result.zip_path:
        print(f"ZIP: {result.zip_path}")
    if result.errors:
        print("Errors:")
        for err in result.errors:
            print(f"  - {err}")

    return 0 if result.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
