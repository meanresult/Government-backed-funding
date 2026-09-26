"""Run a verified collector with ``python -m workers.collector``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from workers.collector.runner import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect approved policy-funding RAW data.")
    parser.add_argument("--source", required=True, choices=["semas_ols_notice"])
    parser.add_argument("--storage", required=True, choices=["local", "s3"])
    parser.add_argument("--config", type=Path, default=Path("configs/sources/semas_ols_notice.yaml"))
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--max-notices", type=int, default=None)
    parser.add_argument("--headed", action="store_true", help="Show Chromium for local debugging.")
    parser.add_argument("--run-id", default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        manifest = run(
            config_path=args.config,
            storage_mode=args.storage,
            max_pages=args.max_pages,
            max_notices=args.max_notices,
            headed=args.headed,
            run_id=args.run_id,
        )
    except Exception as exc:
        print(f"collector failed before manifest creation: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if manifest["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
