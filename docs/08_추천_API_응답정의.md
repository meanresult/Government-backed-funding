# 08. 추천 API 응답정의

> 적용 상태 (`2026-09-17`): 별도 추천 API 응답 구현은 후순위다. 아래 명세는 향후 웹서비스용 참고로 보존하며, 초기 대화 응답의 필수 JSON 계약으로 사용하지 않는다. 현재 답변 기준은 [15_대화형_정책자금_안내_전환계획.md](15_대화형_정책자금_안내_전환계획.md)를 따른다.

정책자금 추천 서비스에서 추천 엔진이 계산한 결과를 프론트 화면에 어떤 형태로 내려줄지 정의한 문서입니다. 이 문서는 `06_추천규칙_데이터모델.md`의 내부 판정 결과와 `07_서류안내_규칙정의.md`의 서류 조합 규칙을, 실제 화면 출력용 응답 구조로 번역한 개발 기준 문서입니다.

실제 엔드포인트, 요청 바디, 오류 응답, 처리 순서는 [09_추천_API_실제명세.md](/Users/jeehun/Documents/GitHub/Government-backed funding/docs/09_추천_API_실제명세.md)를 기준으로 합니다.

## 문서 개요

- 기준일: `2026-05-03`
- 기준 문서:
  - [06_추천규칙_데이터모델.md](/Users/jeehun/Documents/GitHub/Government-backed funding/docs/06_추천규칙_데이터모델.md)
  - [07_서류안내_규칙정의.md](/Users/jeehun/Documents/GitHub/Government-backed funding/docs/07_서류안내_규칙정의.md)
- 적용 대상:
  - 추천 결과 화면
  - 추천 API 응답
  - 추후 모바일/상담 화면 공통 결과 포맷
- 주 독자:
  - 개발

## 1. 문서 목적

이 문서는 아래 4가지를 고정하기 위해 만든다.

- 추천 결과 화면에 어떤 정보만 노출할지 정한다.
- `추천 자금명 + 간략한 추천 이유 + 자금 소개 토글 + 맞춤 제출서류 토글` 구조를 응답으로 고정한다.
- `신청 시 작성/동의`, `자동확인`, `기본 제출 권장`, `심사 후 또는 필요 시 제출`을 프론트가 그대로 그릴 수 있게 만든다.
- 내부 규칙 계산용 `bundle_id`를 사용자 노출용 문서 목록으로 어떻게 변환할지 정한다.
- 내부 정렬값인 `display_priority`는 추천 카드 순서를 정하는 데만 쓰고 사용자 응답에는 포함하지 않는다.

## 2. 응답 설계 원칙

- 결과 화면은 `추천 가능한 자금 카드 목록`만 보여준다.
- `탈락 사유`, `부적격 자금 목록`, `내부 판정 로그`는 사용자 응답에 포함하지 않는다.
- `display_priority`, `sort_weight` 같은 내부 정렬값이나 점수형 값은 사용자에게 보여주지 않는다.
- 각 카드 상단에는 `자금명`과 `간략한 추천 이유`만 먼저 보여준다.
- 추천 이유는 `summary_reason`과 `matched_reasons`로만 표현한다.
- 추천 이유가 아니라 신청 전 확인해야 할 안내는 `guidance_messages`로 분리한다.
- `자금명`을 누르면 카드 안에서 `간략 소개 토글`이 열려야 한다.
- 간략 소개 토글에는 `한 문단 설명`, `지원대상`, `특징`, `지원내용` 3개 요약 정보만 먼저 보여준다.
- `[상세보기]`를 누르면 해당 자금 소개 전용 페이지로 이동한다.
- `[맞춤 제출서류 보기]` 버튼을 누르면 토글 영역에서 상세 안내를 펼친다.
- 토글 영역은 `신청 시 작성/동의`, `자동확인`, `기본 제출 권장`, `심사 후 또는 필요 시 제출` 4개 블록으로 구성한다.
- `심사 후 또는 필요 시 제출` 블록에는 아래 안내 문구를 항상 함께 보여준다.  
  `아래 서류는 심사 후 추가서류로 분류되지만, 신청 시 함께 첨부하면 검토가 더 원활합니다.`
- 내부 추천 엔진은 `BASE-*`, `FUND-*`, `VAR-*` 묶음으로 계산하더라도, API 응답에는 실제 `문서명` 기준으로 펼쳐서 내려준다.

## 3. 화면 기준 응답 구조

추천 결과 화면은 아래 순서로 그린다.

1. 결과 메시지
2. 추천 자금 카드 목록
3. 카드 기본영역
설명: `자금명`, `세부유형명(있을 때)`, `간략한 추천 이유`
4. 자금 소개 토글영역
설명: `자금명` 클릭 시 노출. `한 문단 설명`, `지원대상`, `특징`, `지원내용`, `[상세보기]` 포함
5. 제출서류 토글영역
설명: `맞춤 제출서류 보기` 클릭 시 노출
6. 토글 내부 블록
설명: `신청 시 작성/동의`, `자동확인`, `기본 제출 권장`, `심사 후 또는 필요 시 제출`

즉, 사용자는 처음에는 “무슨 자금이 왜 추천됐는지”만 보고, 필요하면 자금 소개를 간략히 펼쳐본 뒤, 제출서류를 따로 확인하는 구조다.

## 4. 응답 정의

### 4.1 최상위 응답

| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `request_id` | string | 예 | 요청 추적용 ID |
| `generated_at` | string(datetime) | 예 | 추천 결과 생성 시각 |
| `result_message` | string | 예 | 추천 결과 요약 문구 |
| `recommended_funds` | array | 예 | 추천 자금 카드 목록 |

### 4.2 자금 카드 응답

| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `fund_code` | string | 예 | 내부 자금 식별코드 |
| `fund_name` | string | 예 | 사용자에게 보여줄 자금명 |
| `matched_variants` | array<object> | 예 | 매칭된 세부유형 목록. 세부유형이 없으면 빈 배열 |
| `recommendation_level` | string | 예 | `recommended` 또는 `review_needed` |
| `summary_reason` | string | 예 | 카드 상단에 한두 줄로 보여줄 간략한 추천 이유 |
| `matched_reasons` | array<string> | 예 | 추천 근거를 짧게 나열한 목록 |
| `guidance_messages` | array<string> | 예 | 추천 이유와 별도로 보여줄 신청 전 확인 안내. 없으면 빈 배열 |
| `detail_preview` | object | 예 | 자금명 클릭 시 토글로 보여줄 간략 소개 |
| `submission_guide` | object | 예 | 토글 시 보여줄 맞춤 제출서류 안내 |

### 4.3 매칭 세부유형 응답

| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `variant_code` | string | 예 | 세부유형 코드 |
| `variant_name` | string | 예 | 세부유형명 |
| `matched_reason` | string | 예 | 해당 세부유형이 매칭된 짧은 이유 |

같은 자금 안에서 여러 세부유형이 동시에 매칭될 수 있다. 예를 들어 `수출 여부 = 예`와 `로컬크리에이터 = 예`이면 `matched_variants`에 `수출유형`, `로컬크리에이터유형`을 모두 담는다.

### 4.4 자금 소개 토글 응답

| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `intro_paragraph` | string | 예 | 자금을 한 문단으로 간략히 소개하는 설명 |
| `quick_info_sections` | array<object> | 예 | 카드 안에서 먼저 보여줄 3개 요약 정보 |
| `detail_page_url` | string | 예 | `[상세보기]` 클릭 시 이동할 자금 소개 페이지 URL |

`quick_info_sections`는 기본적으로 아래 3개를 권장한다.

- `지원대상`
- `특징`
- `지원내용`

### 4.5 제출안내 응답

| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `application_steps` | array<string> | 예 | 신청 시 작성하거나 동의해야 하는 항목 |
| `auto_checks` | array<string> | 예 | 공공마이데이터·행정정보 공동이용 등으로 자동확인하는 항목 |
| `required_documents` | array<object> | 예 | 신청 단계에서 함께 준비하면 좋은 직접 제출 서류 |
| `review_documents_notice` | string | 예 | 심사 후 추가서류 안내 문구 |
| `review_documents` | array<object> | 예 | 심사 후 또는 필요 시 제출 서류 |

### 4.6 요약 정보 항목 응답

| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `title` | string | 예 | 예: `지원대상`, `특징`, `지원내용` |
| `text` | string | 예 | 해당 항목의 한두 줄 요약 |

### 4.7 문서 항목 응답

| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `doc_name` | string | 예 | 문서명 |
| `issuer` | string | 예 | 발급처 또는 보유 주체 |
| `issuance_method` | string | 예 | 발급방법 또는 제출방법 |
| `condition_note` | string or null | 아니오 | `법인인 경우`, `주된 사업장 기준` 같은 조건 메모 |
| `notes` | array<string> | 아니오 | 화면 보조 안내 문구 |

## 5. 응답 스키마

아래는 사용자 결과 화면용 권장 응답 스키마다.

```json
{
  "request_id": "string",
  "generated_at": "2026-05-03T15:00:00+09:00",
  "result_message": "입력 조건에 맞는 정책자금 2건을 찾았습니다.",
  "recommended_funds": [
    {
      "fund_code": "string",
      "fund_name": "string",
      "matched_variants": [
        {
          "variant_code": "string",
          "variant_name": "string",
          "matched_reason": "string"
        }
      ],
      "recommendation_level": "recommended",
      "summary_reason": "string",
      "matched_reasons": ["string"],
      "guidance_messages": ["string"],
      "detail_preview": {
        "intro_paragraph": "string",
        "quick_info_sections": [
          {
            "title": "지원대상",
            "text": "string"
          },
          {
            "title": "특징",
            "text": "string"
          },
          {
            "title": "지원내용",
            "text": "string"
          }
        ],
        "detail_page_url": "https://example.com/funds/innovation-growth"
      },
      "submission_guide": {
        "application_steps": ["string"],
        "auto_checks": ["string"],
        "required_documents": [
          {
            "doc_name": "string",
            "issuer": "string",
            "issuance_method": "string",
            "condition_note": "string or null",
            "notes": ["string"]
          }
        ],
        "review_documents_notice": "아래 서류는 심사 후 추가서류로 분류되지만, 신청 시 함께 첨부하면 검토가 더 원활합니다.",
        "review_documents": [
          {
            "doc_name": "string",
            "issuer": "string",
            "issuance_method": "string",
            "condition_note": "string or null",
            "notes": ["string"]
          }
        ]
      }
    }
  ]
}
```

## 6. 예시 응답

아래 예시는 `사업장 임차`, `법인`, `스마트기술 도입`, `NICE 839점 이하` 조건이 함께 들어온 상황을 가정한 응답 예시다.

```json
{
  "request_id": "rec_20260503_001",
  "generated_at": "2026-05-03T15:10:00+09:00",
  "result_message": "입력 조건에 맞는 정책자금 2건을 찾았습니다.",
  "recommended_funds": [
    {
      "fund_code": "innovation_growth",
      "fund_name": "혁신성장촉진자금",
      "matched_variants": [
        {
          "variant_code": "smart_tech",
          "variant_name": "스마트기술유형",
          "matched_reason": "스마트기술 도입 여부가 확인되었습니다."
        }
      ],
      "recommendation_level": "recommended",
      "summary_reason": "스마트기술 도입 여부가 확인되어 혁신성장촉진자금 스마트기술유형 검토가 가능합니다.",
      "matched_reasons": [
        "스마트기술 도입 여부가 확인되었습니다.",
        "사업장 임차 조건에 맞는 권리확인 서류 제출이 가능합니다."
      ],
      "guidance_messages": [],
      "detail_preview": {
        "intro_paragraph": "혁신성장촉진자금은 스마트기술 도입, 스마트공장 구축, 수출 등 성장성과 혁신성을 가진 소상공인의 사업 확장과 경쟁력 강화를 지원하는 자금입니다.",
        "quick_info_sections": [
          {
            "title": "지원대상",
            "text": "혁신형 성장 요소를 보유한 소상공인"
          },
          {
            "title": "특징",
            "text": "스마트기술, 수출, 로컬크리에이터 등 세부유형별로 심사 포인트가 다릅니다."
          },
          {
            "title": "지원내용",
            "text": "운전자금 또는 시설자금 검토가 가능하며 유형별 추가 증빙이 필요합니다."
          }
        ],
        "detail_page_url": "/funds/innovation-growth"
      },
      "submission_guide": {
        "application_steps": [
          "자금 신청서 작성",
          "사업계획 입력",
          "기업(신용)정보 동의",
          "개인(신용)정보 동의",
          "행정정보 공동이용 동의"
        ],
        "auto_checks": [
          "대표자 정보 자동확인",
          "사업자 등록정보 자동확인",
          "업종 정보 자동확인",
          "상시근로자 정보 자동확인",
          "세금 정보 자동확인",
          "주소 정보 자동확인"
        ],
        "required_documents": [
          {
            "doc_name": "사업장 임대차계약서",
            "issuer": "임대인·임차인 보유 계약서",
            "issuance_method": "체결한 계약서 사본 제출",
            "condition_note": "주된 사업장 기준",
            "notes": []
          },
          {
            "doc_name": "등기부등본",
            "issuer": "대법원 등기 민원 체계",
            "issuance_method": "인터넷등기소, 등기소 방문, 무인발급기 등으로 발급",
            "condition_note": "사업장 권리관계 확인용",
            "notes": []
          },
          {
            "doc_name": "거주주택 임대차계약서",
            "issuer": "임대인·임차인 보유 계약서",
            "issuance_method": "체결한 계약서 사본 제출",
            "condition_note": "대표자 또는 공동대표 거주형태 임차",
            "notes": []
          },
          {
            "doc_name": "법인 인감증명서",
            "issuer": "등기소 민원 체계",
            "issuance_method": "실무상 등기소 또는 발급 지원 무인발급기 이용",
            "condition_note": "법인인 경우",
            "notes": []
          },
          {
            "doc_name": "스마트설비 매매계약서",
            "issuer": "계약 당사자 보유 서류",
            "issuance_method": "계약서 사본 제출",
            "condition_note": "스마트기술유형",
            "notes": [
              "임차형이면 임차계약서로 대체 가능"
            ]
          },
          {
            "doc_name": "세금계산서",
            "issuer": "사업자 보유 자료",
            "issuance_method": "기발행 세금계산서 사본 제출",
            "condition_note": "스마트기술 도입 증빙",
            "notes": []
          }
        ],
        "review_documents_notice": "아래 서류는 심사 후 추가서류로 분류되지만, 신청 시 함께 첨부하면 검토가 더 원활합니다.",
        "review_documents": [
          {
            "doc_name": "최근 3개월 임차료 지급 이체확인증",
            "issuer": "거래은행",
            "issuance_method": "인터넷뱅킹, 모바일앱, 영업점에서 이체내역 또는 거래명세 발급",
            "condition_note": "사업장 임차",
            "notes": []
          },
          {
            "doc_name": "최근 3년 재무자료",
            "issuer": "국세청 또는 사업자 보유 자료",
            "issuance_method": "표준재무제표증명, 부가가치세과세표준증명 등 제출",
            "condition_note": "심사 단계 보강자료",
            "notes": []
          }
        ]
      }
    },
    {
      "fund_code": "credit_vulnerable",
      "fund_name": "신용취약소상공인자금",
      "matched_variants": [],
      "recommendation_level": "recommended",
      "summary_reason": "NICE 참고 기준 839점 이하 구간으로 확인되어 신용취약소상공인자금 검토가 가능합니다.",
      "matched_reasons": [
        "저신용 구간에 해당합니다.",
        "신용관리교육은 후속 보완으로 처리할 수 있습니다."
      ],
      "guidance_messages": [
        "신용관리교육은 빠르게 이수할 수 있으므로 추천은 가능하지만, 신청 전 이수 여부를 확인해주세요."
      ],
      "detail_preview": {
        "intro_paragraph": "신용취약소상공인자금은 신용 여건이 상대적으로 취약한 소상공인이 경영을 지속하고 정상화할 수 있도록 돕는 정책자금입니다.",
        "quick_info_sections": [
          {
            "title": "지원대상",
            "text": "저신용 구간에 해당하는 소상공인"
          },
          {
            "title": "특징",
            "text": "신용점수 구간이 핵심 판단 기준이며 교육 이수는 후속 보완으로 처리할 수 있습니다."
          },
          {
            "title": "지원내용",
            "text": "운전자금 중심으로 검토되며 신용 관련 보완자료가 추가될 수 있습니다."
          }
        ],
        "detail_page_url": "/funds/credit-vulnerable"
      },
      "submission_guide": {
        "application_steps": [
          "자금 신청서 작성",
          "기업(신용)정보 동의",
          "개인(신용)정보 동의"
        ],
        "auto_checks": [
          "대표자 정보 자동확인",
          "사업자 등록정보 자동확인",
          "세금 정보 자동확인"
        ],
        "required_documents": [],
        "review_documents_notice": "아래 서류는 심사 후 추가서류로 분류되지만, 신청 시 함께 첨부하면 검토가 더 원활합니다.",
        "review_documents": [
          {
            "doc_name": "신용관리교육 이수확인",
            "issuer": "교육 운영기관",
            "issuance_method": "이수확인 자료 제출",
            "condition_note": "후속 보완 가능",
            "notes": []
          }
        ]
      }
    }
  ]
}
```

## 7. 내부 규칙 모델과의 연결

- `06_추천규칙_데이터모델.md`는 어떤 자금을 추천할지 판단한다.
- `07_서류안내_규칙정의.md`는 어떤 서류를 어떤 묶음과 시점으로 보여줄지 정한다.
- 본 문서는 위 두 결과를 프론트가 바로 쓸 수 있는 `화면 출력용 JSON`으로 바꾼다.
- 자금 소개 한 문단과 요약 정보 3칸도 본 문서 응답에 포함한다.

즉, 내부 계산은 아래처럼 진행된다.

1. 추천 엔진이 추천 자금과 세부유형을 계산한다.
2. 추천 엔진이 내부 정렬값인 `display_priority`로 추천 카드 표시 순서를 정한다.
3. 서류 조합 엔진이 `BASE-*`, `FUND-*`, `VAR-*` 묶음을 계산한다.
4. API 응답 변환기가 묶음을 실제 문서 목록으로 펼치고, 내부 정렬값은 제거한다.
5. 프론트는 `recommended_funds[]`만 받아 카드와 토글 UI를 그린다.

## 8. 응답에 넣지 않는 항목

이번 MVP 응답에서는 아래 항목을 사용자 응답에 넣지 않는다.

- 탈락 사유
- 부적격 자금 목록
- 내부 판정 점수
- 내부 정렬값인 `display_priority` 또는 `sort_weight`
- 내부 `bundle_id`
- 관리자 검토 로그

이 항목들은 운영자 화면이나 로그에서는 별도 보관할 수 있지만, 사용자 추천 결과 화면용 응답에는 포함하지 않는 것이 적절하다.

## 9. 구현 메모

- `[맞춤 제출서류 보기]` 버튼 라벨은 프론트 고정 문구로 두고, API는 실제 내용만 내려주는 편이 낫다.
- 자금명 클릭 시 열리는 소개 토글은 `detail_preview`만으로 그릴 수 있어야 한다.
- `[상세보기]` 링크는 프론트에서 하드코딩하지 말고 `detail_page_url`을 그대로 사용하는 편이 안전하다.
- `required_documents`와 `review_documents`는 이미 사용자 입력값이 반영된 결과여야 한다.
- 같은 문서가 여러 규칙에서 중복될 수 있으므로, API 응답 직전에 `doc_name` 기준 중복 제거가 필요하다.
- `review_documents`가 비어 있어도 `review_documents_notice` 필드는 유지하는 편이 화면 구조를 단순하게 만든다.
- `recommendation_level = review_needed`인 자금도 같은 카드 UI를 쓰되, 배지나 보조문구만 다르게 처리하면 된다.
- 유형 관련 문장을 형광 배경으로 강조하는 기능은 추후 `detail_preview` 안에 강조 구간 정보를 추가해도 충분하다.
