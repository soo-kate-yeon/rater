# API 엔드포인트 문서

## 개요

TOEFL Speaking Rater API는 RESTful 원칙을 따르며, FastAPI 기반으로 구현되었습니다.

### 기본 정보

- **Base URL**: `http://localhost:8000` (개발 환경)
- **API 문서**:
  - Swagger UI: http://localhost:8000/docs
  - ReDoc: http://localhost:8000/redoc
- **인증 방식**: JWT Bearer Token
- **Content-Type**: `application/json`

---

## 인증 (Authentication)

### 회원가입

**POST** `/api/v1/auth/register`

새로운 사용자 계정을 생성합니다.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "username": "testuser"
}
```

**Response:** `201 Created`
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "username": "testuser",
  "created_at": "2026-01-27T00:00:00Z"
}
```

---

### 로그인

**POST** `/api/v1/auth/login`

사용자 인증 후 JWT 토큰을 발급합니다.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## 문제 세트 관리 (Sets)

### 세트 목록 조회

**GET** `/api/v1/sets`

문제 세트 목록을 페이지네이션으로 조회합니다.

**Query Parameters:**
- `skip` (integer, optional): 건너뛸 레코드 수 (default: 0)
- `limit` (integer, optional): 조회할 최대 레코드 수 (default: 50, max: 100)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "set_id": "TPO-01",
      "title": "TPO 1 Speaking Set",
      "source": "Official TPO",
      "version": "1.0",
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 40,
  "skip": 0,
  "limit": 50
}
```

---

### 세트 생성

**POST** `/api/v1/sets`

새로운 문제 세트를 생성합니다.

**Request Body:**
```json
{
  "set_id": "TPO-01",
  "title": "TPO 1 Speaking Set",
  "source": "Official TPO",
  "version": "1.0"
}
```

**Response:** `201 Created`

---

### 세트 상세 조회

**GET** `/api/v1/sets/{set_id}`

특정 문제 세트의 상세 정보를 조회합니다.

**Path Parameters:**
- `set_id` (string, required): 세트 ID

**Response:** `200 OK`

---

### 세트 수정

**PATCH** `/api/v1/sets/{set_id}`

문제 세트 정보를 부분 수정합니다.

**Request Body:**
```json
{
  "title": "Updated Title",
  "version": "1.1"
}
```

**Response:** `200 OK`

---

### 세트 삭제

**DELETE** `/api/v1/sets/{set_id}`

문제 세트를 삭제합니다.

**Response:** `204 No Content`

---

## 문항 관리 (Items)

### 문항 목록 조회

**GET** `/api/v1/items`

문항 목록을 페이지네이션으로 조회합니다.

**Query Parameters:**
- `skip` (integer, optional): 건너뛸 레코드 수 (default: 0)
- `limit` (integer, optional): 조회할 최대 레코드 수 (default: 50)
- `set_id` (string, optional): 특정 세트의 문항만 필터링
- `task_type` (string, optional): 문항 유형 필터링 (`independent`, `integrated_read_listen`, `integrated_listen_only`)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "item_id": "TPO-01-Q1",
      "set_id": "TPO-01",
      "task_no": 1,
      "task_type": "independent",
      "prompt": "Talk about a book you have read...",
      "prep_seconds": 15,
      "response_seconds": 45,
      "language": "en",
      "tags": ["personal_preference", "reading"],
      "difficulty": "medium",
      "scoring_focus": "general_description"
    }
  ],
  "total": 240,
  "skip": 0,
  "limit": 50
}
```

---

### 문항 생성

**POST** `/api/v1/items`

새로운 문항을 생성합니다.

**Request Body:**
```json
{
  "item_id": "TPO-01-Q1",
  "set_id": "TPO-01",
  "task_no": 1,
  "task_type": "independent",
  "prompt": "Talk about a book you have read...",
  "prep_seconds": 15,
  "response_seconds": 45,
  "language": "en",
  "tags": ["personal_preference", "reading"],
  "difficulty": "medium",
  "scoring_focus": "general_description"
}
```

**Response:** `201 Created`

---

### 문항 상세 조회

**GET** `/api/v1/items/{item_id}`

특정 문항의 상세 정보를 조회합니다.

**Response:** `200 OK`

---

### 문항 관계 포함 조회

**GET** `/api/v1/items/{item_id}/with-relations`

문항과 관련된 Stimuli, AnswerKeys를 함께 조회합니다.

**Response:** `200 OK`
```json
{
  "item": {
    "item_id": "TPO-01-Q3",
    "task_type": "integrated_read_listen",
    "prompt": "Explain the concept..."
  },
  "stimuli": [
    {
      "stimulus_id": "STIM-001",
      "kind": "reading",
      "title": "University Announcement",
      "content_text": "...",
      "order": 1
    },
    {
      "stimulus_id": "STIM-002",
      "kind": "listening",
      "asset_url": "s3://bucket/audio.mp3",
      "duration_seconds": 60,
      "order": 2
    }
  ],
  "answer_keys": [
    {
      "answer_id": "ANS-001",
      "type": "sample_response",
      "level": "advanced",
      "content": "..."
    }
  ]
}
```

---

### 문항 수정

**PATCH** `/api/v1/items/{item_id}`

문항 정보를 부분 수정합니다.

**Response:** `200 OK`

---

### 문항 삭제

**DELETE** `/api/v1/items/{item_id}`

문항을 삭제합니다.

**Response:** `204 No Content`

---

## 자극자료 관리 (Stimuli)

### Stimuli 목록 조회

**GET** `/api/v1/stimuli`

자극자료 목록을 조회합니다.

**Query Parameters:**
- `skip`, `limit`: 페이지네이션
- `item_id` (string, optional): 특정 문항의 Stimuli만 필터링
- `kind` (string, optional): 자극자료 종류 필터링 (`reading`, `listening`, `direction`)

**Response:** `200 OK`

---

### Stimuli 생성

**POST** `/api/v1/stimuli`

새로운 자극자료를 생성합니다.

**Request Body:**
```json
{
  "stimulus_id": "STIM-001",
  "item_id": "TPO-01-Q3",
  "kind": "reading",
  "title": "University Announcement",
  "content_text": "The university will implement...",
  "order": 1,
  "notes_allowed": true
}
```

**Response:** `201 Created`

---

### Stimuli 상세 조회

**GET** `/api/v1/stimuli/{stimulus_id}`

**Response:** `200 OK`

---

### Stimuli 수정

**PATCH** `/api/v1/stimuli/{stimulus_id}`

**Response:** `200 OK`

---

### Stimuli 삭제

**DELETE** `/api/v1/stimuli/{stimulus_id}`

**Response:** `204 No Content`

---

## 모범답안 관리 (Answer Keys)

### Answer Key 목록 조회

**GET** `/api/v1/answer-keys`

모범답안 목록을 조회합니다.

**Query Parameters:**
- `skip`, `limit`: 페이지네이션
- `item_id` (string, optional): 특정 문항의 Answer Keys만 필터링
- `type` (string, optional): 타입 필터링 (`sample_response`, `transcript`, `blueprint`)
- `level` (string, optional): 레벨 필터링 (`basic`, `advanced`, `ultimate`)

**Response:** `200 OK`

---

### Answer Key 생성

**POST** `/api/v1/answer-keys`

새로운 모범답안을 생성합니다.

**Request Body:**
```json
{
  "answer_id": "ANS-001",
  "item_id": "TPO-01-Q1",
  "type": "sample_response",
  "level": "advanced",
  "content": "I would like to talk about...",
  "source": "Official Guide"
}
```

**Response:** `201 Created`

---

### Blueprint 생성

**POST** `/api/v1/answer-keys/blueprint`

Blueprint 타입의 Answer Key를 생성합니다 (별도 엔드포인트).

**Response:** `201 Created`

---

### Answer Key 상세 조회

**GET** `/api/v1/answer-keys/{answer_key_id}`

**Response:** `200 OK`

---

### Answer Key 수정

**PATCH** `/api/v1/answer-keys/{answer_key_id}`

**Response:** `200 OK`

---

### Answer Key 삭제

**DELETE** `/api/v1/answer-keys/{answer_key_id}`

**Response:** `204 No Content`

---

## 태스크 관리 (Tasks)

### 태스크 목록 조회

**GET** `/api/v1/tasks`

사용자의 태스크 목록을 조회합니다.

**Response:** `200 OK`
```json
[
  {
    "task_id": "uuid",
    "user_id": "uuid",
    "item_id": "TPO-01-Q1",
    "status": "pending",
    "created_at": "2026-01-27T00:00:00Z"
  }
]
```

---

### 태스크 생성

**POST** `/api/v1/tasks`

새로운 태스크를 생성합니다 (음성 파일 업로드 후 채점 요청).

**Request Body:**
```json
{
  "item_id": "TPO-01-Q1",
  "audio_url": "s3://bucket/responses/user_123_response.mp3"
}
```

**Response:** `201 Created`

---

### 태스크 상세 조회

**GET** `/api/v1/tasks/{task_id}`

**Response:** `200 OK`

---

## 작업 관리 (Jobs)

### 채점 작업 생성

**POST** `/api/v1/jobs`

비동기 채점 작업을 생성합니다 (Celery Worker로 처리).

**Request Body:**
```json
{
  "task_id": "uuid",
  "job_type": "scoring"
}
```

**Response:** `201 Created`
```json
{
  "job_id": "uuid",
  "task_id": "uuid",
  "status": "queued",
  "created_at": "2026-01-27T00:00:00Z"
}
```

---

### 작업 상태 조회

**GET** `/api/v1/jobs/{job_id}`

채점 작업의 현재 상태를 조회합니다.

**Response:** `200 OK`
```json
{
  "job_id": "uuid",
  "status": "completed",
  "progress": 100,
  "result": {
    "score_range": [22, 25],
    "feedback": "..."
  },
  "error": null,
  "created_at": "2026-01-27T00:00:00Z",
  "completed_at": "2026-01-27T00:01:30Z"
}
```

**Status Values:**
- `queued`: 대기 중
- `processing`: 처리 중
- `completed`: 완료
- `failed`: 실패

---

### 채점 리포트 조회

**GET** `/api/v1/jobs/{job_id}/report`

채점 완료 후 상세 리포트를 조회합니다.

**Response:** `200 OK`
```json
{
  "job_id": "uuid",
  "task_id": "uuid",
  "score_range": [22, 25],
  "feedback": {
    "structure": "Your response had a clear introduction...",
    "language_use": "Grammar was generally accurate...",
    "delivery": "Pronunciation was clear but pace was rushed..."
  },
  "weakness_analysis": "Main weakness: Limited development of ideas...",
  "transcript": "Recognized text from audio...",
  "created_at": "2026-01-27T00:01:30Z"
}
```

---

## 파일 업로드 (Uploads)

### Presigned URL 발급

**POST** `/api/v1/uploads/presign`

S3 업로드를 위한 Presigned URL을 발급합니다.

**Request Body:**
```json
{
  "file_name": "response.mp3",
  "content_type": "audio/mpeg"
}
```

**Response:** `201 Created`
```json
{
  "upload_url": "https://s3.amazonaws.com/...",
  "file_key": "responses/uuid_response.mp3",
  "expires_in": 3600
}
```

**Usage Flow:**
1. 클라이언트가 `/api/v1/uploads/presign`을 호출하여 Presigned URL 발급
2. 클라이언트가 Presigned URL로 직접 S3에 파일 업로드
3. 업로드 완료 후 `file_key`를 사용하여 Task 생성

---

## 에러 응답

### 표준 에러 형식

```json
{
  "detail": "Error message",
  "error_code": "ITEM_NOT_FOUND",
  "timestamp": "2026-01-27T00:00:00Z"
}
```

### 주요 HTTP 상태 코드

| 코드 | 설명 |
|------|------|
| **200 OK** | 요청 성공 |
| **201 Created** | 리소스 생성 성공 |
| **204 No Content** | 삭제 성공 |
| **400 Bad Request** | 잘못된 요청 (스키마 검증 실패) |
| **401 Unauthorized** | 인증 실패 (토큰 없음/만료) |
| **403 Forbidden** | 권한 없음 |
| **404 Not Found** | 리소스 없음 |
| **422 Unprocessable Entity** | 유효성 검증 실패 |
| **500 Internal Server Error** | 서버 오류 |

---

## 인증 헤더 사용법

JWT 토큰이 필요한 엔드포인트는 다음과 같이 헤더를 포함해야 합니다:

```bash
curl -X GET "http://localhost:8000/api/v1/tasks" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## 페이지네이션

목록 조회 엔드포인트는 다음 쿼리 파라미터를 지원합니다:

- `skip`: 건너뛸 레코드 수 (default: 0)
- `limit`: 조회할 최대 레코드 수 (default: 50, max: 100)

**예시:**
```bash
GET /api/v1/items?skip=20&limit=10
```

---

## 참고 자료

- **OpenAPI 스펙**: http://localhost:8000/openapi.json
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **데이터베이스 스키마**: [database-schema.md](./database-schema.md)
- **데이터 수집 가이드**: [data-collection.md](./data-collection.md)

---

**작성일**: 2026-01-27
**버전**: 1.0.0
**API 버전**: v1
