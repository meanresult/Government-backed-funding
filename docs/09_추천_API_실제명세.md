# 09. 추천 API 실제명세

정책자금 추천 서비스에서 프론트엔드가 백엔드에 어떤 값을 보내고, 백엔드는 어떤 순서로 추천 결과와 맞춤 제출서류를 계산해 반환할지 정의한 실제 API 명세 문서입니다.

이 문서는 새로운 추천 정책을 만드는 문서가 아니라, [06_추천규칙_데이터모델.md](/Users/jeehun/Documents/GitHub/Government-backed funding/docs/06_추천규칙_데이터모델.md), [07_서류안내_규칙정의.md](/Users/jeehun/Documents/GitHub/Government-backed funding/docs/07_서류안내_규칙정의.md), [08_추천_API_응답정의.md](/Users/jeehun/Documents/GitHub/Government-backed funding/docs/08_추천_API_응답정의.md)를 실제 API 호출 규격으로 연결하는 개발 기준 문서입니다.

## 문서 개요

- 기준일: `2026-05-03`
- API 버전: `v1`
- 기준 규칙 버전: `2026-05`
- 주 독자:
  - 프론트엔드 개발자
  - 백엔드 개발자
  - 추천 엔진 구현 담당자
- 적용 범위:
  - 사용자 정책자금 추천 요청
  - 추천 결과 카드 생성
  - 맞춤 제출서류 안내 생성
- 제외 범위:
  - 관리자 문서 업로드 API
  - 관리자 승인/반려 API
  - 업종 검색 API 상세 명세
  - 자금 상세 페이지 CMS API

## 1. API 개요

| 항목 | 값 |
| --- | --- |
| Method | `POST` |
| URL | `/api/recommendations` |
| 인증 | 비로그인 가능 |
| Content-Type | `application/json` |
| 응답 형식 | `application/json` |
| 성공 상태코드 | `200 OK` |

사용자 추천 API는 개인정보 기반 로그인이나 사용자 식별을 전제로 하지 않는다. 요청값은 추천 평가에 필요한 구간값과 선택값만 받는다.

### 1.1 요청 헤더

| 헤더명 | 필수 | 설명 |
| --- | --- | --- |
| `Content-Type: application/json` | 예 | JSON 요청임을 표시 |
| `X-Request-Id` | 아니오 | 프론트에서 생성한 요청 추적용 ID. 없으면 서버가 생성 |

### 1.2 응답 헤더

| 헤더명 | 필수 | 설명 |
| --- | --- | --- |
| `X-Request-Id` | 예 | 요청 추적용 ID |
| `X-Api-Version` | 예 | 추천 API 버전. 예: `v1` |
| `X-Rule-Version` | 예 | 추천 규칙 버전. 예: `2026-05` |

`api_version`, `rule_version`은 운영 추적용 헤더로 내려주고, 사용자 화면용 응답 본문에는 포함하지 않는다.

## 2. 요청 바디 구조

요청 바디는 화면 입력값을 그대로 보내지 않고, 백엔드가 이해할 수 있는 정규화된 필드명으로 보낸다.

```json
{
  "applicant": {},
  "industry": {},
  "employment": {},
  "business_status": {},
  "credit": {},
  "business_site": {},
  "residence": {},
  "innovation_signals": {},
  "growth_signals": {},
  "special_conditions": {},
  "joint_representatives": [],
  "follow_up_answers": {}
}
```

### 2.1 최상위 필드

| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `applicant` | object | 예 | 사업자 형태, 체납 여부, 공동대표 여부 |
| `industry` | object | 예 | 업종 검색 선택 결과 |
| `employment` | object | 예 | 상시근로자 구간 |
| `business_status` | object | 예 | 휴폐업 이력, 매출 구간 |
| `credit` | object | 예 | NICE 신용점수 구간 |
| `business_site` | object | 예 | 사업장 점유 형태와 권리침해 여부 |
| `residence` | object | 예 | 대표자 거주 형태 |
| `innovation_signals` | object | 아니오 | 혁신성장 관련 선택값 |
| `growth_signals` | object | 아니오 | 온라인·플랫폼·성장 관련 선택값 |
| `special_conditions` | object | 아니오 | 홈플러스, 재난피해, 지정지역 등 특수 조건 |
| `joint_representatives` | array<object> | 조건부 | 공동대표가 있는 경우 대표자별 추가 정보 |
| `follow_up_answers` | object | 아니오 | 세부유형 확정용 후속 질문 답변 |

## 3. 요청 필드 정의

### 3.1 applicant

```json
{
  "business_entity_type": "corporation",
  "tax_delinquent": false,
  "has_joint_representative": true,
  "joint_representative_count": 2
}
```

| 필드명 | 타입 | 필수 | 허용값 | 설명 |
| --- | --- | --- | --- | --- |
| `business_entity_type` | enum | 예 | `individual`, `corporation` | 개인/법인 구분 |
| `tax_delinquent` | boolean | 예 | `true`, `false` | `true`는 국세·지방세 체납 있음 |
| `has_joint_representative` | boolean | 예 | `true`, `false` | 공동대표 여부 |
| `joint_representative_count` | integer | 조건부 | `1` 이상 | 공동대표가 있으면 입력 |

`tax_delinquent = true`는 유효한 입력값이지만 추천 결과는 비어 있을 수 있다. 사용자에게 체납 사유를 API 응답으로 자세히 노출하지 않고, 프론트 입력 단계에서 안내 문구를 보여주는 것을 기본으로 한다.

### 3.2 industry

```json
{
  "industry_code": "G47912",
  "industry_name": "전자상거래 소매업",
  "industry_level": "small",
  "standard_industry_name": "전자상거래 소매업",
  "is_excluded": false,
  "source": "external_api"
}
```

| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `industry_code` | string | 예 | 외부 업종 검색 결과의 업종 코드 |
| `industry_name` | string | 예 | 사용자에게 표시한 업종명 |
| `industry_level` | enum | 아니오 | `major`, `middle`, `small` |
| `standard_industry_name` | string | 아니오 | 표준산업분류 또는 내부 매핑명 |
| `is_excluded` | boolean | 예 | 제외업종 여부 |
| `source` | enum | 예 | `external_api`, `manual_override` |

업종 검색 자체는 별도 API에서 처리한다. 추천 API는 사용자가 최종 선택한 업종 객체만 받는다.

### 3.3 employment

```json
{
  "employee_band": "under_5"
}
```

| 필드명 | 타입 | 필수 | 허용값 | 설명 |
| --- | --- | --- | --- | --- |
| `employee_band` | enum | 예 | `under_5`, `five_to_nine`, `ten_or_more` | 상시근로자 구간 |

화면 표시값은 `5인 미만`, `5인 이상 10인 미만`, `10인 이상`으로 매핑한다.

### 3.4 business_status

```json
{
  "has_closure_history": false,
  "sales_band_y3": "none",
  "sales_band_y2": "50m_to_104m",
  "sales_band_y1": "104m_to_450m"
}
```

| 필드명 | 타입 | 필수 | 허용값 | 설명 |
| --- | --- | --- | --- | --- |
| `has_closure_history` | boolean | 예 | `true`, `false` | 폐업/휴폐업 이력 여부 |
| `sales_band_y3` | enum | 아니오 | `none`, `under_50m`, `50m_to_104m`, `104m_to_450m`, `450m_to_1500m`, `over_1500m` | 3년 전 매출 구간 |
| `sales_band_y2` | enum | 아니오 | 위와 동일 | 2년 전 매출 구간 |
| `sales_band_y1` | enum | 아니오 | 위와 동일 | 최근 연도 매출 구간 |

사업기간이 3년 미만이면 해당 연도 매출은 `none`으로 보낼 수 있다.

### 3.5 credit

```json
{
  "credit_score_band_nice": "800_839"
}
```

| 필드명 | 타입 | 필수 | 허용값 | 설명 |
| --- | --- | --- | --- | --- |
| `credit_score_band_nice` | enum | 예 | `unknown`, `below_700`, `700_749`, `750_799`, `800_839`, `840_899`, `900_or_more` | NICE 기준 참고 구간 |

신용취약소상공인자금은 운영 기준상 `below_700`, `700_749`, `750_799`, `800_839`이면 추천 후보로 본다. 실제 공식 심사는 NCB 기준을 별도로 확인해야 한다.

### 3.6 business_site

```json
{
  "occupancy_type": "leased",
  "has_right_issue": false,
  "deposit": 10000000,
  "monthly_rent": 700000,
  "uses_leased_business_vehicle_or_vessel": false
}
```

| 필드명 | 타입 | 필수 | 허용값 | 설명 |
| --- | --- | --- | --- | --- |
| `occupancy_type` | enum | 예 | `owned`, `leased`, `subleased`, `free_use` | 사업장 형태 |
| `has_right_issue` | boolean | 예 | `true`, `false` | 권리침해 여부 |
| `deposit` | number | 조건부 | 0 이상 | 임차/전대인 경우 사용 |
| `monthly_rent` | number | 조건부 | 0 이상 | 임차/전대인 경우 사용 |
| `uses_leased_business_vehicle_or_vessel` | boolean | 아니오 | `true`, `false` | 운송·선박 영업용 임차 사용 여부 |

`has_right_issue = true`이면 추천 결과가 비어 있을 수 있다.

### 3.7 residence

```json
{
  "occupancy_type": "leased",
  "deposit": 5000000,
  "monthly_rent": 500000
}
```

| 필드명 | 타입 | 필수 | 허용값 | 설명 |
| --- | --- | --- | --- | --- |
| `occupancy_type` | enum | 예 | `owned`, `leased`, `free_use` | 대표자 거주 형태 |
| `deposit` | number | 조건부 | 0 이상 | 임차인 경우 사용 |
| `monthly_rent` | number | 조건부 | 0 이상 | 임차인 경우 사용 |

### 3.8 innovation_signals

```json
{
  "smart_tech_adoption": true,
  "smart_factory": false,
  "has_patent_or_ip": false,
  "has_esg_certification": false,
  "has_export_experience": true,
  "is_local_creator": false,
  "needs_facility_fund": false
}
```

| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `smart_tech_adoption` | boolean | 아니오 | 스마트기술 도입 여부 |
| `smart_factory` | boolean | 아니오 | 스마트공장 여부 |
| `has_patent_or_ip` | boolean | 아니오 | 특허/지식재산 보유 여부 |
| `has_esg_certification` | boolean | 아니오 | ESG 인증 여부 |
| `has_export_experience` | boolean | 아니오 | 수출 여부 |
| `is_local_creator` | boolean | 아니오 | 로컬크리에이터 여부 |
| `needs_facility_fund` | boolean | 아니오 | 시설자금 신청 여부 |

혁신성장촉진자금은 점수 합산이 아니라 세부유형 직접 매칭으로 판단한다. 예를 들어 `has_export_experience = true`와 `is_local_creator = true`가 동시에 들어오면 `수출유형`, `로컬크리에이터유형`이 모두 매칭된다.

### 3.9 growth_signals

```json
{
  "sells_online": true,
  "platform_entry_or_tops": true
}
```

| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `sells_online` | boolean | 아니오 | 온라인 판매 여부 |
| `platform_entry_or_tops` | boolean | 아니오 | 플랫폼 입점, TOPS, POST-TOPS 여부 |

`sells_online = true`이면 상생성장지원자금을 추천 후보로 만든다. 단, `platform_entry_or_tops = false`이면 응답의 `guidance_messages`에 `TOPS/POST-TOPS 참여가 필요합니다.` 안내를 함께 담는다.

### 3.10 special_conditions

```json
{
  "is_homeplus_tenant": false,
  "has_disaster_damage": false,
  "is_in_designated_area": false
}
```

| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `is_homeplus_tenant` | boolean | 아니오 | 홈플러스 입점 피해 여부 |
| `has_disaster_damage` | boolean | 아니오 | 재난피해 여부 |
| `is_in_designated_area` | boolean | 아니오 | 지정지역 소재 여부 |

### 3.11 joint_representatives

```json
[
  {
    "sequence": 1,
    "residence": {
      "occupancy_type": "owned"
    }
  },
  {
    "sequence": 2,
    "residence": {
      "occupancy_type": "leased",
      "deposit": 5000000,
      "monthly_rent": 400000
    }
  }
]
```

공동대표가 없으면 빈 배열을 보낸다. 공동대표가 있으면 `joint_representative_count`와 배열 길이가 같아야 한다.

### 3.12 follow_up_answers

```json
{
  "fg-innovation-growth": {
    "innovation_variant_types": ["smart_tech", "export"],
    "smart_tech_proof_type": "purchase",
    "export_proof_type": "certificate"
  }
}
```

후속 질문 답변은 선택값이다. 값이 없어도 1차 추천 카드는 만들 수 있지만, 일부 세부유형명과 제출서류가 덜 정확할 수 있다.

## 4. 요청 예시

### 4.1 법인, 사업장 임차, 스마트기술 도입

```json
{
  "applicant": {
    "business_entity_type": "corporation",
    "tax_delinquent": false,
    "has_joint_representative": false,
    "joint_representative_count": 0
  },
  "industry": {
    "industry_code": "G47912",
    "industry_name": "전자상거래 소매업",
    "industry_level": "small",
    "standard_industry_name": "전자상거래 소매업",
    "is_excluded": false,
    "source": "external_api"
  },
  "employment": {
    "employee_band": "under_5"
  },
  "business_status": {
    "has_closure_history": false,
    "sales_band_y3": "none",
    "sales_band_y2": "50m_to_104m",
    "sales_band_y1": "104m_to_450m"
  },
  "credit": {
    "credit_score_band_nice": "840_899"
  },
  "business_site": {
    "occupancy_type": "leased",
    "has_right_issue": false,
    "deposit": 10000000,
    "monthly_rent": 700000,
    "uses_leased_business_vehicle_or_vessel": false
  },
  "residence": {
    "occupancy_type": "leased",
    "deposit": 5000000,
    "monthly_rent": 500000
  },
  "innovation_signals": {
    "smart_tech_adoption": true,
    "smart_factory": false,
    "has_patent_or_ip": false,
    "has_esg_certification": false,
    "has_export_experience": false,
    "is_local_creator": false,
    "needs_facility_fund": false
  },
  "growth_signals": {
    "sells_online": true,
    "platform_entry_or_tops": false
  },
  "special_conditions": {
    "is_homeplus_tenant": false,
    "has_disaster_damage": false,
    "is_in_designated_area": false
  },
  "joint_representatives": [],
  "follow_up_answers": {
    "fg-innovation-growth": {
      "innovation_variant_types": ["smart_tech"],
      "smart_tech_proof_type": "purchase"
    }
  }
}
```

이 예시는 `growth_signals.sells_online = true`도 함께 들어오므로, 공통 제한 조건이 없다면 `혁신성장촉진자금`과 별도로 `상생성장지원자금`도 추천 후보가 될 수 있다. 이때 `platform_entry_or_tops = false`이면 TOPS/POST-TOPS 참여가 필요하다는 안내를 함께 내려준다.

### 4.2 수출과 로컬크리에이터가 동시에 해당

```json
{
  "applicant": {
    "business_entity_type": "individual",
    "tax_delinquent": false,
    "has_joint_representative": false,
    "joint_representative_count": 0
  },
  "industry": {
    "industry_code": "C10100",
    "industry_name": "식료품 제조업",
    "industry_level": "small",
    "standard_industry_name": "식료품 제조업",
    "is_excluded": false,
    "source": "external_api"
  },
  "employment": {
    "employee_band": "five_to_nine"
  },
  "business_status": {
    "has_closure_history": false,
    "sales_band_y3": "104m_to_450m",
    "sales_band_y2": "104m_to_450m",
    "sales_band_y1": "450m_to_1500m"
  },
  "credit": {
    "credit_score_band_nice": "840_899"
  },
  "business_site": {
    "occupancy_type": "owned",
    "has_right_issue": false,
    "uses_leased_business_vehicle_or_vessel": false
  },
  "residence": {
    "occupancy_type": "owned"
  },
  "innovation_signals": {
    "smart_tech_adoption": false,
    "smart_factory": false,
    "has_patent_or_ip": false,
    "has_esg_certification": false,
    "has_export_experience": true,
    "is_local_creator": true,
    "needs_facility_fund": false
  },
  "growth_signals": {
    "sells_online": false,
    "platform_entry_or_tops": false
  },
  "special_conditions": {
    "is_homeplus_tenant": false,
    "has_disaster_damage": false,
    "is_in_designated_area": false
  },
  "joint_representatives": [],
  "follow_up_answers": {
    "fg-innovation-growth": {
      "innovation_variant_types": ["export", "local_creator"],
      "export_proof_type": "certificate",
      "local_creator_proof_available": true
    }
  }
}
```

이 경우 `혁신성장촉진자금` 카드의 `matched_variants`에는 `수출유형`, `로컬크리에이터유형`이 함께 들어가야 한다. `스마트기술유형`은 추천되지 않는다.

### 4.3 온라인 판매만 확인된 상생성장지원자금

```json
{
  "applicant": {
    "business_entity_type": "individual",
    "tax_delinquent": false,
    "has_joint_representative": false,
    "joint_representative_count": 0
  },
  "industry": {
    "industry_code": "G47912",
    "industry_name": "전자상거래 소매업",
    "industry_level": "small",
    "standard_industry_name": "전자상거래 소매업",
    "is_excluded": false,
    "source": "external_api"
  },
  "employment": {
    "employee_band": "under_5"
  },
  "business_status": {
    "has_closure_history": false,
    "sales_band_y3": "none",
    "sales_band_y2": "none",
    "sales_band_y1": "50m_to_104m"
  },
  "credit": {
    "credit_score_band_nice": "840_899"
  },
  "business_site": {
    "occupancy_type": "leased",
    "has_right_issue": false,
    "deposit": 10000000,
    "monthly_rent": 700000,
    "uses_leased_business_vehicle_or_vessel": false
  },
  "residence": {
    "occupancy_type": "leased",
    "deposit": 5000000,
    "monthly_rent": 500000
  },
  "innovation_signals": {
    "smart_tech_adoption": false,
    "smart_factory": false,
    "has_patent_or_ip": false,
    "has_esg_certification": false,
    "has_export_experience": false,
    "is_local_creator": false,
    "needs_facility_fund": false
  },
  "growth_signals": {
    "sells_online": true,
    "platform_entry_or_tops": false
  },
  "special_conditions": {
    "is_homeplus_tenant": false,
    "has_disaster_damage": false,
    "is_in_designated_area": false
  },
  "joint_representatives": [],
  "follow_up_answers": {
    "fg-winwin-growth": {
      "growth_trigger_type": "online_sales",
      "mail_order_registration_available": true
    }
  }
}
```

이 경우 `상생성장지원자금`은 추천하되, `guidance_messages`에 TOPS/POST-TOPS 참여가 필요하다는 안내가 들어가야 한다.

## 5. 처리 순서

백엔드는 아래 순서로 요청을 처리한다.

1. `X-Request-Id`가 없으면 서버에서 생성한다.
2. JSON 구조와 필수 필드를 검증한다.
3. 화면 코드값을 내부 필드명으로 정규화한다.
4. 업종 제외 여부, 체납 여부, 권리침해 여부, 소상공인 상시근로자 기준을 확인한다.
5. 공통 신청 제한에 걸리면 추천 후보를 만들지 않는다.
6. 자금별 추천 규칙을 평가한다.
7. 세부유형 트리거를 평가한다.
8. 후속 질문 답변이 있으면 세부유형과 서류 묶음을 보정한다.
9. `BASE-*`, `FUND-*`, `VAR-*` 서류 묶음을 계산한다.
10. 실제 문서명 기준으로 중복 서류를 제거한다.
11. 추천 후보를 내부 `display_priority` 기준으로 정렬한다.
12. `display_priority`, `bundle_id`, 내부 판정 로그를 제거한다.
13. [08_추천_API_응답정의.md](/Users/jeehun/Documents/GitHub/Government-backed funding/docs/08_추천_API_응답정의.md)의 응답 구조로 반환한다.

## 6. 성공 응답

성공 응답은 항상 `200 OK`로 반환한다.

추천 가능한 자금이 있으면 `recommended_funds`에 자금 카드 목록을 담는다.

```json
{
  "request_id": "rec_20260503_001",
  "generated_at": "2026-05-03T21:30:00+09:00",
  "result_message": "입력 조건에 맞는 정책자금 1건을 찾았습니다.",
  "recommended_funds": [
    {
      "fund_code": "innovation_growth",
      "fund_name": "혁신성장촉진자금",
      "matched_variants": [
        {
          "variant_code": "export",
          "variant_name": "수출유형",
          "matched_reason": "수출 여부가 확인되었습니다."
        },
        {
          "variant_code": "local_creator",
          "variant_name": "로컬크리에이터유형",
          "matched_reason": "로컬크리에이터 조건이 확인되었습니다."
        }
      ],
      "recommendation_level": "recommended",
      "summary_reason": "수출과 로컬크리에이터 조건이 확인되어 혁신성장촉진자금 검토가 가능합니다.",
      "matched_reasons": [
        "수출 여부가 확인되었습니다.",
        "로컬크리에이터 조건이 확인되었습니다."
      ],
      "guidance_messages": [],
      "detail_preview": {
        "intro_paragraph": "혁신성장촉진자금은 성장성과 혁신성을 가진 소상공인의 사업 확장과 경쟁력 강화를 지원하는 자금입니다.",
        "quick_info_sections": [
          {
            "title": "지원대상",
            "text": "혁신형 성장 요소를 보유한 소상공인"
          },
          {
            "title": "특징",
            "text": "세부유형별로 추가 증빙과 심사 포인트가 다릅니다."
          },
          {
            "title": "지원내용",
            "text": "운전자금 또는 시설자금 검토가 가능합니다."
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
            "doc_name": "수출실적증명원",
            "issuer": "수출 관련 증명 발급기관",
            "issuance_method": "수출 실적 증명자료 발급 후 제출",
            "condition_note": "수출유형",
            "notes": []
          },
          {
            "doc_name": "로컬크리에이터 선정확인서",
            "issuer": "선정기관 또는 사업 운영기관",
            "issuance_method": "선정확인서 또는 협약서 사본 제출",
            "condition_note": "로컬크리에이터유형",
            "notes": []
          }
        ],
        "review_documents_notice": "아래 서류는 심사 후 추가서류로 분류되지만, 신청 시 함께 첨부하면 검토가 더 원활합니다.",
        "review_documents": [
          {
            "doc_name": "최근 3년 재무자료",
            "issuer": "홈택스 또는 세무대리인",
            "issuance_method": "표준재무제표증명 등 제출",
            "condition_note": "심사 보강자료",
            "notes": []
          }
        ]
      }
    }
  ]
}
```

### 6.1 추천 결과가 없는 경우

추천 후보가 없더라도 오류로 보지 않는다. 이 경우도 `200 OK`로 반환한다.

```json
{
  "request_id": "rec_20260503_002",
  "generated_at": "2026-05-03T21:31:00+09:00",
  "result_message": "현재 입력 조건으로 바로 추천할 수 있는 정책자금이 없습니다.",
  "recommended_funds": []
}
```

`recommended_funds`가 비어 있는 이유를 사용자 응답에 상세히 넣지 않는다. 필요한 안내는 프론트 입력 단계의 검증 문구나 상담 화면에서 처리한다.

## 7. 오류 응답

요청 자체가 처리 불가능할 때만 오류 응답을 사용한다.

### 7.1 오류 응답 공통 구조

```json
{
  "request_id": "rec_20260503_003",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "요청값을 확인해주세요.",
    "fields": [
      {
        "path": "industry.industry_code",
        "reason": "업종 코드는 필수입니다."
      }
    ]
  }
}
```

### 7.2 상태코드

| 상태코드 | code | 사용 상황 |
| --- | --- | --- |
| `400 Bad Request` | `INVALID_JSON` | JSON 파싱 실패 |
| `422 Unprocessable Entity` | `VALIDATION_ERROR` | 필수 필드 누락, enum 값 오류, 조건부 필드 불일치 |
| `500 Internal Server Error` | `INTERNAL_ERROR` | 서버 내부 처리 실패 |
| `503 Service Unavailable` | `RULE_DATA_UNAVAILABLE` | 게시된 추천 규칙 또는 서류 규칙을 읽을 수 없음 |

신청 제한 조건에 걸리는 것은 오류가 아니다. 예를 들어 제외업종이나 체납 여부가 확인된 경우에도 요청값 자체는 유효하므로 `200 OK`와 빈 추천 목록을 반환할 수 있다.

## 8. 검증 규칙

### 8.1 필수값 검증

- `applicant.business_entity_type`은 반드시 있어야 한다.
- `applicant.tax_delinquent`는 반드시 있어야 한다.
- `industry.industry_code`, `industry.industry_name`, `industry.is_excluded`는 반드시 있어야 한다.
- `employment.employee_band`는 반드시 있어야 한다.
- `business_status.has_closure_history`는 반드시 있어야 한다.
- `credit.credit_score_band_nice`는 반드시 있어야 한다.
- `business_site.occupancy_type`, `business_site.has_right_issue`는 반드시 있어야 한다.
- `residence.occupancy_type`은 반드시 있어야 한다.

### 8.2 조건부 검증

- `applicant.has_joint_representative = true`이면 `joint_representative_count`는 `1` 이상이어야 한다.
- `applicant.has_joint_representative = true`이면 `joint_representatives.length`는 `joint_representative_count`와 같아야 한다.
- `business_site.occupancy_type`이 `leased` 또는 `subleased`이면 `deposit`, `monthly_rent`는 숫자여야 한다.
- `residence.occupancy_type = leased`이면 `deposit`, `monthly_rent`는 숫자여야 한다.
- `industry.source = manual_override`이면 운영자 화면에서는 별도 감사 로그가 필요하다.

### 8.3 enum 검증

허용되지 않은 enum 값이 들어오면 `422 VALIDATION_ERROR`로 처리한다. 화면 표시값은 프론트에서 API 코드값으로 변환해서 보내야 한다.

## 9. 정렬 규칙

추천 후보는 내부 `display_priority` 기준으로 정렬한다.

- `display_priority`는 사용자 응답에 포함하지 않는다.
- 같은 자금 안에서 여러 세부유형이 매칭되면 `matched_variants[]` 내부도 `display_priority` 기준으로 정렬한다.
- 같은 우선순위이면 자금 운영 우선순위, 추천 근거 수, 자금명 순으로 정렬한다.

정렬은 화면 노출 순서만 결정한다. 추천 여부 자체는 조건 직접 매칭으로 판단한다.

## 10. 개인정보와 로그 정책

- 사용자 추천 API는 이름, 연락처, 사업자등록번호, 주민등록번호를 받지 않는다.
- 신용점수는 원점수가 아니라 구간값만 받는다.
- 추천 요청 로그를 남긴다면 raw 입력 전체가 아니라 아래 수준만 저장한다.

```json
{
  "request_id": "rec_20260503_001",
  "generated_at": "2026-05-03T21:30:00+09:00",
  "rule_version": "2026-05",
  "matched_fund_codes": ["innovation_growth"],
  "matched_variant_codes": ["export", "local_creator"],
  "credit_score_band_nice": "840_899",
  "industry_is_excluded": false
}
```

- `business_site_deposit`, `business_site_monthly_rent`, `residence_deposit`, `residence_monthly_rent`는 추천 계산에만 사용하고 기본 로그 저장 대상에서 제외한다.
- 내부 판정 로그, `display_priority`, `bundle_id`는 운영자 디버깅 로그에는 남길 수 있지만 사용자 응답에는 포함하지 않는다.

## 11. 프론트 구현 메모

- 프론트는 사용자가 선택한 화면 라벨을 API 코드값으로 변환해서 보낸다.
- 업종은 텍스트 입력값이 아니라 검색 결과에서 선택된 객체를 보낸다.
- `recommended_funds[]`가 비어 있으면 결과 없음 화면을 보여준다.
- `matched_variants[]`가 여러 개이면 카드 안에 세부유형 배지를 여러 개 보여줄 수 있다.
- `[맞춤 제출서류 보기]` 버튼 라벨은 프론트 고정 문구로 둔다.
- 자금명 클릭 시 `detail_preview`를 토글로 보여주고, `[상세보기]`는 `detail_page_url`로 이동한다.
- `guidance_messages[]`가 있으면 카드 상단 추천 이유 아래에 주의 안내 박스로 보여준다.
- `review_documents_notice`는 심사 후 서류가 없어도 화면 정책상 유지할 수 있다.

## 12. 백엔드 구현 메모

- 추천 API는 게시 완료된 운영 규칙만 참조한다.
- 초안 상태의 규칙이나 서류 가이드는 사용자 추천에 사용하지 않는다.
- `display_priority`, `bundle_id`, 내부 rule id는 응답 직전에 제거한다.
- 같은 문서가 여러 묶음에서 중복되면 `doc_name` 기준으로 1차 중복 제거한다.
- 동일 문서명이지만 제출 조건이 다르면 `condition_note`를 합치거나 `notes`에 조건을 병합한다.
- 추천 결과 생성 실패가 외부 업종 검색 API 장애 때문이면 안 된다. 추천 API는 이미 선택된 업종 객체를 받기 때문이다.
