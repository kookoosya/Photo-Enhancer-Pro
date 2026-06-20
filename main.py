"""Photo Enhancer Pro — main entry point."""

from __future__ import annotations

import argparse
import sys

from utils import setup_logging


def main(argv: list[str] | None = None) -> int:
    """Application entry point."""
    parser = argparse.ArgumentParser(description="Photo Enhancer Pro")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    parser.add_argument("--port", type=int, default=7860, help="GUI server port")
    parser.add_argument("--share", action="store_true", help="Create public Gradio link")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    args, remaining = parser.parse_known_args(argv)

    level = __import__("logging").DEBUG if args.verbose else __import__("logging").INFO
    setup_logging(level=level)

    if args.cli or remaining:
        from cli import main as cli_main
        return cli_main(remaining if remaining else None)

    from gui import launch_gui
    launch_gui(share=args.share, server_port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
