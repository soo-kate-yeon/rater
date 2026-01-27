# SPEC-TOEFL-SCHEMA-001: 인수 조건

---
spec_id: SPEC-TOEFL-SCHEMA-001
title: TOEFL Speaking 정규화 데이터 스키마 확장 - 인수 조건
created: 2026-01-25
status: draft
priority: High
assigned: manager-spec
---

## HISTORY

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 1.0.0 | 2026-01-25 | manager-spec | 초기 인수 조건 작성 |

---

## 인수 조건 개요

이 문서는 SPEC-TOEFL-SCHEMA-001의 완료를 검증하기 위한 인수 조건을 정의합니다. 모든 테스트 시나리오는 Given-When-Then 형식을 따릅니다.

---

## 테스트 시나리오

### Feature: Set 모델 CRUD

#### Scenario: 새로운 Set 생성

```gherkin
Given 데이터베이스가 초기화되어 있고
  And 유효한 Set 데이터가 준비됨:
      | title          | source       | version |
      | ETS Practice 1 | ETS Official | v1.0    |

When POST /v1/sets 요청을 보내면

Then 응답 상태 코드는 201 Created이고
  And 응답 본문에 UUID 형식의 id가 포함되어 있고
  And 응답 본문에 created_at과 updated_at이 포함되어 있고
  And 데이터베이스에 해당 Set 레코드가 생성됨
```

#### Scenario: 중복 source-version 조합 방지

```gherkin
Given "ETS Official" source와 "v1.0" version의 Set이 이미 존재하고

When 동일한 source와 version으로 POST /v1/sets 요청을 보내면

Then 응답 상태 코드는 409 Conflict이고
  And 에러 메시지에 "duplicate" 관련 내용이 포함됨
```

#### Scenario: Set 삭제 시 연관 Item 연쇄 삭제

```gherkin
Given Set(id=set-1)이 존재하고
  And Item(id=item-1, set_id=set-1)이 존재하고
  And Stimulus(id=stim-1, item_id=item-1)이 존재하고

When DELETE /v1/sets/set-1 요청을 보내면

Then 응답 상태 코드는 204 No Content이고
  And 데이터베이스에서 Set(id=set-1)이 삭제되고
  And 데이터베이스에서 Item(id=item-1)이 삭제되고
  And 데이터베이스에서 Stimulus(id=stim-1)이 삭제됨
```

---

### Feature: Item 모델 CRUD

#### Scenario: Independent Item 생성 - 필수 필드 검증

```gherkin
Given Set(id=set-1)이 존재하고
  And 유효한 Independent Item 데이터가 준비됨:
      | set_id | task_type   | prompt                    | topic_type | topic_category |
      | set-1  | INDEPENDENT | Do you prefer A or B?     | preference | lifestyle      |

When POST /v1/items 요청을 보내면

Then 응답 상태 코드는 201 Created이고
  And 응답 본문의 task_no는 자동으로 1이 할당됨
  And 응답 본문의 prep_seconds 기본값은 15이고
  And 응답 본문의 response_seconds 기본값은 45임
```

#### Scenario: Independent Item 생성 - topic_type 누락 시 에러

```gherkin
Given Set(id=set-1)이 존재하고
  And Independent Item 데이터에 topic_type이 누락됨:
      | set_id | task_type   | prompt                |
      | set-1  | INDEPENDENT | Do you prefer A or B? |

When POST /v1/items 요청을 보내면

Then 응답 상태 코드는 422 Unprocessable Entity이고
  And 에러 메시지에 "topic_type is required for INDEPENDENT task" 내용이 포함됨
```

#### Scenario: Integrated Item 생성 - topic_type 선택적

```gherkin
Given Set(id=set-1)이 존재하고
  And Integrated Item 데이터가 준비됨:
      | set_id | task_type  | prompt                              |
      | set-1  | INTEGRATED | Summarize the points in the lecture |

When POST /v1/items 요청을 보내면

Then 응답 상태 코드는 201 Created이고
  And 응답 본문의 topic_type은 null임
```

#### Scenario: 동일 Set 내 task_no 자동 증가

```gherkin
Given Set(id=set-1)이 존재하고
  And Item(task_no=1, set_id=set-1)이 존재하고

When 새로운 Item을 Set(id=set-1)에 추가하면

Then 새 Item의 task_no는 2가 됨
```

---

### Feature: Stimulus 모델 CRUD

#### Scenario: Reading Stimulus 생성 - content_text 필수

```gherkin
Given Item(id=item-1)이 존재하고
  And Reading Stimulus 데이터가 준비됨:
      | item_id | kind    | content_text                    |
      | item-1  | reading | The university announced...     |

When POST /v1/stimuli 요청을 보내면

Then 응답 상태 코드는 201 Created이고
  And 응답 본문의 display_order 기본값은 0임
```

#### Scenario: Audio Stimulus 생성 - asset_url 및 duration_seconds 필수

```gherkin
Given Item(id=item-1)이 존재하고
  And Audio Stimulus 데이터에 duration_seconds가 누락됨:
      | item_id | kind  | asset_url                  |
      | item-1  | audio | s3://bucket/audio/001.mp3  |

When POST /v1/stimuli 요청을 보내면

Then 응답 상태 코드는 422 Unprocessable Entity이고
  And 에러 메시지에 "duration_seconds is required for audio stimulus" 내용이 포함됨
```

#### Scenario: Stimulus 순서 정렬

```gherkin
Given Item(id=item-1)이 존재하고
  And Stimulus(kind=direction, display_order=0)이 존재하고
  And Stimulus(kind=reading, display_order=1)이 존재하고
  And Stimulus(kind=audio, display_order=2)이 존재하고

When GET /v1/items/item-1/stimuli 요청을 보내면

Then 응답 본문의 stimuli 배열은 display_order 오름차순으로 정렬됨:
      | display_order | kind      |
      | 0             | direction |
      | 1             | reading   |
      | 2             | audio     |
```

---

### Feature: AnswerKey 모델 CRUD

#### Scenario: Sample Response AnswerKey 생성

```gherkin
Given Item(id=item-1)이 존재하고
  And Sample Response AnswerKey 데이터가 준비됨:
      | item_id | answer_type     | level | content                              |
      | item-1  | sample_response | high  | {"text": "In my opinion...", ...}   |

When POST /v1/answer-keys 요청을 보내면

Then 응답 상태 코드는 201 Created이고
  And 응답 본문의 content는 JSONB 형식으로 저장됨
```

#### Scenario: Blueprint AnswerKey - IntegratedBlueprint 스키마 검증

```gherkin
Given Item(id=item-1, task_type=INTEGRATED)이 존재하고
  And Blueprint AnswerKey 데이터가 IntegratedBlueprint 스키마를 따름:
      | item_id | answer_type | content                                    |
      | item-1  | blueprint   | {"schema_version": "1.0", "info_units": [...], ...} |

When POST /v1/answer-keys 요청을 보내면

Then 응답 상태 코드는 201 Created이고
  And content 필드가 IntegratedBlueprint 스키마로 검증됨
```

#### Scenario: Blueprint AnswerKey - 잘못된 스키마 거부

```gherkin
Given Item(id=item-1, task_type=INTEGRATED)이 존재하고
  And Blueprint AnswerKey 데이터가 잘못된 스키마를 포함함:
      | item_id | answer_type | content              |
      | item-1  | blueprint   | {"invalid_field": 1} |

When POST /v1/answer-keys 요청을 보내면

Then 응답 상태 코드는 422 Unprocessable Entity이고
  And 에러 메시지에 스키마 검증 실패 내용이 포함됨
```

---

### Feature: Blueprint Pydantic 스키마

#### Scenario: IntegratedBlueprint 유효성 검증 - 정상 케이스

```gherkin
Given 유효한 IntegratedBlueprint JSON이 준비됨:
      {
        "schema_version": "1.0",
        "info_units": [
          {"source": "reading", "label": "Main Point", "content": "The text discusses...", "importance": "essential"}
        ],
        "recommended_order": ["reading_main", "listening_example_1"],
        "linking_moves": [
          {"position": "transition_to_listening", "phrases": ["According to the lecture..."]}
        ],
        "coverage_expectations": {"reading": 0.3, "listening": 0.7},
        "time_budget": {
          "intro_seconds": 10,
          "reading_summary_seconds": 15,
          "listening_summary_seconds": 25,
          "conclusion_seconds": 5
        }
      }

When IntegratedBlueprint.model_validate(json_data)를 호출하면

Then ValidationError가 발생하지 않고
  And 모델 인스턴스가 정상적으로 생성됨
```

#### Scenario: IndependentBlueprint 유효성 검증 - 정상 케이스

```gherkin
Given 유효한 IndependentBlueprint JSON이 준비됨:
      {
        "schema_version": "1.0",
        "topic_type": "preference",
        "recommended_structure": ["intro", "reason_1", "example_1", "conclusion"],
        "linking_moves": [
          {"position": "intro", "phrases": ["In my opinion..."]}
        ],
        "score_expectations": {
          "structure_weight": 0.3,
          "language_weight": 0.4,
          "delivery_weight": 0.3
        },
        "topic_specific_vocabulary": ["prefer", "beneficial", "advantage"],
        "time_budget": {
          "intro_seconds": 10,
          "reading_summary_seconds": 0,
          "listening_summary_seconds": 0,
          "conclusion_seconds": 5
        }
      }

When IndependentBlueprint.model_validate(json_data)를 호출하면

Then ValidationError가 발생하지 않고
  And 모델 인스턴스가 정상적으로 생성됨
```

#### Scenario: TimeBudget 범위 검증

```gherkin
Given TimeBudget에 intro_seconds가 20인 데이터가 준비됨 (허용 범위: 5-15)

When TimeBudget.model_validate(json_data)를 호출하면

Then ValidationError가 발생하고
  And 에러 메시지에 "intro_seconds must be between 5 and 15" 내용이 포함됨
```

---

### Feature: 데이터베이스 마이그레이션

#### Scenario: 마이그레이션 적용

```gherkin
Given 현재 데이터베이스에 sets, items, stimuli, answer_keys 테이블이 없고

When alembic upgrade head 명령을 실행하면

Then sets 테이블이 생성되고
  And items 테이블이 생성되고
  And stimuli 테이블이 생성되고
  And answer_keys 테이블이 생성되고
  And 모든 인덱스가 정상적으로 생성됨
```

#### Scenario: 마이그레이션 롤백

```gherkin
Given sets, items, stimuli, answer_keys 테이블이 존재하고

When alembic downgrade -1 명령을 실행하면

Then 마지막 마이그레이션이 롤백되고
  And 관련 테이블이 삭제됨
```

---

### Feature: Enum 타입

#### Scenario: TopicType Enum 직렬화

```gherkin
Given Item 모델에 topic_type=TopicType.PREFERENCE가 설정되고

When JSON으로 직렬화하면

Then topic_type 값은 "preference" 문자열로 출력됨
```

#### Scenario: 잘못된 Enum 값 거부

```gherkin
Given Item 생성 요청에 topic_type="invalid_type"이 포함되고

When POST /v1/items 요청을 보내면

Then 응답 상태 코드는 422 Unprocessable Entity이고
  And 에러 메시지에 허용된 값 목록이 포함됨
```

---

## 품질 게이트 기준

### 테스트 커버리지

- [ ] **전체 커버리지**: 85% 이상
- [ ] **모델 커버리지**: 90% 이상
- [ ] **스키마 커버리지**: 95% 이상
- [ ] **API 라우터 커버리지**: 80% 이상

### 성능 기준

- [ ] **Set 목록 조회 (100개)**: < 100ms
- [ ] **Item 상세 조회 (Stimulus, AnswerKey 포함)**: < 50ms
- [ ] **Set 생성 (Item 4개 포함)**: < 200ms

### 코드 품질

- [ ] **Ruff 린터**: 에러 0개
- [ ] **MyPy 타입 체크**: 에러 0개
- [ ] **Black 포맷팅**: 변경 필요 없음

---

## 검증 방법

### 자동화 테스트

```bash
# 전체 테스트 실행
pytest tests/ -v --cov=src --cov-report=term-missing

# 모델 테스트
pytest tests/models/ -v

# 스키마 테스트
pytest tests/schemas/ -v

# API 테스트
pytest tests/api/ -v
```

### 수동 검증

1. **API 문서 확인**: http://localhost:8000/docs
2. **마이그레이션 테스트**: 개발 DB에서 upgrade/downgrade 실행
3. **데이터 무결성**: 연쇄 삭제 동작 확인

---

## Definition of Done

- [x] 모든 테스트 시나리오 통과
- [x] 테스트 커버리지 85% 이상
- [x] 코드 리뷰 완료
- [x] 마이그레이션 스크립트 검증 완료
- [x] API 문서 자동 생성 확인
- [x] 성능 기준 충족
- [x] SPEC-TOEFL-001과의 통합 테스트 완료

---

**작성자**: manager-spec
**검토자**: 수연
**버전**: 1.0.0
**최종 수정일**: 2026-01-25
