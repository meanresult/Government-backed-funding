# Technical Architecture

## Recommended Stack

- Frontend / BFF: Next.js
- Backend Processing: FastAPI
- Operational Database: PostgreSQL
- Vector Search: pgvector
- Object Storage: Amazon S3
- LLM / Embeddings: OpenAI API
- Runtime: Docker Compose
- Final Demo Deployment: Amazon EC2
- Analytics: Optional only

## Architecture Diagram

```mermaid
flowchart TD
    subgraph Client["Client Layer"]
        A["Admin Browser"]
        B["End User Browser"]
    end

    subgraph Runtime["Runtime Layer"]
        C["EC2 Instance"]
        D["Docker Compose"]
    end

    subgraph App["Application Layer"]
        E["Next.js Web App"]
        F["FastAPI Service"]
        G["Admin Upload UI"]
        H["Review UI"]
        I["Recommendation API"]
        J["Chatbot API"]
    end

    subgraph Pipeline["Document Pipeline"]
        K["Upload Handler"]
        L["Parser / OCR"]
        M["Parsed Output Writer"]
        N["Chunk Builder"]
        O["Embedding Job"]
        P["Rule Extraction Job"]
    end

    subgraph Storage["Storage Layer"]
        Q["Amazon S3 Raw"]
        R["Amazon S3 Parsed"]
        S["PostgreSQL"]
        T["Published Rules"]
        U["Draft Rules"]
        V["Audit Logs / User Inputs"]
        W["pgvector"]
    end

    subgraph External["External Services"]
        X["OpenAI API"]
    end

    subgraph Analytics["Optional Analytics Layer"]
        Y["Parquet / DW Export"]
        Z["Portfolio Reporting"]
    end

    A --> E
    B --> E

    C --> D
    D --> E
    D --> F
    D --> S

    E --> G
    E --> H
    E --> I
    E --> J

    G --> F
    H --> F
    I --> F
    J --> F

    F --> K
    K --> Q
    Q --> L
    L --> M
    M --> R

    R --> N
    N --> O
    O --> W

    R --> P
    P --> U
    H --> U
    H --> T

    F --> S
    S --> T
    S --> U
    S --> V

    F --> X
    O --> X
    P --> X

    Q --> Y
    R --> Y
    T --> Y
    Y --> Z
```

## Component Responsibilities

### 1. Next.js Web App

- 정책자금 소개 페이지 제공
- 관리자 문서 업로드 화면 제공
- 추천 결과 화면 제공
- 챗봇 UI 제공
- 검토 및 승인 화면 제공

### 2. FastAPI Service

- 문서 업로드 처리
- S3 파일 저장 연동
- 문서 파싱 및 후처리 오케스트레이션
- 추천 API 및 챗봇 API 제공
- Draft / Published Rules 반영 처리

### 3. Amazon S3

- 원본 PDF / HWP / HTML 저장
- 파싱된 텍스트 결과 저장
- chunk 생성 전 중간 산출물 저장
- 재파싱 / 재임베딩 / 재검토를 위한 장기 보관 계층

### 4. PostgreSQL

- 문서 메타데이터 저장
- 자격요건 초안 저장
- 승인된 정책 규칙 저장
- 사용자 입력, 감사 로그, 검토 이력 저장

### 5. pgvector

- 문서 청크 임베딩 저장
- 챗봇 RAG 검색
- 추천 결과에 필요한 근거 탐색 보조

### 6. OpenAI API

- 임베딩 생성
- 문서 기반 자격요건 구조화 추출
- 챗봇 응답 생성

### 7. Docker Compose

- Next.js / FastAPI / PostgreSQL 실행 환경 통합
- 로컬 개발과 데모 서버 실행 환경 일치
- 면접 시 `docker compose up` 기반 재현성 제공

### 8. Amazon EC2

- 최종 데모용 배포 서버
- Docker Compose 기반으로 앱 실행
- 필요할 때만 켜고, 평소에는 중지 가능한 비용 절약형 운영

## Main Flows

### A. 문서 업로드 및 구조화

1. 관리자가 PDF / HWP / HTML 문서를 업로드한다.
2. 업로드 핸들러가 원본 문서를 S3 Raw에 저장한다.
3. 파서가 문서를 텍스트로 변환하고 파싱 결과를 S3 Parsed에 저장한다.
4. LLM이 파싱 결과에서 자격요건 후보를 추출해 Draft Rules로 저장한다.
5. 관리자가 검토 후 Published Rules로 승인한다.

### B. 사용자 자금 추천

1. 사용자가 기업 상태를 입력한다.
2. FastAPI가 PostgreSQL의 Published Rules를 조회한다.
3. 추천 엔진이 조건 매칭과 업종 기반 추론을 수행한다.
4. 추천 자금, 보완 항목, 필요 서류를 반환한다.

### C. 챗봇 RAG

1. 사용자가 질문을 입력한다.
2. 챗봇 API가 pgvector에서 관련 문서 청크를 검색한다.
3. 관련 청크와 Published Rules를 함께 LLM에 전달한다.
4. 답변과 근거를 함께 반환한다.

### D. 최종 데모 배포

1. 애플리케이션을 Docker Compose로 패키징한다.
2. EC2 인스턴스에서 컨테이너를 실행한다.
3. 데모가 끝나면 EC2를 중지하고, 문서와 데이터는 S3 / PostgreSQL에 유지한다.

## Design Principles

- 업로드 문서 원본과 파싱 결과를 분리 저장한다.
- 운영 데이터는 Published Rules만 사용한다.
- AI 추출 결과는 반드시 Draft 상태를 거친다.
- 챗봇 RAG와 추천 엔진은 같은 문서를 참고하되, 운영 규칙 저장소는 분리한다.
- Docker Compose로 로컬과 데모 서버 실행 방식을 통일한다.
- EC2는 상시 운영이 아니라 포트폴리오 데모 목적의 선택적 런타임으로 사용한다.
