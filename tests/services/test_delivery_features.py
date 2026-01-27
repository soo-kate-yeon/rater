"""Delivery Features 추출 서비스 characterization tests

이 테스트는 기존 delivery_features.py의 동작을 문서화하고 보존합니다.
"""

from typing import Any

import pytest

from src.schemas.scoring import ASRResult, DeliverySignals
from src.services.delivery_features import DeliveryFeatureExtractor, get_delivery_feature_extractor


@pytest.fixture
def extractor() -> DeliveryFeatureExtractor:
    """Delivery feature extractor 인스턴스"""
    return DeliveryFeatureExtractor()


@pytest.fixture
def simple_asr_result() -> ASRResult:
    """단순한 ASR 결과 (테스트용)"""
    return ASRResult(
        transcript="I think education is very important for everyone.",
        segments=[
            {
                "id": 0,
                "start": 0.0,
                "end": 5.0,
                "text": " I think education is very important for everyone.",
                "tokens": [1, 519, 519, 3775, 307, 588, 1021, 337, 1518, 13],
                "temperature": 0.0,
                "avg_logprob": -0.25,
                "compression_ratio": 1.2,
                "no_speech_prob": 0.01,
            }
        ],
        language="en",
        avg_logprob=-0.25,
        no_speech_prob=0.01,
        duration_sec=5.0,
    )


@pytest.fixture
def complex_asr_result() -> ASRResult:
    """복잡한 ASR 결과 (여러 세그먼트, pause 포함)"""
    return ASRResult(
        transcript="I think education is very important. Um, it helps people develop skills.",
        segments=[
            {
                "id": 0,
                "start": 0.0,
                "end": 3.5,
                "text": " I think education is very important.",
                "tokens": [1, 519, 519, 3775, 307, 588, 1021, 13],
                "temperature": 0.0,
                "avg_logprob": -0.22,
                "compression_ratio": 1.3,
                "no_speech_prob": 0.02,
            },
            # 0.6초 pause (> 500ms)
            {
                "id": 1,
                "start": 4.1,
                "end": 8.0,
                "text": " Um, it helps people develop skills.",
                "tokens": [4599, 11, 309, 3665, 561, 1499, 3942, 13],
                "temperature": 0.0,
                "avg_logprob": -0.28,
                "compression_ratio": 1.1,
                "no_speech_prob": 0.03,
            },
        ],
        language="en",
        avg_logprob=-0.25,
        no_speech_prob=0.025,
        duration_sec=8.0,
    )


class TestDeliveryFeatureExtractorBasicBehavior:
    """기본 동작 characterization"""

    def test_characterize_simple_extraction(
        self, extractor: DeliveryFeatureExtractor, simple_asr_result: ASRResult
    ):
        """CHARACTERIZE: 단순 ASR 결과에서 기본 features 추출"""
        result = extractor.extract(simple_asr_result)

        # 현재 동작 문서화
        assert isinstance(result, DeliverySignals)
        assert result.duration_sec == 5.0
        assert result.wpm > 0  # 분당 단어 수 계산됨
        assert 0.0 <= result.silence_ratio <= 1.0
        assert result.pause_count >= 0
        assert result.pause_p95_ms >= 0
        assert result.filler_count >= 0
        assert -1.0 <= result.asr_clarity_signal <= 0.0
        assert len(result.interpretation) > 0
        # SPEC-TOEFL-FEATURE-001: 추가 features
        assert result.secpchk >= 0.0
        assert result.silpsecutt >= 0.0
        assert result.within_clause_interruptions >= 0
        assert result.within_clause_silence_mean_ms >= 0.0

    def test_characterize_word_counting(self, extractor: DeliveryFeatureExtractor):
        """CHARACTERIZE: 단어 카운팅 방식"""
        # 알파벳 단어만 카운트 (구두점 제외)
        assert extractor._count_words("Hello, world!") == 2
        assert extractor._count_words("I think it's good.") == 5  # it's는 "it"과 "s"로 분리됨
        assert extractor._count_words("123 test 456") == 1  # 숫자 제외
        assert extractor._count_words("") == 0

    def test_characterize_pause_extraction(
        self, extractor: DeliveryFeatureExtractor, complex_asr_result: ASRResult
    ):
        """CHARACTERIZE: Pause 추출 (>500ms만 포함)"""
        pauses = extractor._extract_pauses(complex_asr_result.segments)

        # 0.6초 pause가 감지됨
        assert len(pauses) == 1
        assert pauses[0] > 500  # 밀리초

    def test_characterize_filler_detection(self, extractor: DeliveryFeatureExtractor):
        """CHARACTERIZE: Filler 단어 감지"""
        # 현재 filler 목록: uh, um, like, you know, well, so, actually, basically
        assert extractor._count_fillers("Um, I think") == 1
        assert extractor._count_fillers("Well, you know, I actually like it") == 4
        assert extractor._count_fillers("I think it is good") == 0

    def test_characterize_silence_ratio(self, extractor: DeliveryFeatureExtractor):
        """CHARACTERIZE: Silence ratio 계산"""
        pauses_ms = [600.0, 800.0, 1000.0]  # 총 2.4초
        duration_sec = 10.0
        ratio = extractor._calculate_silence_ratio(pauses_ms, duration_sec)

        assert ratio == pytest.approx(0.24, abs=0.01)

    def test_characterize_interpretation_rules(self, extractor: DeliveryFeatureExtractor):
        """CHARACTERIZE: Interpretation 생성 규칙"""
        # 느린 속도
        interp = extractor._generate_interpretation(wpm=80, silence_ratio=0.15, asr_clarity_signal=-0.3)
        assert "느림" in interp

        # 과속
        interp = extractor._generate_interpretation(
            wpm=200, silence_ratio=0.15, asr_clarity_signal=-0.3
        )
        assert "과속" in interp

        # 침묵 많음
        interp = extractor._generate_interpretation(
            wpm=130, silence_ratio=0.25, asr_clarity_signal=-0.3
        )
        assert "침묵 많음" in interp

        # 발음 개선 필요
        interp = extractor._generate_interpretation(
            wpm=130, silence_ratio=0.15, asr_clarity_signal=-0.6
        )
        assert "발음 개선 필요" in interp


class TestDeliveryFeatureExtractorEdgeCases:
    """Edge cases characterization"""

    def test_characterize_empty_segments(self, extractor: DeliveryFeatureExtractor):
        """CHARACTERIZE: 세그먼트가 없을 때 예외 발생"""
        asr_result = ASRResult(
            transcript="",
            segments=[],
            language="en",
            avg_logprob=0.0,
            no_speech_prob=0.0,
            duration_sec=0.0,
        )

        with pytest.raises(ValueError, match="세그먼트가 없습니다"):
            extractor.extract(asr_result)

    def test_characterize_zero_duration(self, extractor: DeliveryFeatureExtractor):
        """CHARACTERIZE: Duration이 0일 때 WPM 계산"""
        asr_result = ASRResult(
            transcript="Test",
            segments=[
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 0.0,
                    "text": "Test",
                    "tokens": [1],
                    "temperature": 0.0,
                    "avg_logprob": -0.3,
                    "compression_ratio": 1.0,
                    "no_speech_prob": 0.1,
                }
            ],
            language="en",
            avg_logprob=-0.3,
            no_speech_prob=0.1,
            duration_sec=0.0,
        )

        result = extractor.extract(asr_result)
        assert result.wpm == 0.0  # Division by zero 방지

    def test_characterize_no_pauses(self, extractor: DeliveryFeatureExtractor):
        """CHARACTERIZE: Pause가 없을 때 (연속 발화)"""
        asr_result = ASRResult(
            transcript="Continuous speech without pauses.",
            segments=[
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 3.0,
                    "text": " Continuous speech without pauses.",
                    "tokens": [1, 2, 3, 4, 5],
                    "temperature": 0.0,
                    "avg_logprob": -0.2,
                    "compression_ratio": 1.2,
                    "no_speech_prob": 0.01,
                }
            ],
            language="en",
            avg_logprob=-0.2,
            no_speech_prob=0.01,
            duration_sec=3.0,
        )

        result = extractor.extract(asr_result)
        assert result.pause_count == 0
        assert result.pause_p95_ms == 0.0
        assert result.silence_ratio == 0.0


class TestDeliveryFeatureExtractorSingleton:
    """싱글톤 패턴 characterization"""

    def test_characterize_singleton_pattern(self):
        """CHARACTERIZE: get_delivery_feature_extractor는 동일 인스턴스 반환"""
        instance1 = get_delivery_feature_extractor()
        instance2 = get_delivery_feature_extractor()

        assert instance1 is instance2


class TestDeliveryFeatureExtractorRealWorldScenario:
    """실제 사용 시나리오 characterization"""

    def test_characterize_typical_toefl_response(
        self, extractor: DeliveryFeatureExtractor, mock_asr_result_model: ASRResult
    ):
        """CHARACTERIZE: 일반적인 TOEFL 응답 처리 (conftest fixture 사용)"""
        result = extractor.extract(mock_asr_result_model)

        # 기대 동작 문서화
        assert result.duration_sec == 12.0
        assert result.wpm > 0  # 단어가 있으므로 WPM 계산됨
        assert result.filler_count == 0  # 이 샘플에는 filler 없음
        assert result.pause_count == 0  # 세그먼트 간 gap이 500ms 이하
        assert "명료도 양호" in result.interpretation  # avg_logprob이 -0.235로 양호


class TestDeliveryFeatureExtractorSPECFeatures:
    """SPEC-TOEFL-FEATURE-001 추가 features 테스트"""

    def test_secpchk_calculation(self, extractor: DeliveryFeatureExtractor):
        """secpchk: 평균 chunk 길이 계산"""
        asr_result = ASRResult(
            transcript="Test",
            segments=[
                {"id": 0, "start": 0.0, "end": 2.0, "text": "First", "tokens": [1], "temperature": 0.0, "avg_logprob": -0.2, "compression_ratio": 1.0, "no_speech_prob": 0.01},
                {"id": 1, "start": 2.0, "end": 5.0, "text": "Second", "tokens": [2], "temperature": 0.0, "avg_logprob": -0.2, "compression_ratio": 1.0, "no_speech_prob": 0.01},
            ],
            language="en",
            avg_logprob=-0.2,
            no_speech_prob=0.01,
            duration_sec=5.0,
        )

        result = extractor.extract(asr_result)
        # (2.0 + 3.0) / 2 = 2.5초
        assert result.secpchk == 2.5

    def test_silpsecutt_calculation(self, extractor: DeliveryFeatureExtractor):
        """silpsecutt: 초당 pause 빈도"""
        asr_result = ASRResult(
            transcript="Test",
            segments=[
                {"id": 0, "start": 0.0, "end": 2.0, "text": "A", "tokens": [1], "temperature": 0.0, "avg_logprob": -0.2, "compression_ratio": 1.0, "no_speech_prob": 0.01},
                # 0.6초 pause (>500ms) → pause_count=1
                {"id": 1, "start": 2.6, "end": 5.0, "text": "B", "tokens": [2], "temperature": 0.0, "avg_logprob": -0.2, "compression_ratio": 1.0, "no_speech_prob": 0.01},
            ],
            language="en",
            avg_logprob=-0.2,
            no_speech_prob=0.01,
            duration_sec=5.0,
        )

        result = extractor.extract(asr_result)
        # 1 pause / 5.0 sec = 0.2
        assert result.silpsecutt == 0.2

    def test_within_clause_interruptions(self, extractor: DeliveryFeatureExtractor):
        """within_clause_interruptions: 절 내부 중단 (50ms~500ms pause)"""
        asr_result = ASRResult(
            transcript="Test",
            segments=[
                {"id": 0, "start": 0.0, "end": 1.0, "text": "A", "tokens": [1], "temperature": 0.0, "avg_logprob": -0.2, "compression_ratio": 1.0, "no_speech_prob": 0.01},
                # 0.1초 pause (100ms, 50~500ms 범위) → 절 내부 중단
                {"id": 1, "start": 1.1, "end": 2.0, "text": "B", "tokens": [2], "temperature": 0.0, "avg_logprob": -0.2, "compression_ratio": 1.0, "no_speech_prob": 0.01},
                # 0.2초 pause (200ms, 50~500ms 범위) → 절 내부 중단
                {"id": 2, "start": 2.2, "end": 3.0, "text": "C", "tokens": [3], "temperature": 0.0, "avg_logprob": -0.2, "compression_ratio": 1.0, "no_speech_prob": 0.01},
            ],
            language="en",
            avg_logprob=-0.2,
            no_speech_prob=0.01,
            duration_sec=3.0,
        )

        result = extractor.extract(asr_result)
        assert result.within_clause_interruptions == 2

    def test_within_clause_silence_mean(self, extractor: DeliveryFeatureExtractor):
        """within_clause_silence_mean_ms: 절 내부 평균 침묵 길이"""
        asr_result = ASRResult(
            transcript="Test",
            segments=[
                {"id": 0, "start": 0.0, "end": 1.0, "text": "A", "tokens": [1], "temperature": 0.0, "avg_logprob": -0.2, "compression_ratio": 1.0, "no_speech_prob": 0.01},
                # 0.1초 pause (100ms)
                {"id": 1, "start": 1.1, "end": 2.0, "text": "B", "tokens": [2], "temperature": 0.0, "avg_logprob": -0.2, "compression_ratio": 1.0, "no_speech_prob": 0.01},
                # 0.2초 pause (200ms)
                {"id": 2, "start": 2.2, "end": 3.0, "text": "C", "tokens": [3], "temperature": 0.0, "avg_logprob": -0.2, "compression_ratio": 1.0, "no_speech_prob": 0.01},
            ],
            language="en",
            avg_logprob=-0.2,
            no_speech_prob=0.01,
            duration_sec=3.0,
        )

        result = extractor.extract(asr_result)
        # (100 + 200) / 2 = 150ms
        assert result.within_clause_silence_mean_ms == 150.0

    def test_no_within_clause_pauses(self, extractor: DeliveryFeatureExtractor):
        """절 내부 pause가 없을 때 0 반환"""
        asr_result = ASRResult(
            transcript="Test",
            segments=[
                {"id": 0, "start": 0.0, "end": 1.0, "text": "A", "tokens": [1], "temperature": 0.0, "avg_logprob": -0.2, "compression_ratio": 1.0, "no_speech_prob": 0.01},
                # 0.6초 pause (>500ms, 절 간 pause로 간주)
                {"id": 1, "start": 1.6, "end": 2.0, "text": "B", "tokens": [2], "temperature": 0.0, "avg_logprob": -0.2, "compression_ratio": 1.0, "no_speech_prob": 0.01},
            ],
            language="en",
            avg_logprob=-0.2,
            no_speech_prob=0.01,
            duration_sec=2.0,
        )

        result = extractor.extract(asr_result)
        assert result.within_clause_interruptions == 0
        assert result.within_clause_silence_mean_ms == 0.0
