"""SEMAS 정책자금 공지사항 전용 수집 어댑터.

원본 수집만 담당하며, 자격 조건·금리·한도 같은 정책 해석은 하지 않는다.
"""

from __future__ import annotations

# 표준 라이브러리: 해시 계산, 파일명 정리, 시간·임시 파일 처리
import hashlib
import html
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from urllib.parse import urlparse

# 외부 라이브러리: HTML 분석과 실제 브라우저 자동화
from bs4 import BeautifulSoup
from playwright.sync_api import Page, Response

from workers.collector.storage import StorageBackend, put_json


# 사이트의 JavaScript 함수에서 게시물 번호와 첨부파일 번호를 추출한다.
ADAPTER_VERSION = "semas_ols_notice_v1"
DETAIL_PATTERN = re.compile(
    r"fnGoModNoti\(\s*([^,]+)\s*,\s*['\"]?([^,'\")\s]+)['\"]?"
)
DOWNLOAD_PATTERN = re.compile(r"fnDownFile\(\s*(\d+)\s*\)")


# 목록 화면에서 확인한 게시물의 핵심 필드
@dataclass(frozen=True)
class NoticeSummary:
    source_record_id: str
    bbs_type_code: str
    loan_type: str
    category: str
    title: str
    registered_date: str


# 상세 화면에서 확인한 첨부파일 정보
@dataclass(frozen=True)
class AttachmentRef:
    sequence: int
    filename: str
    source_url: str | None = None


def sha256(data: bytes) -> str:
    # 원본 바이트가 같은지 비교하기 위한 SHA-256 해시를 만든다.
    return hashlib.sha256(data).hexdigest()


def safe_filename(name: str, fallback: str) -> str:
    # 경로 탈출 문자와 제어 문자를 제거해 안전한 저장 파일명을 만든다.
    cleaned = Path(html.unescape(name or "")).name
    cleaned = re.sub(r"[\x00-\x1f\x7f]+", "_", cleaned).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or fallback


def parse_notice_rows(markup: str) -> list[NoticeSummary]:
    # 목록 HTML에서 게시물 번호·구분·제목·등록일을 읽는다.
    soup = BeautifulSoup(markup, "html.parser")
    results: list[NoticeSummary] = []
    for row in soup.select("#resultList tr"):
        # 표의 셀 순서는 번호, 대출구분, 구분, 제목, 등록일이다.
        cells = [cell.get_text(" ", strip=True) for cell in row.select("td")]
        link = row.select_one("a[onclick*='fnGoModNoti']")
        if len(cells) < 5 or link is None:
            continue
        # 상세 페이지 이동 함수의 인자에서 사이트 게시물 ID와 게시판 코드를 얻는다.
        match = DETAIL_PATTERN.search(link.get("onclick", ""))
        if not match:
            continue
        results.append(
            NoticeSummary(
                source_record_id=match.group(1).strip(),
                bbs_type_code=match.group(2).strip(),
                loan_type=cells[1],
                category=cells[2],
                title=link.get_text(" ", strip=True),
                registered_date=cells[4],
            )
        )
    return results


def parse_attachments(markup: str, base_url: str) -> list[AttachmentRef]:
    # 상세 HTML에서 첨부파일 다운로드 함수와 파일명을 찾는다.
    del base_url
    soup = BeautifulSoup(markup, "html.parser")
    attachments: list[AttachmentRef] = []
    for link in soup.select("a[onclick*='fnDownFile']"):
        match = DOWNLOAD_PATTERN.search(link.get("onclick", ""))
        if not match:
            continue
        href = link.get("href")
        source_url = href if href and not href.startswith("javascript:") else None
        attachments.append(
            AttachmentRef(
                sequence=int(match.group(1)),
                filename=safe_filename(link.get_text(" ", strip=True), f"attachment_{match.group(1)}"),
                source_url=source_url,
            )
        )
    return attachments


def extract_detail_text(markup: str) -> str:
    # 정책자금 공지 본문 영역만 텍스트로 추출한다.
    soup = BeautifulSoup(markup, "html.parser")
    content = soup.select_one("#cntnDiv")
    if content is None:
        raise ValueError("detail body #cntnDiv was not found")
    return content.get_text("\n", strip=True)


def _is_html_error(data: bytes) -> bool:
    # PDF 대신 로그인 페이지나 오류 HTML이 저장되는 상황을 차단한다.
    sample = data[:512].lstrip().lower()
    return sample.startswith(b"<!doctype html") or sample.startswith(b"<html") or b"<html" in sample


def _mime_type(filename: str) -> str:
    # S3에 저장할 때 사용할 기본 MIME 타입을 확장자로 결정한다.
    suffix = Path(filename).suffix.lower()
    return {
        ".pdf": "application/pdf",
        ".hwp": "application/x-hwp",
        ".hwpx": "application/hwp+zip",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".zip": "application/zip",
    }.get(suffix, "application/octet-stream")


def _artifact(artifact_id: str, role: str, key: str, data: bytes, **extra: Any) -> dict[str, Any]:
    # 파일 하나의 위치·크기·해시를 manifest 항목으로 만든다.
    return {
        "artifact_id": artifact_id,
        "role": role,
        "s3_key": key,
        "sha256": sha256(data),
        "size_bytes": len(data),
        "status": "COMPLETE",
        **extra,
    }


def _content_hash(summary: NoticeSummary, body: str, attachments: list[dict[str, Any]]) -> str:
    # 수집 시각을 제외하고 내용과 첨부가 바뀌었는지 비교할 해시를 만든다.
    payload = "\n".join(
        [
            summary.source_record_id,
            summary.bbs_type_code,
            summary.loan_type,
            summary.category,
            summary.title,
            summary.registered_date,
            body.strip(),
            *[
                f"{item['artifact_id']}|{item['original_filename']}|{item['sha256']}"
                for item in sorted(attachments, key=lambda x: x["artifact_id"])
            ],
        ]
    )
    return sha256(payload.encode("utf-8"))


def classify_notice(summary: NoticeSummary) -> tuple[str, str]:
    """Return a retention class without interpreting policy eligibility."""
    # 정책 해석이 아니라 보관 기간을 정하는 단순 규칙만 적용한다.
    title = summary.title
    if summary.category == "서비스안내":
        return "service_guide", "long"
    if "교육" in title:
        return "education", "long"
    if "공고" in title or "수정" in title:
        return "public_notice", "long"
    if "신청" in title or "접수" in title:
        return "application_current", "short"
    return "review_required", "review"


def _allowed_host(url: str, allowed_hosts: set[str]) -> bool:
    # 지정된 기관 도메인으로만 이동했는지 확인한다.
    return urlparse(url).hostname in allowed_hosts


def _page_count(markup: str) -> int:
    # 페이지 번호 링크를 읽어 전체 목록 페이지 수를 계산한다.
    soup = BeautifulSoup(markup, "html.parser")
    pages = []
    for link in soup.select("a[onclick*='fnSearch']"):
        match = re.search(r"fnSearch\(\s*(\d+)\s*\)", link.get("onclick", ""))
        if match:
            pages.append(int(match.group(1)))
    return max(pages, default=1)


def _open_list_page(page: Page, url: str, page_number: int, timeout_ms: int) -> None:
    # 목록을 열고 JavaScript 방식의 다음 페이지 이동이 끝날 때까지 기다린다.
    page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    page.wait_for_function(
        "document.querySelectorAll('#resultList tr').length > 0",
        timeout=timeout_ms,
    )
    if page_number == 1:
        return
    previous = page.locator("#resultList").inner_html()
    page.locator(f"a[onclick*='fnSearch({page_number})']").click()
    page.wait_for_function(
        "old => document.querySelector('#resultList')?.innerHTML !== old && "
        "document.querySelectorAll('#resultList tr').length > 0",
        previous,
        timeout=timeout_ms,
    )


def collect_notice(
    page: Page,
    summary: NoticeSummary,
    *,
    requested_url: str,
    allowed_hosts: set[str],
    storage: StorageBackend,
    run_id: str,
    source_config_hash: str,
    navigation_timeout_ms: int,
    request_delay_ms: int,
) -> dict[str, Any]:
    # 목록의 한 게시물을 상세 페이지까지 들어가 원본 파일을 수집한다.
    detail_link = page.locator(f"a[onclick*='fnGoModNoti({summary.source_record_id}']").first
    with page.expect_navigation(wait_until="domcontentloaded", timeout=navigation_timeout_ms) as navigation:
        detail_link.click()
    response: Response | None = navigation.value
    if not _allowed_host(page.url, allowed_hosts):
        raise ValueError(f"detail page redirected to a disallowed host: {page.url}")
    page.wait_for_selector("#cntnDiv", state="attached", timeout=navigation_timeout_ms)

    # 서버 응답 HTML과 브라우저 렌더링 후 DOM을 각각 보존한다.
    source_html = response.body() if response is not None else page.content().encode("utf-8")
    rendered_html = page.content().encode("utf-8")
    body = extract_detail_text(rendered_html.decode("utf-8", errors="replace"))
    attachment_refs = parse_attachments(rendered_html.decode("utf-8", errors="replace"), page.url)
    snapshot_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{sha256(rendered_html)[:12]}"
    current_prefix = f"records/announcement_{summary.source_record_id}/current"

    files: list[tuple[str, bytes, str]] = [
        (f"{current_prefix}/source.html", source_html, "text/html; charset=utf-8"),
        (f"{current_prefix}/rendered.html", rendered_html, "text/html; charset=utf-8"),
        (f"{current_prefix}/extracted_text.txt", body.encode("utf-8"), "text/plain; charset=utf-8"),
    ]
    attachment_metadata: list[dict[str, Any]] = []

    # 첨부파일은 임시 파일로 받은 뒤 검증하고 S3/로컬 저장 대상으로 넘긴다.
    with TemporaryDirectory(prefix="semas_download_") as temp_dir:
        for attachment in attachment_refs:
            locator = page.locator(f"a[onclick*='fnDownFile({attachment.sequence})']").first
            with page.expect_download(timeout=navigation_timeout_ms) as download_info:
                locator.click()
            download = download_info.value
            target = Path(temp_dir) / safe_filename(download.suggested_filename or attachment.filename, attachment.filename)
            download.save_as(str(target))
            data = target.read_bytes()
            if not data or _is_html_error(data):
                raise ValueError(f"attachment download was empty or HTML: {attachment.filename}")
            filename = safe_filename(attachment.filename or target.name, f"attachment_{attachment.sequence}")
            key = f"{current_prefix}/attachments/{filename}"
            files.append((key, data, _mime_type(filename)))
            attachment_metadata.append(
                {
                    "artifact_id": f"attachment_{attachment.sequence:02d}",
                    "original_filename": filename,
                    "source_url": attachment.source_url,
                    "sha256": sha256(data),
                    "size_bytes": len(data),
                    "status": "COMPLETE",
                }
            )
            time.sleep(request_delay_ms / 1000)

    # 이전 current와 비교해 새 버전이 필요한지 먼저 판단한다.
    content_hash = _content_hash(summary, body, attachment_metadata)
    notice_type, retention_class = classify_notice(summary)
    previous_metadata_raw = storage.get_bytes(f"{current_prefix}/metadata.json")
    previous_metadata = json_loads(previous_metadata_raw) if previous_metadata_raw else None
    if previous_metadata and previous_metadata.get("content_hash") == content_hash:
        return {
            "announcement_id": f"announcement_{summary.source_record_id}",
            "source_record_id": summary.source_record_id,
            "status": "UNCHANGED",
            "content_hash": content_hash,
            "previous_snapshot_id": previous_metadata.get("snapshot_id"),
        }

    # 내용이 바뀌었다면 기존 current를 history로 복사해 보존한다.
    previous_snapshot_id = previous_metadata.get("snapshot_id") if previous_metadata else None
    if previous_snapshot_id:
        for artifact in previous_metadata.get("artifacts", []):
            old_key = artifact.get("s3_key")
            if old_key:
                history_key = old_key.replace(
                    f"{current_prefix}/",
                    f"records/announcement_{summary.source_record_id}/history/{previous_snapshot_id}/",
                    1,
                )
                storage.copy(old_key, history_key)

    # 원본 파일을 먼저 저장하고 마지막에 COMPLETE metadata를 저장한다.
    artifacts: list[dict[str, Any]] = []
    for key, data, content_type in files:
        is_attachment = "/attachments/" in key
        if is_attachment:
            attachment_name = Path(key).name
            artifact_id = next(
                item["artifact_id"]
                for item in attachment_metadata
                if item["original_filename"] == attachment_name
            )
            role = "attachment"
            extra = {
                "original_filename": attachment_name,
                "mime_type": content_type,
            }
        else:
            artifact_id = Path(key).name
            role = Path(key).stem
            extra = {"mime_type": content_type}
        artifacts.append(_artifact(artifact_id, role, key, data, **extra))
        storage.put_bytes(key, data, content_type=content_type, tags={"RetentionClass": retention_class})

    # 후속 가공 Agent가 읽을 운영 메타데이터와 완료 상태를 만든다.
    metadata = {
        "metadata_schema_version": "1",
        "source_id": "semas_ols_notice",
        "institution_name": "소상공인시장진흥공단",
        "announcement_id": f"announcement_{summary.source_record_id}",
        "source_record_id": summary.source_record_id,
        "identity_method": "site_notice_number",
        "bbs_type_code": summary.bbs_type_code,
        "loan_type": summary.loan_type,
        "category": summary.category,
        "title": summary.title,
        "registered_date": summary.registered_date,
        "notice_type": notice_type,
        "retention_class": retention_class,
        "requested_url": requested_url,
        "final_url": page.url,
        "run_id": run_id,
        "snapshot_id": snapshot_id,
        "previous_snapshot_id": previous_snapshot_id,
        "collected_at": datetime.now(UTC).isoformat(),
        "collector_version": ADAPTER_VERSION,
        "source_config_hash": source_config_hash,
        "content_hash": content_hash,
        "capture_status": "COMPLETE",
        "errors": [],
        "artifacts": artifacts,
    }
    put_json(storage, f"{current_prefix}/metadata.json", metadata, tags={"RetentionClass": retention_class})
    return {
        "announcement_id": metadata["announcement_id"],
        "source_record_id": summary.source_record_id,
        "status": "NEW" if previous_metadata is None else "CHANGED",
        "snapshot_id": snapshot_id,
        "content_hash": content_hash,
    }


def json_loads(data: bytes) -> dict[str, Any]:
    # 저장된 metadata.json이 객체 형식인지 확인하며 읽는다.
    import json

    value = json.loads(data.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("metadata.json must contain an object")
    return value


def collect_source(
    page: Page,
    *,
    start_url: str,
    allowed_hosts: set[str],
    storage: StorageBackend,
    source_prefix: str,
    run_id: str,
    source_config_hash: str,
    max_pages: int | None,
    max_notices: int | None,
    navigation_timeout_ms: int,
    request_delay_ms: int,
) -> tuple[list[dict[str, Any]], int]:
    # 목록 전체를 순회하고 각 상세 게시물을 collect_notice에 전달한다.
    del source_prefix
    if not _allowed_host(start_url, allowed_hosts):
        raise ValueError(f"start_url host is not allowed: {start_url}")
    page.goto(start_url, wait_until="domcontentloaded", timeout=navigation_timeout_ms)
    page.wait_for_function(
        "document.querySelectorAll('#resultList tr').length > 0",
        timeout=navigation_timeout_ms,
    )
    # 현재 페이지의 pagination HTML에서 전체 페이지 수를 발견한다.
    total_pages = _page_count(page.content())
    pages_to_collect = min(total_pages, max_pages) if max_pages else total_pages
    results: list[dict[str, Any]] = []

    for page_number in range(1, pages_to_collect + 1):
        _open_list_page(page, start_url, page_number, navigation_timeout_ms)
        summaries = parse_notice_rows(page.content())
        for summary in summaries:
            # 운영 실행은 한도에 도달하면 더 이상 외부 요청을 보내지 않는다.
            if max_notices is not None and len(results) >= max_notices:
                return results, total_pages
            try:
                result = collect_notice(
                    page,
                    summary,
                    requested_url=start_url,
                    allowed_hosts=allowed_hosts,
                    storage=storage,
                    run_id=run_id,
                    source_config_hash=source_config_hash,
                    navigation_timeout_ms=navigation_timeout_ms,
                    request_delay_ms=request_delay_ms,
                )
            except Exception as exc:
                # 한 게시물 실패를 기록하고 다음 게시물은 계속 시도한다.
                result = {
                    "announcement_id": f"announcement_{summary.source_record_id}",
                    "source_record_id": summary.source_record_id,
                    "status": "FAILED",
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                }
            results.append(result)
            page.goto(start_url, wait_until="domcontentloaded", timeout=navigation_timeout_ms)
            page.wait_for_function(
                "document.querySelectorAll('#resultList tr').length > 0",
                timeout=navigation_timeout_ms,
            )
            time.sleep(request_delay_ms / 1000)
        time.sleep(request_delay_ms / 1000)
    return results, total_pages
