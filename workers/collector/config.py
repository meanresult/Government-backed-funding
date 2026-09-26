"""Validated source configuration loading."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


def load_source_config(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("source config must be a YAML mapping")
    required = {"source_id", "institution_name", "start_url", "allowed_hosts", "adapter", "storage", "limits"}
    missing = sorted(required - value.keys())
    if missing:
        raise ValueError(f"source config missing fields: {', '.join(missing)}")
    if value["source_id"] != "semas_ols_notice" or value["adapter"] != "semas_ols_notice":
        raise ValueError("only the registered semas_ols_notice adapter is enabled")
    if not isinstance(value["allowed_hosts"], list) or not value["allowed_hosts"]:
        raise ValueError("allowed_hosts must be a non-empty list")
    storage = value["storage"]
    if not isinstance(storage, dict) or not storage.get("s3_bucket"):
        raise ValueError("storage.s3_bucket is required")
    return value


def config_hash(config: dict[str, Any]) -> str:
    payload = json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
