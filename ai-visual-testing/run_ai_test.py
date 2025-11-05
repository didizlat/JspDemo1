import argparse
import os
import sys
from pathlib import Path

from src.utils.config import load_config
from src.utils.logging_setup import setup_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Visual Testing Framework (Phase 1.1 CLI stub)",
    )
    parser.add_argument(
        "--requirements",
        required=False,
        help="Path to a requirement file or glob (e.g., AIInputData/*.txt)",
    )
    parser.add_argument(
        "--provider",
        default="openai",
        help="AI provider (openai|claude|gemini|custom)",
    )
    parser.add_argument(
        "--config",
        default=str(Path(__file__).parent / "config" / "default.yaml"),
        help="Path to YAML config file",
    )
    parser.add_argument(
        "--output-dir",
        default="./test-reports",
        help="Directory for reports and artifacts",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser headless (overrides config)",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose logs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    setup_logging("DEBUG" if args.verbose else None)

    cfg = load_config(args.config)
    if args.headless:
        # Simple override at runtime
        os.environ["BROWSER_HEADLESS"] = "true"

    # Phase 1.1 stub: just echo what would run
    print("AI Visual Testing Framework – CLI Stub")
    print(f"Provider: {args.provider}")
    print(f"Requirements: {args.requirements}")
    print(f"Base URL: {cfg.get('testing.base_url')}")
    print(f"Output Dir: {args.output_dir}")
    print("Status: OK (Scaffold ready). Proceed to Phase 1.2 models.")
    return 0


if __name__ == "__main__":
    sys.exit(main())


