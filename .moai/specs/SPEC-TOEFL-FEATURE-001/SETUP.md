# SPEC-TOEFL-FEATURE-001 설치 가이드

## 📋 개요

SPEC-TOEFL-FEATURE-001 구현에 필요한 Python 의존성 설치 가이드입니다.

---

## ✅ 설치 완료 (2026-01-27)

### 성공적으로 설치된 패키지

| 패키지 | 버전 | 용도 | 상태 |
|--------|------|------|------|
| **scikit-learn** | 1.6.1 | TF-IDF, cosine similarity (cvamax) | ✅ 설치 완료 |
| **nltk** | 3.9.2 | Word frequency (logFreq) | ✅ 설치 완료 |
| **scipy** | 1.13.1 | scikit-learn 의존성 | ✅ 설치 완료 |
| **joblib** | 1.5.3 | scikit-learn 의존성 | ✅ 설치 완료 |

### NLTK 데이터 다운로드 완료

```bash
✅ brown corpus (word frequency)
✅ punkt tokenizer
```

---

## ⚠️ 미해결: spaCy 설치 실패

### 문제 상황

**일시**: 2026-01-27
**환경**: macOS, Python 3.9.6
**시도한 명령어**:
```bash
pip3 install spacy --user
```

### 오류 내용

```
ERROR: Failed to build 'spacy' when installing build dependencies for spacy

Building wheel for thinc (pyproject.toml) ... error
  error: command '/usr/bin/clang++' failed with exit code 1

thinc/backends/cblas.cpp:1150:10: fatal error: 'ios' file not found
 1150 | #include "ios"
      |          ^~~~~
```

**근본 원인**:
- `thinc` 패키지 (spaCy 의존성) C++ 컴파일 실패
- Python 3.9 + spaCy 3.8+ 호환성 문제
- macOS Command Line Tools C++ 헤더 이슈

### 영향 범위

**작동하는 기능 (spaCy 없이도 정상):**
- ✅ Vocabulary Features (cvamax, types, logFreq) - 74% 커버리지
- ✅ Delivery Features (전체 8개) - 99% 커버리지
- ✅ Blueprint/Structure Comparison (stub)

**제한되는 기능 (spaCy 필요):**
- ⚠️ Grammar Features (poscvamax, dep_clauses_per_clause)
  - Graceful degradation으로 `None` 반환
  - 테스트 6개 skipped
  - 47% 커버리지 (전체 로직의 절반 미실행)

---

## 🔧 해결 방법 (향후)

### 옵션 1: Conda 사용 (권장)

Pre-built 바이너리를 사용하여 컴파일 없이 설치:

```bash
# Conda 환경 생성 (선택)
conda create -n toefl-rater python=3.9
conda activate toefl-rater

# spaCy 설치 (컴파일 없음)
conda install -c conda-forge spacy

# spaCy 모델 다운로드
python -m spacy download en_core_web_lg
```

**장점:**
- ✅ 컴파일 불필요
- ✅ 의존성 자동 해결
- ✅ 안정적

**단점:**
- ⚠️ Conda 설치 필요
- ⚠️ 환경 분리 필요

---

### 옵션 2: 구버전 spaCy 사용

Python 3.9에서 안정적인 구버전 설치:

```bash
# spaCy 3.7.x 설치 (thinc 빌드 이슈 없음)
pip3 install "spacy<3.8" --user

# 가벼운 모델 다운로드 (200MB vs 500MB)
python -m spacy download en_core_web_sm

# 또는 중간 모델
python -m spacy download en_core_web_md
```

**장점:**
- ✅ pip로 간단히 설치
- ✅ Python 3.9 호환 확인됨

**단점:**
- ⚠️ 최신 버전 아님 (성능 차이 미미)
- ⚠️ 작은 모델은 정확도 약간 낮음

---

### 옵션 3: Python 3.10+ 업그레이드

Python 버전을 올려서 최신 spaCy 사용:

```bash
# pyenv로 Python 3.11 설치 (권장)
pyenv install 3.11.7
pyenv local 3.11.7

# 의존성 재설치
pip install -e .

# spaCy 설치
pip install spacy
python -m spacy download en_core_web_lg
```

**장점:**
- ✅ 최신 spaCy 3.8+ 사용 가능
- ✅ 향후 호환성 좋음
- ✅ 성능 개선

**단점:**
- ⚠️ 프로젝트 Python 버전 변경 필요
- ⚠️ 전체 의존성 재설치 필요

---

### 옵션 4: Docker 사용

Docker 컨테이너에서 실행:

```bash
# Dockerfile 예시
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e . && \
    python -m spacy download en_core_web_lg

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0"]
```

**장점:**
- ✅ 환경 독립적
- ✅ 프로덕션 배포에 적합
- ✅ 재현 가능

**단점:**
- ⚠️ 로컬 개발 복잡도 증가
- ⚠️ Docker 설치 필요

---

## 📊 현재 상태 요약

### 테스트 결과 (2026-01-27)

```
✅ 40개 테스트 통과
⏭️ 6개 테스트 skipped (spaCy 필요)
⏱️ 28.52초 실행 시간
```

### 커버리지

| 파일 | 커버리지 | 비고 |
|------|---------|------|
| vocabulary_features.py | 74% | ✅ 양호 (scikit-learn 작동) |
| delivery_features.py | 99% | ✅ 완벽 |
| grammar_features.py | 47% | ⚠️ spaCy 필요 |

**전체 프로젝트 커버리지**: 55%

---

## 🎯 권장 조치

### 즉시 조치 (선택)

```bash
# 옵션 2 사용: 구버전 spaCy 설치
pip3 install "spacy<3.8" --user
python3 -m spacy download en_core_web_sm

# 테스트 재실행
python3 -m pytest tests/services/test_grammar_features.py -v
```

### 프로덕션 배포 시

- **권장**: Docker + Python 3.11 + spaCy 3.8+
- 이유: 안정성, 재현성, 최신 기능

---

## 📝 참고 문서

- [spaCy Installation Guide](https://spacy.io/usage)
- [thinc Build Issues](https://github.com/explosion/thinc/issues)
- [SPEC-TOEFL-FEATURE-001 spec.md](./spec.md)

---

**작성일**: 2026-01-27
**작성자**: Claude Sonnet 4.5
**버전**: 1.0.0
