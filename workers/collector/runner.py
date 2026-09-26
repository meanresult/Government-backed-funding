"""Collector orchestration and explicit local/S3 storage selection."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

from workers.collector.adapters.semas_ols_notice import collect_source
from workers.collector.config import config_hash, load_source_config
from workers.collector.storage import LocalStorage, S3Storage, StorageBackend, put_json


def _storage(config: dict[str, Any], mode: str) -> StorageBackend:
    settings = config["storage"]
    if mode == "local":
        return LocalStorage(Path(settings["local_root"]))
    return S3Storage(settings["s3_bucket"], settings["s3_region"], settings["s3_prefix"])


def run(
    *,
    config_path: Path,
    storage_mode: str,
    max_pages: int | None = None,
    max_notices: int | None = None,
    headed: bool = False,
    run_id: str | None = None,
) -> dict[str, Any]:
    config = load_source_config(config_path)
    settings = config["storage"]
    limits = config["limits"]
    run_id = run_id or f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    source_config_hash = config_hash(config)
    storage = _storage(config, storage_mode)
    max_pages = max_pages if max_pages is not None else limits.get("max_pages")
    max_notices = max_notices if max_notices is not None else limits.get("max_notices")
    timeout_ms = int(limits.get("navigation_timeout_ms", 30000))
    delay_ms = int(limits.get("request_delay_ms", 200))
    started_at = datetime.now(UTC).isoformat()
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    total_pages = 0

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not headed)
        page = browser.new_page(accept_downloads=True)
        page.set_default_timeout(timeout_ms)
        try:
            results, total_pages = collect_source(
                page,
                start_url=config["start_url"],
                allowed_hosts=set(config["allowed_hosts"]),
                storage=storage,
                source_prefix=settings["s3_prefix"],
                run_id=run_id,
                source_config_hash=source_config_hash,
                max_pages=max_pages,
                max_notices=max_notices,
                navigation_timeout_ms=timeout_ms,
                request_delay_ms=delay_ms,
            )
        except Exception as exc:
            errors.append({"type": type(exc).__name__, "message": str(exc), "url": page.url})
        finally:
            browser.close()

    failed_items = [item for item in results if item.get("status") == "FAILED"]
    if failed_items:
        errors.append({
            "type": "ItemFailures",
            "message": f"{len(failed_items)} notice(s) were not captured completely",
            "url": config["start_url"],
        })
    if max_pages is not None and total_pages > max_pages:
        errors.append({
            "type": "PageLimitReached",
            "message": f"discovered {total_pages} pages but collected only {max_pages}",
            "url": config["start_url"],
        })
    if max_notices is not None and len(results) >= max_notices:
        errors.append({
            "type": "NoticeLimitReached",
            "message": f"collected up to the configured notice limit of {max_notices}",
            "url": config["start_url"],
        })

    status = "COMPLETE" if not errors else "PARTIAL"
    manifest = {
        "metadata_schema_version": "1",
        "source_id": config["source_id"],
        "run_id": run_id,
        "storage_mode": storage_mode,
        "started_at": started_at,
        "finished_at": datetime.now(UTC).isoformat(),
        "source_config_hash": source_config_hash,
        "total_pages_discovered": total_pages,
        "requested_max_pages": max_pages,
        "requested_max_notices": max_notices,
        "status": status,
        "counts": {
            "total": len(results),
            "new": sum(item["status"] == "NEW" for item in results),
            "changed": sum(item["status"] == "CHANGED" for item in results),
            "unchanged": sum(item["status"] == "UNCHANGED" for item in results),
        },
        "results": results,
        "errors": errors,
    }
    put_json(storage, f"runs/{run_id}/manifest.json", manifest)
    return manifest
