# System Architecture

```mermaid
flowchart TD
    A["관리자 문서 업로드<br/>PDF / HWP / HTML"] --> B["Admin Upload UI"]
    B --> C["원본 저장소<br/>(Amazon S3 Raw)"]

    C --> D["문서 파서<br/>(PDF / HWP / OCR)"]
    D --> E["파싱 결과 저장<br/>(S3 Parsed)"]

    E --> F["문서 분류기"]
    F --> G["청크 생성"]
    G --> H["임베딩 생성"]
    H --> I["Vector Store<br/>(pgvector)"]

    E --> J["LLM 추출기"]
    J --> K["Draft Rules<br/>(PostgreSQL)"]

    K --> L["검토 UI (Admin)"]
    L -->|승인| M["Published Rules<br/>(PostgreSQL)"]
    L -->|수정 후 승인| M
    L -->|반려| N["Draft 보관 / 재검토"]

    U["사용자 상태 선택<br/>업종 / 매출 / 업력 / 체납 여부"] --> O["상태 선택형 추천 API"]
    M --> O

    V["챗봇 질문"] --> P["챗봇 API"]
    P --> I
    P --> M
    P --> W["LLM 응답 생성"]

    C --> Q["선택적 분석 적재"]
    E --> Q
    M --> Q
    Q --> R["리포팅 / 포트폴리오 데모 분석"]

    S["EC2 + Docker Compose<br/>(최종 데모 배포)"] --> B
    S --> O
    S --> P
```

## Notes

- 문서는 크롤링이 아니라 관리자가 직접 업로드하는 MVP 기준입니다.
- Amazon S3는 원본 문서와 파싱 결과를 보관하는 저장소입니다.
- PostgreSQL은 Draft / Published Rules와 추천 서비스 운영 데이터의 기준 저장소입니다.
- `Draft Rules`는 AI가 추출한 초안이고, `Published Rules`는 검토 후 실제 추천에 사용되는 운영 규칙입니다.
- pgvector는 챗봇 RAG와 문서 근거 검색을 위한 벡터 저장소입니다.
- 상태 선택형 추천은 PostgreSQL의 `Published Rules`를 직접 조회합니다.
- 챗봇은 FastAPI를 통해 pgvector와 PostgreSQL을 함께 조회한 뒤 LLM으로 답변을 생성합니다.
- EC2는 최종 데모 배포용 런타임으로만 사용하며, 평소에는 인스턴스를 꺼둘 수 있습니다.
- 분석 계층은 선택 사항이며, 포트폴리오 MVP에서는 필수는 아닙니다.
