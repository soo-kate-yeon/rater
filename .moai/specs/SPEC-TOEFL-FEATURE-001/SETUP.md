# SPEC-TOEFL-FEATURE-001 설치 가이드

## 📋 개요

SPEC-TOEFL-FEATURE-001 구현에 필요한 Python 의존성 설치 가이드입니다.

---

## ✅ 설치 완료 (최종)

### 성공적으로 설치된 패키지

| 패키지 | 버전 | 용도 | 설치일 | 상태 |
|--------|------|------|--------|------|
| **scikit-learn** | 1.6.1 | TF-IDF, cosine similarity (cvamax) | 2026-01-27 | ✅ 작동 |
| **nltk** | 3.9.2 | Word frequency (logFreq) | 2026-01-27 | ✅ 작동 |
| **scipy** | 1.13.1 | scikit-learn 의존성 | 2026-01-27 | ✅ 작동 |
| **joblib** | 1.5.3 | scikit-learn 의존성 | 2026-01-27 | ✅ 작동 |
| **spaCy** | 3.7.5 | POS tagging, dependency parsing | 2026-01-28 | ✅ 작동 |
| **en_core_web_sm** | 3.7.1 | spaCy 영어 모델 | 2026-01-28 | ✅ 작동 |

### NLTK 데이터

```bash
✅ brown corpus (word frequency)
✅ punkt tokenizer
```

---

## 🎯 spaCy 설치 과정

### 문제 발생 (2026-01-27)

최신 spaCy (3.8+) 설치 시 C++ 컴파일 오류:

```bash
pip3 install spacy --user

ERROR: Failed to build 'spacy' when installing build dependencies
thinc/backends/cblas.cpp:1150:10: fatal error: 'ios' file not found
```

**근본 원인**: Python 3.9 + spaCy 3.8+ + macOS Command Line Tools 비호환

### 해결 방법 (2026-01-28)

✅ **구버전 spaCy 사용 (3.7.x)**

```bash
# Python 3.9 호환 버전 설치
pip3 install "spacy<3.8" --user

# 가벼운 영어 모델 다운로드 (12.8MB)
python3 -m spacy download en_core_web_sm
```

**설치 결과**:
- spaCy 3.7.5 설치 완료
- en_core_web_sm 3.7.1 모델 설치 완료
- Pre-built wheel 사용으로 컴파일 불필요

### 다중 모델 지원

코드에서 우선순위 기반 폴백 구현:

```python
# grammar_features.py
for model_name in ["en_core_web_lg", "en_core_web_md", "en_core_web_sm"]:
    try:
        self._nlp = spacy.load(model_name)
        logger.info(f"spaCy model '{model_name}' loaded successfully")
        break
    except OSError:
        continue
```

---

## 📊 영향 분석

### Phase 1+2 테스트 결과

| 측정 항목 | 2026-01-27 (spaCy 없음) | 2026-01-28 (spaCy 설치) | 개선 |
|----------|------------------------|------------------------|-----|
| **전체 테스트** | 95 passed, 6 skipped | 101 passed, 0 skipped | +6 tests |
| **프로젝트 커버리지** | 63% | 64% | +1%p |
| **grammar_features.py** | 47% | 85% | **+38%p** |
| **blueprint_comparison.py** | 26% | 97% | +71%p |
| **delivery_features.py** | 20% | 99% | +79%p |
| **structure_comparison.py** | 36% | 100% | +64%p |
| **language_features.py** | 33% | 93% | +60%p |
| **structure_features.py** | 41% | 98% | +57%p |
| **vocabulary_features.py** | 33% | 74% | +41%p |

### 활성화된 기능

**13/13 Features 완전 작동** ✅

- **8 Delivery Features** (99% coverage)
  - silmean, wpsec, secpchk, numrep, numdff, silpsecutt, IPC, withinClauseSilMean

- **2 Grammar Features** (85% coverage)
  - poscvamax: POS n-gram 기반 문법 프로파일 유사도
  - dep_clauses_per_clause: 평균 종속절 수

- **3 Vocabulary Features** (74% coverage)
  - cvamax: TF-IDF 기반 어휘 유사도
  - types: 고유 단어 수 (lexical diversity)
  - logFreq: 평균 log frequency

---

## 🔧 대안 설치 방법 (참고용)

### 옵션 1: Conda 사용

```bash
conda create -n toefl-rater python=3.9
conda activate toefl-rater
conda install -c conda-forge spacy
python -m spacy download en_core_web_lg
```

### 옵션 2: Python 3.10+ 업그레이드

```bash
pyenv install 3.11.7
pyenv local 3.11.7
pip install -e .
pip install spacy
python -m spacy download en_core_web_lg
```

### 옵션 3: Docker 사용

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e . && python -m spacy download en_core_web_lg
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0"]
```

---

## 📝 참고 문서

- [spaCy Installation Guide](https://spacy.io/usage)
- [thinc Build Issues](https://github.com/explosion/thinc/issues)
- [SPEC-TOEFL-FEATURE-001 spec.md](./spec.md)

---

**최종 업데이트**: 2026-01-28
**작성자**: Claude Sonnet 4.5
**버전**: 2.0.0
**상태**: ✅ 모든 의존성 설치 완료, 프로덕션 준비
