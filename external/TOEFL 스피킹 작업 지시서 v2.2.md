# TOEFL Speaking 40세트 → 엔진화 파이프라인 (Claude Agent 단일 작업 지시서) v2.2

> **Version History**: 
> - v2.0: ETS SpeechRater 채점 체계 리서치 내용을 기반으로 루브릭 및 Feature Map 섹션 전면 업데이트
> - v2.1: **유저 피드백 스키마(User Feedback Schema)** 추가 - 앱 유저가 받는 결과물 정의
> - v2.2: **Independent Speaking (Q1)** 토픽 뱅크 및 별도 Blueprint 스키마 추가

## 0) 목적
내부에 보유한 TOEFL Speaking 연습자료(약 40세트)를 **외부에 재배포하지 않고**(내부 분석/개발용) 다음을 가능하게 하는 **문항·자극자료·모범답안·구조(blueprint)·루브릭(feature)** 기반 데이터셋으로 변환한다.

이번 작업의 핵심 목표는:
- 앱이 바로 로딩할 수 있는 **문항 세트 데이터(JSON/Excel)** 생성
- 각 문항에 대해 **모범 답안 "구조(blueprint)"**를 추출하여 피드백 엔진의 근거로 사용
- 기존 자료의 "수준별 모범답안"을 바탕으로 **Topic(구조) & Delivery(발화 특성)** 평가 준비(feature map)까지 연결
- **ETS SpeechRater 채점 체계**를 참조하여 실제 TOEFL 채점 기준에 부합하는 Feature 정의

> 주의: 원문/오디오/스크립트는 **외부 배포용으로 사용하지 않는다**. 본 산출물은 내부 테스트/학습/개발용 데이터 구조 확립이 목적이다.

---

## 1) 입력 자료
### A. Integrated Speaking 자료 (Q2~Q4)
- `Speaking Actual Test 1~110.pdf` — 통합형 문항, reading/listening 자극자료, 수준별 모범답안
- `Speaking 스크립트 및 수정별.pdf` — listening script 및 수준별 샘플 응답

### B. Independent Speaking 자료 (Q1) - NEW
- `Independent_Topics.pdf` — 독립형 말하기 토픽 질문 모음 (약 300+ 토픽)
  - Preference 유형: "Do you prefer A or B?"
  - Agree/Disagree 유형: "Do you agree with the statement that...?"
  - Description 유형: "Describe a time when..."
  - Opinion 유형: "What do you think about...?"

각 PDF에는 Speaking 문항, reading material, listening script(또는 오디오 스크립트), 수준별 모범답안 등이 포함되어 있다.

---

## 2) 최종 산출물(Deliverables)
아래 6개 산출물을 **데이터 형태로** 만든다.

### D1) Independent 문항 데이터 (Q1 독립형 말하기) - EXPANDED
- Independent Task(Q1)의 문항 텍스트(질문/지시문)
- 준비/응답 시간 (15초 준비, 45초 응답)
- **토픽 유형 분류**: preference | agree_disagree | description | opinion | hypothetical
- **주제 카테고리**: education, technology, lifestyle, work, relationships, society 등
- 세트/문항 ID, 태그, 난이도 포함
- **권장 답변 구조(Blueprint)**: 주장-이유-예시 패턴

### D2) Integrated 문항 구성요소 데이터
Integrated(통상 Q3~Q4 Read+Listen, 필요 시 Q5~Q6 Listen-only 포함)의 구성요소:
- Reading material(지문) (해당 시)
- Listening script(텍스트)
- Direction(지시문)
- Question/Prompt(질문)
- 타이밍(준비/응답)

> 앱이 Q1~Q4만 사용하더라도 데이터 스키마는 Q1~Q6까지 확장 가능하게 설계한다.

### D3) 각 문항의 모범 답안 구조(blueprint)
- "모범답안 텍스트"가 아니라 **답변 구조**를 JSON으로 저장
- 정보 유닛(info units), 추천 순서, 연결 방식(linking moves), 점수대별 커버리지 기대치(예: 20/23/26), 시간배분(time budget)

### D4) ETS SpeechRater 기반 채점 루브릭 (Scoring Rubric)
- ETS SpeechRater v5.0에서 사용하는 20개 핵심 Feature 정의 및 가중치
- Delivery(Fluency, Pronunciation, Prosody/Rhythm) + Language Use(Grammar, Vocabulary) + Topic Development 구조
- 각 Feature의 정의, 측정방법, 권장범위, 실패패턴 포함

### D5) 루브릭 반영 준비: Topic/Delivery Feature Map
- D3 blueprint에서 역으로 도출한 **측정 가능한(feature)** 항목 정의
- Topic(구조) feature + Delivery(발화 특성) feature를 각각 정의/측정방법/권장범위/실패패턴 포함
- **발음/억양 피처는 외부 ASR 엔진 연동을 전제로 구조만 정의**

### D6) 유저 피드백 스키마 (User Feedback Schema) - NEW
- 앱 유저가 응답 제출 후 받게 되는 **피드백 데이터 구조** 표준 정의
- 점수(총점/영역별), 강점/약점 피드백, Blueprint 비교 결과, 개선 팁 포함
- UI 컴포넌트와 매핑 가능한 구조화된 JSON 포맷
- 피드백 상세도 레벨(Basic/Standard/Premium) 정의

---

## 3) 데이터 스키마(정규화) — JSON 또는 Excel(3시트)
핵심 원칙: `items(문항)`과 `stimuli(자극자료)`와 `answer_keys(모범답안/구조)`를 분리한다.

### 3.1 Set (문제 세트)
```yaml
set:
  set_id: string              # 예: "ACTUAL_TEST_01"
  title: string               # 예: "Speaking Actual Test 1"
  source: string              # 예: "internal_pdf"
  version: string             # 예: "1.0.0"
  created_at: string          # ISO datetime (optional)
  updated_at: string          # ISO datetime (optional)
```

### 3.2 Item (개별 문항: Q1~Q6)
```yaml
item:
  item_id: string             # 예: "ACTUAL_TEST_01_Q3" 또는 "INDEP_TOPIC_001"
  set_id: string              # FK (Independent는 "INDEPENDENT_BANK")
  task_no: integer            # 1~6
  task_type: enum             # independent | integrated_read_listen | integrated_listen_only
  prompt: string              # 질문(지시문 일부가 섞여 있으면 prompt에 포함 가능)
  prep_seconds: integer       # 15/20/30...
  response_seconds: integer   # 45/60...
  language: string            # "en"
  tags: string[]              # ["campus", "opinion", "summarize", ...]
  difficulty: integer|null    # 1~5 등 (optional)
  scoring_focus: object|null  # optional (예: {"delivery":0.4,"language_use":0.3,"topic_development":0.3})
  
  # === Independent Speaking 전용 필드 (NEW) ===
  topic_type: enum|null       # preference | agree_disagree | description | opinion | hypothetical
  topic_category: string|null # education | technology | lifestyle | work | relationships | society
  question_pattern: string|null  # "Do you prefer A or B?" | "Do you agree that...?" 등
```

#### 3.2.1 Independent Topic Types 상세

| topic_type | 설명 | 예시 질문 패턴 |
|------------|------|---------------|
| `preference` | 두 가지 중 선호 선택 | "Do you prefer A or B?" |
| `agree_disagree` | 진술에 대한 동의/반대 | "Do you agree with the statement that...?" |
| `description` | 경험/사물/사람 묘사 | "Describe a time when..." |
| `opinion` | 의견 제시 | "What do you think about...?" |
| `hypothetical` | 가상 상황 대응 | "If you could..., what would you...?" |

#### 3.2.2 Topic Categories

| category | 포함 주제 |
|----------|----------|
| `education` | 학교, 대학, 학습 방법, 교육 정책 |
| `technology` | 인터넷, SNS, 디지털 기기, AI |
| `lifestyle` | 음식, 패션, 취미, 건강 |
| `work` | 직업, 커리어, 직장 생활 |
| `relationships` | 친구, 가족, 연인, 사회적 관계 |
| `society` | 환경, 정치, 경제, 문화 |

### 3.3 Stimulus (자극자료)
```yaml
stimulus:
  stimulus_id: string
  item_id: string             # FK
  kind: enum                  # reading | audio | image | direction
  title: string
  content_text: string|null   # reading 전문 / listening script 전문 / direction 텍스트
  asset_url: string|null      # 오디오 파일 경로(있다면)
  duration_seconds: integer|null
  order: integer              # 표시 순서(1=reading, 2=audio, 3=question 등)
  notes_allowed: boolean
```

### 3.4 AnswerKey (모범답안/해설/구조)
```yaml
answer_key:
  answer_id: string
  item_id: string             # FK
  type: enum                  # sample_response | transcript | outline | points | blueprint
  level: string|null          # "high"|"mid"|"low" 또는 "20"|"23"|"26" 등
  content: string             # 텍스트(blueprint는 JSON 문자열)
  source: string|null         # "internal_pdf" 등
```

---

## 4) Blueprint(모범 답안 구조) 표준 JSON 스키마

### 4.1 Integrated Speaking Blueprint (Q2~Q4)
`answer_keys.type = "blueprint"`의 `content`로 저장한다.

```json
{
  "info_units": [
    {"id":"U1","role":"main_point|detail|example|definition|stance","source":"reading|listening|speaker","summary":"..."}
  ],
  "recommended_order": ["U1","U2","U3"],
  "linking_moves": [
    {"type":"contrast|cause_effect|example|summary","marker_suggestions":["however","for example"]}
  ],
  "coverage_expectations": {
    "20": {"must_include":["U1"],"nice_to_have":["U2"],"common_failures":["missing example"]},
    "23": {"must_include":["U1","U2"],"nice_to_have":["U3"],"common_failures":["weak linkage"]},
    "26": {"must_include":["U1","U2","U3"],"nice_to_have":[],"common_failures":[]}
  },
  "time_budget": {
    "opening_sec": 5,
    "unit_sec": {"U1": 15, "U2": 20, "U3": 15},
    "closing_sec": 5
  }
}
```

### 4.2 Independent Speaking Blueprint (Q1) - NEW
독립형 말하기는 reading/listening 자료가 없으므로 **"권장 답변 구조"** 형태로 저장한다.

```json
{
  "topic_type": "preference|agree_disagree|description|opinion|hypothetical",
  "recommended_structure": {
    "pattern": "position_reason_example",  // 또는 "reason_example_reason_example"
    "components": [
      {"id":"C1","role":"position","description":"Clear statement of your choice/opinion","time_sec":5},
      {"id":"C2","role":"reason_1","description":"First reason supporting your position","time_sec":12},
      {"id":"C3","role":"example_1","description":"Specific example/detail for reason 1","time_sec":10},
      {"id":"C4","role":"reason_2","description":"Second reason (optional but recommended)","time_sec":10},
      {"id":"C5","role":"example_2","description":"Specific example/detail for reason 2","time_sec":8}
    ]
  },
  "linking_moves": [
    {"position":"after_position","type":"transition_to_reason","marker_suggestions":["The main reason is...","First of all,..."]},
    {"position":"after_reason_1","type":"introduce_example","marker_suggestions":["For example,...","For instance,..."]},
    {"position":"after_example_1","type":"transition_to_reason_2","marker_suggestions":["Additionally,...","Another reason is...","Also,..."]},
    {"position":"closing","type":"conclusion","marker_suggestions":["That's why I...","For these reasons,...","So overall,..."]}
  ],
  "score_expectations": {
    "20": {
      "structure": "position + 1 reason (vague)",
      "common_issues": ["unclear position","no specific examples","repetitive language","long pauses"],
      "example_response_pattern": "I prefer A because it's good. A is better than B."
    },
    "23": {
      "structure": "position + 1-2 reasons + some examples",
      "common_issues": ["examples lack specificity","weak transitions","some hesitation"],
      "example_response_pattern": "I prefer A for two reasons. First, A helps me... For example, when I... Second, A is also..."
    },
    "26": {
      "structure": "position + 2 clear reasons + specific examples + smooth delivery",
      "common_issues": ["minor hesitations only"],
      "example_response_pattern": "I definitely prefer A over B, mainly for two reasons. The first reason is that... Let me give you an example. Last month, I... Additionally, A allows me to... For instance,... That's why I strongly prefer A."
    }
  },
  "topic_specific_vocabulary": [
    {"category":"transitions","words":["first of all","additionally","moreover","on top of that"]},
    {"category":"examples","words":["for example","for instance","such as","like when"]},
    {"category":"opinions","words":["I believe","I think","in my opinion","from my perspective"]}
  ],
  "time_budget": {
    "position_sec": 5,
    "body_sec": 35,
    "conclusion_sec": 5,
    "total_sec": 45
  }
}
```

#### 4.2.1 Independent Blueprint - topic_type별 권장 구조

| topic_type | 권장 pattern | 필수 components |
|------------|-------------|-----------------|
| `preference` | position_reason_example | position → reason1 → example1 → (reason2 → example2) |
| `agree_disagree` | position_reason_example | clear stance → reason1 → example1 → reason2 → example2 |
| `description` | intro_detail_detail | intro → detail1 → detail2 → detail3 → wrap-up |
| `opinion` | position_reason_example | opinion → reason1 → example1 → (reason2) |
| `hypothetical` | condition_action_reason | state condition → describe action → explain why |

### 4.3 Blueprint 제약사항 (공통)
- 추가 키 금지(스키마 엄격 준수)
- role/source/type은 enum 범위 내에서만 사용
- Independent blueprint의 `topic_type`은 item의 `topic_type`과 일치해야 함

---

## 5) ETS SpeechRater 채점 체계 참조 (NEW)

### 5.1 SpeechRater 개요
ETS의 SpeechRater는 TOEFL Speaking 자동 채점 시스템으로, 응시자의 음성 응답을 ASR(자동 음성 인식)로 처리한 후 다양한 음성/언어 특성을 추출하고 통계 모델(선형 회귀)로 점수를 예측한다.

**채점 공식**: `Score = β₀ + Σ(βᵢ × fᵢ)`

SpeechRater v5.0은 100개 이상의 raw feature 중 최적화된 **20개 핵심 feature**를 사용하여 TOEFL 채점 rubric의 모든 주요 차원(Delivery, Language Use, Topic Development)을 커버한다.

### 5.2 Feature 카테고리 및 상대적 가중치

| 카테고리 | 하위 영역 | 상대적 가중치 합계 |
|---------|----------|-------------------|
| **Delivery** | Fluency | ~38% |
| | Pronunciation | ~12% |
| | Prosody/Rhythm | ~14% |
| **Language Use** | Grammar | ~6% |
| | Vocabulary | ~20% |
| **Topic Development** | Content/Discourse | (개발 중, ~10% 추정) |

### 5.3 SpeechRater v5.0 핵심 20개 Feature 상세

#### A. Fluency Features (Delivery - 약 38%)

| Feature Code | 한글명 | 정의 | 상대 가중치 | 점수 영향 |
|-------------|--------|------|------------|----------|
| `silmean` | 평균 침묵 길이 | 응답 중 침묵(pause)의 평균 길이(초) | 0.119 | 음(-)* |
| `wpsec` | 발화 속도 | 초당 단어 수 (Words Per Second) | 0.097 | 양(+) |
| `secpchk` | 평균 청크 길이 | 침묵 사이 발화 구간(run)의 평균 길이(초) | 0.066 | 양(+) |
| `numrep` | 반복 횟수 | 단어/구문 반복(재시작) 횟수 | 0.061 | 음(-) |
| `numdff` | 비유창성 횟수 | 필러(uh, um), 거짓 시작 등 비유창성 횟수 | 0.056 | 음(-) |
| `silpsecutt` | 침묵 빈도 | 초당 침묵 발생 횟수 | 0.056 | 음(-) |
| `IPC` | 절 내 중단 | 절(clause) 내 중단/재구성 횟수 | 0.012 | 음(-) |
| `withinClauseSilMean` | 절 내 침묵 평균 | 절 내부에서 발생하는 침묵의 평균 길이 | 0.008 | 음(-) |

> *음(-): 값이 클수록 점수 하락 / 양(+): 값이 클수록 점수 상승

#### B. Pronunciation Features (Delivery - 약 12%)

| Feature Code | 한글명 | 정의 | 상대 가중치 | 점수 영향 |
|-------------|--------|------|------------|----------|
| `L1` | 원어민 음향모델 점수 | 원어민 영어 음향모델의 로그 우도(log-likelihood) 총합 | 0.081 | 양(+) |
| `amscore` | 비원어민 음향모델 점수 | 비원어민 영어 음향모델의 로그 우도 총합 | 0.038 | 양(+) |

#### C. Prosody & Rhythm Features (Delivery - 약 14%)

| Feature Code | 한글명 | 정의 | 상대 가중치 | 점수 영향 |
|-------------|--------|------|------------|----------|
| `powstddev` | 음량 변화량 | 프레임별 파워(음량)의 표준편차 | 0.057 | 양(+) |
| `pitdeltanorm` | 피치 범위 | 정규화된 피치 변화 범위 | 0.028 | 양(+) |
| `phn_shift` | 모음 지속시간 편차 | 기대 모음 길이 대비 평균 절대 편차 | 0.014 | 음(-) |
| `rpvic` | 자음 간격 PVI | 자음 간격의 Raw Pairwise Variability Index | 0.028 | 양(+) |
| `stresyllmdev` | 강세 음절 타이밍 편차 | 강세 음절 간 간격의 평균 편차 | 0.014 | 음(-) |

#### D. Grammar Features (Language Use - 약 6%)

| Feature Code | 한글명 | 정의 | 상대 가중치 | 점수 영향 |
|-------------|--------|------|------------|----------|
| `poscvamax` | POS 문법 유사도 | POS n-gram 기반 문법 프로파일의 최대 유사도 점수 | 0.062 | 양(+) |
| `dep_clauses_per_clause` | 절당 종속절 수 | 절당 평균 종속절(dependent clause) 수 | 0.001 | 양(+) |

#### E. Vocabulary Features (Language Use - 약 20%)

| Feature Code | 한글명 | 정의 | 상대 가중치 | 점수 영향 |
|-------------|--------|------|------------|----------|
| `cvamax` | 어휘 CVA 점수 | Content Vector Analysis 기반 어휘 사용 유사도 최대값 | 0.099 | 양(+) |
| `types` | 고유 단어 수 | 응답 내 고유 단어 타입 수 | 0.061 | 양(+) |
| `logFreq` | 평균 단어 빈도 | 단어들의 평균 로그 빈도 (낮을수록 고급 어휘) | 0.042 | 음(-) |

#### F. Content & Discourse Features (Topic Development - 개발 중)

현재 SpeechRater v5.0에서는 Content/Discourse feature가 완전히 통합되지 않았으나, 연구 단계에서 다음 feature들이 검토됨:

| Feature 유형 | 설명 | 상태 |
|-------------|------|------|
| Content Relevance (CVA) | 프롬프트별 기대 내용과의 의미적 유사도 | 연구 중 |
| Discourse Connectives | 담화 연결어(first, however, therefore) 사용 빈도 | 연구 중 |
| Pronoun-Noun Ratio | 대명사/명사 비율 (응집성 지표) | 연구 중 |
| Connective Chains | 연결어 패턴의 고득점 응답과의 유사도 | 연구 중 |

### 5.4 채점 모델 성능

| 지표 | 값 |
|-----|-----|
| 시스템-인간 상관계수 (개별 응답) | r = 0.557 |
| 시스템-인간 상관계수 (총점) | r = 0.77 |
| 인간-인간 상관계수 (참조) | r = 0.59 |
| 평균 점수 편차 | -0.02 (무시 가능) |

---

## 6) Excel 저장 형식(권장: 4시트)

### Sheet A) `items`
- set_id, item_id, task_no, task_type, prompt, prep_seconds, response_seconds, tags, difficulty

### Sheet B) `stimuli`
- stimulus_id, item_id, kind, title, content_text, asset_url, duration_seconds, order, notes_allowed

### Sheet C) `answer_keys`
- answer_id, item_id, type, level, content, source

### Sheet D) `rubric_features` (NEW)
- feature_code, category, subcategory, name_ko, definition, measurement_method, good_range, failure_modes, relative_weight, score_direction

---

## 7) Claude Agent 작업 범위(What to do)

### Step 1-A) Integrated Speaking: PDF에서 세트/문항 단위로 추출
각 문항을 Q2~Q4 단위로 분리하여 다음을 추출한다:
- prompt/question
- direction(지시문)
- reading text(해당 시)
- listening script(해당 시)
- sample responses(수준별/점수대별)

출력:
- `items` 레코드 (task_type: integrated_*)
- `stimuli` 레코드(reading/audio/direction)
- `answer_keys` 레코드(sample_response/transcript/points 등)

### Step 1-B) Independent Speaking: 토픽 뱅크 구조화 (NEW)
`Independent_Topics.pdf`에서 Q1 토픽들을 추출하여 구조화한다:

**추출 항목:**
- prompt 원문
- topic_type 분류 (preference/agree_disagree/description/opinion/hypothetical)
- topic_category 분류 (education/technology/lifestyle/work/relationships/society)
- question_pattern 식별

**분류 규칙:**
```
"Do you prefer A or B?" → topic_type: preference
"Do you agree/disagree..." → topic_type: agree_disagree  
"Describe a time when..." → topic_type: description
"What do you think about..." → topic_type: opinion
"If you could..., what would..." → topic_type: hypothetical
```

출력:
- `items` 레코드 (task_type: independent, set_id: "INDEPENDENT_BANK")
- **No stimuli** (Independent는 자극자료 없음)

### Step 2-A) Integrated: 모범답안 구조(blueprint) 생성
각 문항별로 (reading + listening script + sample responses)를 입력으로 받아 **Integrated Blueprint 표준 JSON**을 생성한다.

### Step 2-B) Independent: 권장 답변 구조(blueprint) 생성 (NEW)
각 Independent 토픽의 topic_type에 맞는 **Independent Blueprint 표준 JSON**을 생성한다.

**핵심 차이점:**
- Integrated: "정답"이 있음 (reading/listening에서 추출해야 할 정보)
- Independent: "정답" 없음 → **"좋은 답변의 구조"** 를 정의

출력:
- `answer_keys`에 `type="blueprint"` 레코드 추가

### Step 3) SpeechRater 기반 Feature Map 생성 (Topic/Delivery)
각 blueprint를 입력으로 받아 다음을 생성한다:

**A. Delivery Features (발음/억양 제외, 전사 기반)**
- `wpm_estimate`: 단어 수 / 응답 시간으로 추정
- `pause_markers`: "[pause]" 등 전사 마커 기반 침묵 추정
- `filler_count`: "uh", "um", "like" 등 필러 단어 수
- `repetition_count`: 단어/구문 반복 수
- `restart_count`: 거짓 시작, 자기 수정 수

**B. Topic Features (구조/내용)**
- `coverage_ratio`: blueprint info_units 중 커버된 비율
- `order_similarity`: 권장 순서와의 일치도 (0~1)
- `linking_marker_rate`: 담화 연결어 사용 빈도
- `redundancy_score`: 불필요한 반복/중복 정도
- `off_topic_flag`: 주제 이탈 여부

**C. Language Use Features (어휘/문법)**
- `type_token_ratio`: 고유 단어 / 총 단어
- `avg_word_length`: 평균 단어 길이
- `advanced_vocab_ratio`: 고급 어휘 비율 (빈도 기준)
- `clause_complexity`: 평균 절 길이 / 종속절 비율

출력:
- `rubric_maps.json` 파일(또는 set-level 메타데이터)

### Step 4) 피드백 템플릿 및 메시지 뱅크 생성 (NEW)
각 feature와 점수대별로 유저에게 제공할 피드백 메시지를 생성한다:

**A. Summary 템플릿**
- 점수대별(high/mid/low) 요약 메시지 3개씩

**B. Feature별 피드백 메시지**
- 각 feature의 good/acceptable/needs_work 상태별 메시지
- 구체적인 개선 팁 포함

**C. Next Steps 추천**
- 점수대별 우선 개선 영역 추천 로직

출력:
- `feedback_templates.json` 파일

---

## 8) Claude Agent 프롬프트 템플릿

### Prompt A-1) Integrated Answer → Blueprint 추출기
```text
You are a TOEFL speaking analysis agent.
Goal: extract a rubric-aligned ANSWER BLUEPRINT (structure) from multiple sample answers.

INPUTS:
- Task type: {task_type}
- Reading (optional): """{reading_text}"""
- Listening script (optional): """{listening_script}"""
- Question/direction: """{prompt_or_direction}"""
- Sample answers by level:
  - L20: """{ans_20}"""
  - L23: """{ans_23}"""
  - L26: """{ans_26}"""

INSTRUCTIONS:
1) Identify atomic INFORMATION UNITS from reading/listening that appear in answers.
2) Create a recommended order for a high-scoring response.
3) For each band (20/23/26), specify must_include units, typical omissions, and typical logical/structural issues.
4) Include time_budget guidance for a 60-second response (or the task's response time).
5) Output JSON ONLY matching this schema:
{
 "info_units":[{"id":"U1","role":"main_point|detail|example|definition|stance","source":"reading|listening|speaker","summary":"..."}],
 "recommended_order":["U1","U2"],
 "linking_moves":[{"type":"contrast|cause_effect|example|summary","marker_suggestions":["..."]}],
 "coverage_expectations":{
   "20":{"must_include":["U1"],"nice_to_have":["U2"],"common_failures":["..."]},
   "23":{"must_include":["U1","U2"],"nice_to_have":["U3"],"common_failures":["..."]},
   "26":{"must_include":["U1","U2","U3"],"nice_to_have":[],"common_failures":["..."]}
 },
 "time_budget":{"opening_sec":5,"unit_sec":{"U1":15},"closing_sec":5}
}
No extra keys. No commentary.
```

### Prompt A-2) Independent Topic → Blueprint 생성기 (NEW)
```text
You are a TOEFL Independent Speaking structure design agent.
Goal: generate a recommended answer BLUEPRINT for an Independent Speaking question (Q1).

INPUT:
- Question prompt: """{prompt}"""
- Topic type: {topic_type}  // preference | agree_disagree | description | opinion | hypothetical
- Topic category: {topic_category}  // education | technology | lifestyle | work | relationships | society
- Response time: 45 seconds

INSTRUCTIONS:
1) Analyze the question to determine the ideal response structure.
2) For preference/agree_disagree: structure should include clear position + 2 reasons with examples.
3) For description: structure should include intro + 2-3 specific details/aspects.
4) For opinion/hypothetical: structure should include position + reasoning + examples.
5) Provide linking moves appropriate for this topic type.
6) Define score expectations (what makes a 20/23/26 response for THIS specific question).

OUTPUT JSON ONLY:
{
  "topic_type": "preference|agree_disagree|description|opinion|hypothetical",
  "recommended_structure": {
    "pattern": "position_reason_example",
    "components": [
      {"id":"C1","role":"position","description":"...","time_sec":5},
      {"id":"C2","role":"reason_1","description":"...","time_sec":12},
      {"id":"C3","role":"example_1","description":"...","time_sec":10},
      {"id":"C4","role":"reason_2","description":"...","time_sec":10},
      {"id":"C5","role":"example_2","description":"...","time_sec":8}
    ]
  },
  "linking_moves": [
    {"position":"after_position","type":"transition_to_reason","marker_suggestions":["..."]},
    {"position":"after_example_1","type":"transition_to_reason_2","marker_suggestions":["..."]},
    {"position":"closing","type":"conclusion","marker_suggestions":["..."]}
  ],
  "score_expectations": {
    "20": {"structure":"...","common_issues":["..."]},
    "23": {"structure":"...","common_issues":["..."]},
    "26": {"structure":"...","common_issues":["..."]}
  },
  "topic_specific_vocabulary": [
    {"category":"domain","words":["relevant","topic","specific","words"]}
  ],
  "time_budget": {
    "position_sec": 5,
    "body_sec": 35,
    "conclusion_sec": 5,
    "total_sec": 45
  },
  "sample_high_score_outline": "I prefer A because [reason1]. For example, [specific example]. Also, [reason2]. [brief conclusion]."
}

GUIDELINES:
- Be specific to THIS topic (e.g., for "Do you prefer paper books or ebooks?", include vocabulary like "physical pages", "eye strain", "portability")
- Score expectations should reflect what's realistic for a 45-second response
- The sample_high_score_outline should be a template, not a full response
No extra keys. No commentary.
```

### Prompt B) Blueprint → SpeechRater 기반 Feature Map 생성기 (UPDATED)
```text
You are a scoring-feature design agent aligned with ETS SpeechRater methodology.
Given an answer blueprint JSON, propose measurable features for three scoring dimensions:
1) Delivery (fluency aspects only - pronunciation/prosody require audio)
2) Language Use (vocabulary and grammar)
3) Topic Development (content coverage and coherence)

INPUT BLUEPRINT:
{blueprint_json}

REFERENCE - SpeechRater v5.0 Feature Weights:
- Fluency (~38%): silmean(0.119), wpsec(0.097), secpchk(0.066), numrep(0.061), numdff(0.056), silpsecutt(0.056)
- Pronunciation (~12%): L1(0.081), amscore(0.038) [requires audio - mark as external]
- Prosody (~14%): powstddev(0.057), pitdeltanorm(0.028), rpvic(0.028), phn_shift(0.014), stresyllmdev(0.014) [requires audio]
- Grammar (~6%): poscvamax(0.062), dep_clauses_per_clause(0.001)
- Vocabulary (~20%): cvamax(0.099), types(0.061), logFreq(0.042)

OUTPUT JSON ONLY:
{
 "delivery_features":[
   {"name":"wpm_estimate","speechrater_analog":"wpsec","definition":"...","how_to_measure":"...","good_range":"120-150 wpm","failure_modes":["..."],"requires_audio":false},
   {"name":"pause_ratio","speechrater_analog":"silmean","definition":"...","how_to_measure":"...","good_range":"<15%","failure_modes":["..."],"requires_audio":false},
   {"name":"filler_rate","speechrater_analog":"numdff","definition":"...","how_to_measure":"...","good_range":"<3 per response","failure_modes":["..."],"requires_audio":false},
   {"name":"repetition_rate","speechrater_analog":"numrep","definition":"...","how_to_measure":"...","good_range":"<2 per response","failure_modes":["..."],"requires_audio":false}
 ],
 "pronunciation_features":[
   {"name":"native_acoustic_score","speechrater_analog":"L1","definition":"Native acoustic model log-likelihood","how_to_measure":"External ASR engine required","good_range":"model-dependent","failure_modes":["heavy accent","mispronunciation"],"requires_audio":true},
   {"name":"intelligibility_score","speechrater_analog":"amscore","definition":"Non-native acoustic model confidence","how_to_measure":"External ASR engine required","good_range":"model-dependent","failure_modes":["unintelligible segments"],"requires_audio":true}
 ],
 "prosody_features":[
   {"name":"pitch_variation","speechrater_analog":"pitdeltanorm","definition":"Range of pitch variation","how_to_measure":"External audio analysis required","good_range":"appropriate for statement/question","failure_modes":["monotone","unnatural intonation"],"requires_audio":true},
   {"name":"stress_timing","speechrater_analog":"stresyllmdev","definition":"Regularity of stressed syllable intervals","how_to_measure":"External audio analysis required","good_range":"consistent rhythm","failure_modes":["irregular stress","syllable-timed pattern"],"requires_audio":true}
 ],
 "language_use_features":[
   {"name":"type_token_ratio","speechrater_analog":"types","definition":"...","how_to_measure":"...","good_range":"0.4-0.6","failure_modes":["..."],"requires_audio":false},
   {"name":"avg_word_frequency","speechrater_analog":"logFreq","definition":"...","how_to_measure":"...","good_range":"lower is better (advanced vocab)","failure_modes":["..."],"requires_audio":false},
   {"name":"clause_complexity","speechrater_analog":"dep_clauses_per_clause","definition":"...","how_to_measure":"...","good_range":"0.3-0.5 dependent clauses/clause","failure_modes":["..."],"requires_audio":false}
 ],
 "topic_features":[
   {"name":"coverage_ratio","speechrater_analog":"cvamax(proxy)","definition":"Ratio of blueprint info_units mentioned","how_to_measure":"...","good_range":"0.8+ for 26","failure_modes":["..."],"requires_audio":false},
   {"name":"order_similarity","speechrater_analog":"none","definition":"...","how_to_measure":"...","good_range":"0.7+","failure_modes":["..."],"requires_audio":false},
   {"name":"discourse_marker_usage","speechrater_analog":"experimental","definition":"...","how_to_measure":"...","good_range":"3-5 per response","failure_modes":["..."],"requires_audio":false}
 ]
}

Constraints:
- All features must specify requires_audio: true/false
- features with requires_audio:false must be computable from transcript alone
- Include speechrater_analog to show alignment with ETS methodology
- pronunciation and prosody features should all have requires_audio:true
```

### Prompt C) 점수대별 기대치 생성기 (NEW)
```text
You are a TOEFL scoring calibration agent.
Given the SpeechRater feature definitions and a specific task's blueprint, generate score-band expectations.

INPUT:
- Blueprint: {blueprint_json}
- Task type: {task_type}
- Response time: {response_seconds} seconds

Generate expectations for each score band (20/23/26 out of 30):

OUTPUT JSON:
{
  "score_band_expectations": {
    "20": {
      "delivery": {
        "wpm_range": "90-110",
        "pause_tolerance": "up to 25% silence",
        "filler_tolerance": "5-8 per response",
        "typical_issues": ["frequent hesitations", "slow pace", "many restarts"]
      },
      "language_use": {
        "vocabulary": "basic, high-frequency words",
        "grammar": "simple sentences, some errors",
        "typical_issues": ["limited vocabulary", "repetitive structures"]
      },
      "topic_development": {
        "coverage": "50-70% of key points",
        "organization": "partially organized",
        "typical_issues": ["missing key information", "weak connections"]
      }
    },
    "23": {
      "delivery": {
        "wpm_range": "110-130",
        "pause_tolerance": "up to 18% silence",
        "filler_tolerance": "3-5 per response",
        "typical_issues": ["occasional hesitations", "some restarts"]
      },
      "language_use": {
        "vocabulary": "adequate range, some advanced words",
        "grammar": "mix of simple and complex, minor errors",
        "typical_issues": ["inconsistent complexity", "occasional awkward phrasing"]
      },
      "topic_development": {
        "coverage": "70-85% of key points",
        "organization": "generally well-organized",
        "typical_issues": ["some points underdeveloped", "transitions could be smoother"]
      }
    },
    "26": {
      "delivery": {
        "wpm_range": "130-150",
        "pause_tolerance": "up to 12% silence",
        "filler_tolerance": "0-2 per response",
        "typical_issues": ["minor hesitations only"]
      },
      "language_use": {
        "vocabulary": "varied, precise, some academic/advanced",
        "grammar": "complex structures, minimal errors",
        "typical_issues": ["rare minor errors"]
      },
      "topic_development": {
        "coverage": "85-100% of key points",
        "organization": "well-organized with clear transitions",
        "typical_issues": ["minor omissions at most"]
      }
    }
  }
}
```

---

## 9) 품질 체크(Validation)
- 모든 `item_id`, `stimulus_id`, `answer_id`는 유니크
- 각 item은 최소한 prompt를 갖는다
- `integrated_read_listen` item은 reading + (audio script) 존재
- `integrated_listen_only` item은 (audio script) 존재
- blueprint JSON은 정확히 표준 스키마 키만 포함(추가 키 금지)
- tags는 최소 1개 이상
- **NEW**: feature map의 모든 feature는 `requires_audio` 필드를 포함
- **NEW**: `speechrater_analog` 필드가 유효한 SpeechRater feature code를 참조하거나 "none"/"experimental"

---

## 10) 최종 출력 파일 권장

### JSON 출력
- `toefl_speaking_sets.json`  (set/items/stimuli/answer_keys 포함 - Integrated)
- `independent_topics.json`    (Independent Q1 토픽 뱅크 - NEW)
- `rubric_features.json`       (SpeechRater 기반 feature 정의)
- `rubric_maps.json`           (task별 topic_features/delivery_features)
- `score_band_expectations.json` (점수대별 기대치)
- `feedback_templates.json`    (피드백 메시지 템플릿)
- `user_feedback_schema.json`  (유저 피드백 스키마 정의)

### Excel 출력(선택)
- `toefl_speaking_sets.xlsx` (4시트: items/stimuli/answer_keys/rubric_features)
- `independent_topics.xlsx`  (2시트: items/blueprints - NEW)

---

## 11) 실행 메모
- 내부 자료는 분석/학습/개발용으로만 사용한다.
- 외부 공개 MVP에서는 blueprint/feature를 기반으로 **완전 신규 생성 문항**으로 대체한다.
- 앱 개발은 `items/stimuli/answer_keys`만 로드하면 읽기→듣기→말하기 플로우 및 타이머 구현이 즉시 가능하다.
- **NEW**: 발음/억양 채점은 외부 ASR 엔진(예: Azure Speech, Google Cloud Speech-to-Text) 연동 필요
- **NEW**: SpeechRater의 가중치는 참조용이며, 실제 앱에서는 자체 학습 데이터로 재조정 권장

---

## 12) 유저 피드백 스키마 (User Feedback Schema) - NEW

### 12.1 개요
앱 유저(학습자)가 음성 응답 제출 후 받게 되는 피드백의 표준 데이터 구조를 정의한다.

```
[유저 플로우]
문제 확인 → 준비(15~30초) → 녹음(45~60초) → 제출 → 피드백 수신
```

### 12.2 UserFeedback 스키마 (JSON)

#### 공통 필드 + Task Type별 차이

```json
{
  "feedback_id": "string",           // 고유 피드백 ID
  "item_id": "string",               // 문항 ID (FK)
  "user_id": "string",               // 유저 ID
  "submitted_at": "ISO datetime",    // 제출 시간
  "audio_duration_sec": 58.3,        // 실제 녹음 길이
  "task_type": "independent|integrated_read_listen|integrated_listen_only",  // NEW
  
  "transcript": {
    "text": "The professor explains that the concept of...",
    "confidence": 0.92,              // ASR 신뢰도 (0~1)
    "word_count": 142,
    "timestamps": [                  // 단어별 타임스탬프 (선택)
      {"word": "The", "start": 0.0, "end": 0.15},
      {"word": "professor", "start": 0.16, "end": 0.58}
    ]
  },
  
  "scores": {
    "overall": 23,                   // 총점 (0~30 스케일)
    "band": "mid",                   // low(0-19) | mid(20-24) | high(25-30)
    "percentile": 65,                // 백분위 (선택)
    
    "dimensions": {
      "delivery": {
        "score": 7.5,                // 10점 만점
        "weight": 0.40,              // 총점 반영 비중
        "sub_scores": {
          "fluency": 7.0,
          "pronunciation": 8.0,      // requires_audio=true인 경우만
          "prosody": 7.5             // requires_audio=true인 경우만
        }
      },
      "language_use": {
        "score": 7.0,
        "weight": 0.30,
        "sub_scores": {
          "vocabulary": 7.5,
          "grammar": 6.5
        }
      },
      "topic_development": {
        "score": 8.0,
        "weight": 0.30,
        "sub_scores": {
          "content_coverage": 8.5,   // Integrated: 정보 커버리지 / Independent: 구조 완성도
          "coherence": 7.5
        }
      }
    }
  },
  
  "feature_analysis": {
    "delivery": {
      "wpm": 128,
      "wpm_rating": "good",          // slow | good | fast
      "pause_count": 6,
      "avg_pause_duration_sec": 1.8,
      "pause_rating": "needs_work",  // good | acceptable | needs_work
      "filler_count": 3,
      "filler_words": ["um", "uh", "like"],
      "repetition_count": 1,
      "restart_count": 2
    },
    "language_use": {
      "type_token_ratio": 0.52,
      "unique_words": 74,
      "advanced_vocab_count": 8,
      "advanced_vocab_examples": ["concept", "phenomenon", "significant"],
      "avg_sentence_length": 12.3,
      "complex_sentence_ratio": 0.35
    },
    "topic_development": {
      "coverage_ratio": 0.75,        // Integrated에서만 사용
      "structure_score": 0.85,       // Independent에서만 사용 (NEW)
      "covered_units": ["U1", "U2", "U3"],      // Integrated
      "completed_components": ["C1", "C2", "C3"], // Independent (NEW)
      "missing_units": ["U4"],
      "missing_components": ["C4", "C5"],        // Independent (NEW)
      "discourse_markers_used": ["first", "however", "in addition"],
      "discourse_marker_count": 4,
      "organization_score": 0.8      // 0~1, 구조 일치도
    }
  },
```

#### Independent Speaking 전용: Structure Comparison (blueprint_comparison 대체)

```json
  "structure_comparison": {          // Independent Speaking 전용 (NEW)
    "topic_type": "preference",
    "expected_pattern": "position_reason_example",
    "detected_pattern": "position_reason",  // 실제 감지된 패턴
    "pattern_match_score": 0.7,
    
    "component_details": [
      {
        "component_id": "C1",
        "role": "position",
        "status": "completed",       // completed | partial | missing
        "user_content": "I prefer studying alone rather than in groups.",
        "quality_note": "Clear and direct position statement"
      },
      {
        "component_id": "C2",
        "role": "reason_1",
        "status": "completed",
        "user_content": "I can focus better when I study alone.",
        "quality_note": "Valid reason provided"
      },
      {
        "component_id": "C3",
        "role": "example_1",
        "status": "partial",
        "user_content": "Like when I study math...",
        "quality_note": "Example started but lacks specific detail"
      },
      {
        "component_id": "C4",
        "role": "reason_2",
        "status": "missing",
        "user_content": null,
        "quality_note": "Second reason would strengthen the response"
      }
    ],
    
    "linking_analysis": {
      "expected_markers": ["First", "For example", "Additionally", "That's why"],
      "used_markers": ["First", "Like"],
      "missing_transitions": ["transition to second reason", "conclusion marker"],
      "linking_score": 0.5
    }
  },
```

#### Integrated Speaking 전용: Blueprint Comparison (기존 유지)

```json
  "blueprint_comparison": {          // Integrated Speaking 전용
    "total_units": 4,
    "covered_count": 3,
    "coverage_percentage": 75,
    "unit_details": [
      {
        "unit_id": "U1",
        "role": "main_point",
        "status": "covered",         // covered | partial | missing
        "user_mention": "The professor talks about how animals adapt...",
        "expected_summary": "Main concept: animal adaptation to environment"
      },
      {
        "unit_id": "U2",
        "role": "example",
        "status": "covered",
        "user_mention": "For example, the arctic fox changes its fur color...",
        "expected_summary": "Example 1: Arctic fox fur color change"
      },
      {
        "unit_id": "U3",
        "role": "detail",
        "status": "partial",
        "user_mention": "This helps them survive...",
        "expected_summary": "Detail: Survival advantage explanation",
        "missing_elements": ["specific survival statistics mentioned in lecture"]
      },
      {
        "unit_id": "U4",
        "role": "example",
        "status": "missing",
        "user_mention": null,
        "expected_summary": "Example 2: Desert plants water storage"
      }
    ],
    "order_analysis": {
      "expected_order": ["U1", "U2", "U3", "U4"],
      "user_order": ["U1", "U3", "U2"],
      "order_similarity": 0.6,
      "recommendation": "Consider presenting examples immediately after introducing the main point"
    }
  },
  
  "feedback": {
    "summary": "Good attempt with clear main idea coverage. Work on including all examples and reducing pauses.",
    
    "strengths": [
      {
        "category": "topic_development",
        "aspect": "main_point_coverage",
        "message": "You clearly identified and explained the main concept from the lecture.",
        "evidence": "\"The professor talks about how animals adapt...\""
      },
      {
        "category": "language_use",
        "aspect": "vocabulary",
        "message": "Good use of academic vocabulary like 'phenomenon' and 'significant'.",
        "evidence": null
      },
      {
        "category": "delivery",
        "aspect": "speaking_rate",
        "message": "Your speaking pace (128 wpm) is within the optimal range.",
        "evidence": null
      }
    ],
    
    "improvements": [
      {
        "category": "delivery",
        "aspect": "pause_frequency",
        "severity": "high",          // high | medium | low
        "message": "You had 6 pauses averaging 1.8 seconds each. Try to reduce pauses to under 1 second.",
        "tip": "Practice with a timer and try to maintain continuous speech. Use filler phrases like 'what I mean is...' instead of silent pauses.",
        "target_metric": "avg_pause_duration < 1.0 sec"
      },
      {
        "category": "topic_development",
        "aspect": "content_coverage",
        "severity": "medium",
        "message": "You missed the second example about desert plants from the lecture.",
        "tip": "When listening, note down 2-3 key examples. Make sure to mention all of them in your response.",
        "target_metric": "coverage_ratio >= 0.85"
      },
      {
        "category": "topic_development",
        "aspect": "organization",
        "severity": "low",
        "message": "Your response order differed from the optimal structure.",
        "tip": "Try following the lecture's organization: main idea → example 1 → example 2 → conclusion.",
        "target_metric": "order_similarity >= 0.8"
      }
    ],
    
    "next_steps": [
      "Practice 3 more responses focusing on reducing pause length",
      "Review lecture note-taking strategies for capturing all examples",
      "Try the 'shadow speaking' exercise to improve fluency"
    ],
    
    "estimated_improvement": {
      "if_addressed": ["pause_frequency", "content_coverage"],
      "potential_score": 25,
      "potential_band": "high"
    }
  },
  
  "comparison_to_sample": {
    "high_score_sample": {
      "level": "26",
      "transcript_preview": "The professor discusses the concept of animal adaptation...",
      "key_differences": [
        "Sample includes both examples from the lecture",
        "Sample has smoother transitions between points",
        "Sample concludes with a summary statement"
      ]
    }
  },
  
  "history_context": {                // 유저의 과거 기록 대비 (선택)
    "attempts_on_this_item": 2,
    "previous_score": 21,
    "score_change": "+2",
    "improved_areas": ["vocabulary", "speaking_rate"],
    "persistent_issues": ["pause_frequency"]
  }
}
```

### 12.3 피드백 레벨별 상세도

앱에서는 유저 설정 또는 구독 티어에 따라 피드백 상세도를 조절할 수 있다:

| 레벨 | 포함 내용 | 용도 |
|------|----------|------|
| **Basic** | overall score, band, summary, top 2 strengths/improvements | 무료 티어 |
| **Standard** | + dimension scores, feature_analysis 요약, blueprint coverage % | 기본 구독 |
| **Premium** | + 전체 feature_analysis, unit_details, comparison_to_sample, history_context | 프리미엄 구독 |

### 12.4 피드백 메시지 템플릿

#### A. 점수대별 Summary 템플릿

```yaml
summary_templates:
  high (25-30):
    - "Excellent response! You demonstrated strong command of the content with fluent delivery."
    - "Great job covering all key points with clear organization and natural speech flow."
  
  mid (20-24):
    - "Good attempt with solid content coverage. Focus on {top_improvement_area} to reach the next level."
    - "You captured the main ideas well. Work on {top_improvement_area} for a higher score."
  
  low (0-19):
    - "You're on the right track. Let's focus on {top_improvement_area} and {second_improvement_area}."
    - "Keep practicing! Prioritize {top_improvement_area} to see quick improvements."
```

#### B. Feature별 피드백 메시지 뱅크

```yaml
feedback_messages:
  delivery:
    wpm:
      slow (<100):
        message: "Your speaking pace is a bit slow at {value} words per minute."
        tip: "Try to speak slightly faster while maintaining clarity. Aim for 120-150 wpm."
      good (100-150):
        message: "Your speaking pace ({value} wpm) is within the optimal range."
        tip: null
      fast (>150):
        message: "You're speaking quite fast at {value} wpm, which may affect clarity."
        tip: "Slow down slightly to ensure all words are clearly pronounced."
    
    pause_frequency:
      good (<4 pauses):
        message: "Good fluency with minimal pauses."
        tip: null
      acceptable (4-7 pauses):
        message: "You had {value} noticeable pauses in your response."
        tip: "Try to reduce pauses by practicing with familiar topics first."
      needs_work (>7 pauses):
        message: "Frequent pauses ({value}) are affecting your fluency score."
        tip: "Practice 'stream of consciousness' speaking exercises to build fluency."
    
    filler_words:
      good (0-2):
        message: "Minimal use of filler words - great job!"
        tip: null
      acceptable (3-5):
        message: "You used {value} filler words (um, uh, like)."
        tip: "Try replacing fillers with short pauses or transitional phrases."
      needs_work (>5):
        message: "High frequency of filler words ({value}) detected."
        tip: "Record yourself and count fillers. Awareness is the first step to reducing them."
  
  topic_development:
    coverage:
      excellent (>85%):
        message: "Excellent coverage of the key information ({value}% of key points)."
        tip: null
      good (70-85%):
        message: "You covered {value}% of the key points."
        tip: "Review what you missed: {missing_units_summary}"
      needs_work (<70%):
        message: "You covered only {value}% of the expected content."
        tip: "Focus on note-taking during the listening section to capture all main points."
    
    organization:
      good (>0.7):
        message: "Your response was well-organized and easy to follow."
        tip: null
      needs_work (<=0.7):
        message: "The organization of your response could be improved."
        tip: "Use a clear structure: introduction → main points with examples → brief conclusion."
  
  language_use:
    vocabulary:
      advanced:
        message: "Strong vocabulary usage with {advanced_count} advanced/academic words."
        tip: null
      basic:
        message: "Try incorporating more varied and academic vocabulary."
        tip: "Learn 5 new academic words per week and practice using them in responses."
    
    grammar:
      complex:
        message: "Good use of complex sentence structures."
        tip: null
      simple:
        message: "Your responses mainly use simple sentence structures."
        tip: "Practice using subordinate clauses (because, although, which) to add complexity."
```

### 12.5 Claude Agent 프롬프트: 피드백 생성기

```text
You are a TOEFL Speaking feedback generation agent.
Given a user's transcript, extracted features, and the item's blueprint, generate personalized feedback.

INPUTS:
- Item ID: {item_id}
- Task type: {task_type}
- Blueprint: {blueprint_json}
- User transcript: """{transcript}"""
- Extracted features: {features_json}
- User history (optional): {history_json}

INSTRUCTIONS:
1) Calculate dimension scores based on features and SpeechRater weights.
2) Compare transcript to blueprint for content coverage analysis.
3) Identify top 3 strengths and top 3 areas for improvement.
4) Generate actionable, encouraging feedback messages.
5) Prioritize improvements by potential score impact.

OUTPUT JSON matching the UserFeedback schema:
{
  "scores": {...},
  "feature_analysis": {...},
  "blueprint_comparison": {...},
  "feedback": {
    "summary": "...",
    "strengths": [...],
    "improvements": [...],
    "next_steps": [...]
  }
}

TONE GUIDELINES:
- Be encouraging but honest
- Use "you" language, not "the speaker"
- Provide specific, actionable tips
- Reference actual examples from the user's response when possible
- Avoid jargon - explain technical terms simply
```

### 12.6 UI 컴포넌트 매핑

피드백 JSON의 각 섹션이 앱 UI에서 어떻게 표시되는지:

```
┌─────────────────────────────────────────────────────────┐
│  📊 Your Score: 23/30                    [Band: Mid]    │  ← scores.overall, scores.band
├─────────────────────────────────────────────────────────┤
│  Delivery        ████████░░  7.5/10                     │
│  Language Use    ███████░░░  7.0/10                     │  ← scores.dimensions
│  Topic Dev.      ████████░░  8.0/10                     │
├─────────────────────────────────────────────────────────┤
│  📝 Summary                                             │
│  "Good attempt with solid content coverage..."          │  ← feedback.summary
├─────────────────────────────────────────────────────────┤
│  ✅ Strengths                                           │
│  • Clear main idea coverage                             │  ← feedback.strengths
│  • Good academic vocabulary                             │
├─────────────────────────────────────────────────────────┤
│  🎯 Areas to Improve                                    │
│  • [HIGH] Reduce pause frequency                        │  ← feedback.improvements
│  • [MED] Include all examples from lecture              │
├─────────────────────────────────────────────────────────┤
│  📋 Content Coverage: 75%                               │
│  ✓ U1: Main concept    ✓ U2: Example 1                 │  ← blueprint_comparison
│  △ U3: Details         ✗ U4: Example 2                 │
├─────────────────────────────────────────────────────────┤
│  🎧 Your Transcript                      [Show/Hide]    │  ← transcript.text
│  "The professor explains that the concept of..."        │
├─────────────────────────────────────────────────────────┤
│  📈 Next Steps                                          │
│  1. Practice reducing pause length                      │  ← feedback.next_steps
│  2. Review note-taking strategies                       │
│                                                         │
│  [Try Again]  [Next Question]  [View Sample Answer]     │
└─────────────────────────────────────────────────────────┘
```

---

## 13) 참고 자료

### ETS SpeechRater 관련 문헌
1. Chen et al. (2018). "Automated Scoring of Nonnative Speech Using the SpeechRater v. 5.0 Engine" - ETS Research Report
2. Zechner et al. (2007). "Automated Scoring of Non-Native Speech" - SLATE 2007
3. Xie, Evanini & Zechner (2012). Content Vector Analysis for TOEFL Speaking

### Feature 상관관계 요약
- 가장 높은 영향: `silmean`(0.119), `cvamax`(0.099), `wpsec`(0.097)
- 중간 영향: `L1`(0.081), `secpchk`(0.066), `poscvamax`(0.062), `types`(0.061)
- 낮은 영향: `dep_clauses_per_clause`(0.001), `withinClauseSilMean`(0.008)

### 주요 인사이트
1. **Fluency가 가장 중요**: 전체 가중치의 ~38%를 차지
2. **어휘가 문법보다 중요**: Vocabulary(~20%) vs Grammar(~6%)
3. **발음은 원어민 유사도가 핵심**: L1 feature가 amscore보다 2배 이상 영향
4. **Content는 아직 약점**: ASR 정확도 한계로 완전 통합 미완료
