"""Storage backends for local verification and S3 RAW persistence."""

from __future__ import annotations

import json
import mimetypes
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class StorageBackend(Protocol):
    def put_bytes(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> None: ...

    def get_bytes(self, key: str) -> bytes | None: ...

    def copy(self, source_key: str, destination_key: str) -> None: ...


def _content_type(key: str) -> str:
    return mimetypes.guess_type(key)[0] or "application/octet-stream"


@dataclass
class LocalStorage:
    root: Path

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        root = self.root.resolve()
        if path != root and root not in path.parents:
            raise ValueError(f"storage key escapes local root: {key}")
        return path

    def put_bytes(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> None:
        del content_type, tags
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def get_bytes(self, key: str) -> bytes | None:
        path = self._path(key)
        return path.read_bytes() if path.is_file() else None

    def copy(self, source_key: str, destination_key: str) -> None:
        source = self._path(source_key)
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = self._path(destination_key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


@dataclass
class S3Storage:
    bucket: str
    region: str
    prefix: str

    def __post_init__(self) -> None:
        import boto3

        self.client = boto3.client("s3", region_name=self.region)

    def _key(self, key: str) -> str:
        return f"{self.prefix.rstrip('/')}/{key.lstrip('/')}"

    def put_bytes(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> None:
        from urllib.parse import urlencode

        kwargs = {
            "Bucket": self.bucket,
            "Key": self._key(key),
            "Body": data,
            "ContentType": content_type or _content_type(key),
        }
        if tags:
            kwargs["Tagging"] = urlencode(tags)
        self.client.put_object(**kwargs)

    def get_bytes(self, key: str) -> bytes | None:
        from botocore.exceptions import ClientError

        try:
            response = self.client.get_object(Bucket=self.bucket, Key=self._key(key))
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in {"NoSuchKey", "404"}:
                return None
            raise
        return response["Body"].read()

    def copy(self, source_key: str, destination_key: str) -> None:
        self.client.copy_object(
            Bucket=self.bucket,
            Key=self._key(destination_key),
            CopySource={"Bucket": self.bucket, "Key": self._key(source_key)},
            MetadataDirective="COPY",
        )


def put_json(storage: StorageBackend, key: str, value: object, *, tags: dict[str, str] | None = None) -> None:
    storage.put_bytes(
        key,
        json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8"),
        content_type="application/json",
        tags=tags,
    )
