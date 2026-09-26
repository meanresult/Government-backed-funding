import unittest

from workers.collector.adapters.semas_ols_notice import (
    NoticeSummary,
    _content_hash,
    classify_notice,
    extract_detail_text,
    parse_attachments,
    parse_notice_rows,
    safe_filename,
)


LIST_HTML = """
<table><tbody id="resultList">
<tr><td>407</td><td>대리대출</td><td>대출정보</td>
<td><a onclick="fnGoModNoti(407,01); return false;">접수 안내</a></td><td>2026-09-11</td></tr>
</tbody></table>
<a onclick="fnSearch(1); return false;">1</a>
<a onclick="fnSearch(2); return false;">2</a>
"""


DETAIL_HTML = """
<div id="cntnDiv"><p>본문 첫 줄</p><p>본문 둘째 줄</p></div>
<a onclick="fnDownFile(1); return false;">자료.pdf</a>
"""


class SemasNoticeParserTest(unittest.TestCase):
    def test_parse_notice_rows(self):
        rows = parse_notice_rows(LIST_HTML)
        self.assertEqual(rows[0].source_record_id, "407")
        self.assertEqual(rows[0].bbs_type_code, "01")
        self.assertEqual(rows[0].title, "접수 안내")


    def test_parse_detail_text_and_attachment(self):
        self.assertEqual(extract_detail_text(DETAIL_HTML), "본문 첫 줄\n본문 둘째 줄")
        attachments = parse_attachments(DETAIL_HTML, "https://ols.semas.or.kr/detail")
        self.assertEqual(attachments[0].sequence, 1)
        self.assertEqual(attachments[0].filename, "자료.pdf")


    def test_safe_filename_removes_path_escape(self):
        self.assertEqual(safe_filename("../../비밀.txt", "fallback"), "비밀.txt")


    def test_content_hash_is_deterministic(self):
        summary = NoticeSummary("407", "01", "대리대출", "대출정보", "접수 안내", "2026-09-11")
        attachments = [{"artifact_id": "attachment_01", "original_filename": "자료.pdf", "sha256": "a"}]
        self.assertEqual(_content_hash(summary, "본문", attachments), _content_hash(summary, "본문", attachments))

    def test_retention_class_is_rule_based(self):
        summary = NoticeSummary("407", "01", "대리대출", "대출정보", "2026년 접수 안내", "2026-09-11")
        self.assertEqual(classify_notice(summary), ("application_current", "short"))
