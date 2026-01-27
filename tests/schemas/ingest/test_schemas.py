"""
Ingest 스키마 테스트 - Pydantic v2 검증 로직 검증.

PRESERVE 단계: 기존 스키마 동작 검증
- 유효한 데이터 파싱 성공
- 필수 필드 누락 시 ValidationError 발생
- 필드 제약조건 (min_length, ge, enum) 적용
- extra="ignore" 동작 확인
"""
from datetime import datetime

import pytest
from pydantic import ValidationError

from src.schemas.ingest.answer_key import AnswerKeyIngest
from src.schemas.ingest.item import ItemIngest
from src.schemas.ingest.set import SetIngest
from src.schemas.ingest.stimulus import StimulusIngest
from src.schemas.ingest.topic import IndependentTopicIngest


class TestSetIngest:
    """SetIngest 스키마 검증"""

    def test_valid_data_parsing(self):
        """유효한 데이터가 올바르게 파싱됨"""
        # Given: 유효한 Set 데이터
        data = {
            "set_id": "ACTUAL_TEST_01",
            "title": "TOEFL Speaking Actual Test 1",
            "source": "ETS Official",
            "version": "v1.0",
        }

        # When
        schema = SetIngest.model_validate(data)

        # Then
        assert schema.set_id == "ACTUAL_TEST_01"
        assert schema.title == "TOEFL Speaking Actual Test 1"
        assert schema.source == "ETS Official"
        assert schema.version == "v1.0"

    def test_missing_required_field(self):
        """필수 필드 누락 시 ValidationError 발생"""
        # Given: title이 누락된 데이터
        data = {
            "set_id": "ACTUAL_TEST_01",
            "source": "ETS Official",
            "version": "v1.0",
        }

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            SetIngest.model_validate(data)

        assert "title" in str(exc_info.value)

    def test_set_id_min_length_constraint(self):
        """set_id가 빈 문자열이면 ValidationError 발생"""
        # Given: 빈 문자열 set_id
        data = {
            "set_id": "",
            "title": "Test",
            "source": "ETS",
            "version": "v1.0",
        }

        # When/Then
        with pytest.raises(ValidationError):
            SetIngest.model_validate(data)

    def test_set_id_max_length_constraint(self):
        """set_id가 100자를 초과하면 ValidationError 발생"""
        # Given: 101자 set_id
        data = {
            "set_id": "A" * 101,
            "title": "Test",
            "source": "ETS",
            "version": "v1.0",
        }

        # When/Then
        with pytest.raises(ValidationError):
            SetIngest.model_validate(data)

    def test_extra_fields_ignored(self):
        """extra="ignore" 설정으로 추가 필드가 무시됨"""
        # Given: 스키마에 없는 필드 포함
        data = {
            "set_id": "ACTUAL_TEST_01",
            "title": "Test",
            "source": "ETS",
            "version": "v1.0",
            "unknown_field": "should be ignored",
            "another_extra": 12345,
        }

        # When
        schema = SetIngest.model_validate(data)

        # Then: 추가 필드는 무시되고 스키마 생성 성공
        assert not hasattr(schema, "unknown_field")
        assert not hasattr(schema, "another_extra")

    def test_optional_datetime_fields(self):
        """created_at, updated_at은 선택 필드 (DB 자동 생성)"""
        # Given: 타임스탬프 필드가 포함된 데이터
        data = {
            "set_id": "ACTUAL_TEST_01",
            "title": "Test",
            "source": "ETS",
            "version": "v1.0",
            "created_at": "2024-01-27T10:00:00",
            "updated_at": "2024-01-27T11:00:00",
        }

        # When
        schema = SetIngest.model_validate(data)

        # Then: 타임스탬프 필드가 파싱됨
        assert isinstance(schema.created_at, datetime)
        assert isinstance(schema.updated_at, datetime)

    def test_without_optional_datetime_fields(self):
        """타임스탬프 필드 없이도 파싱 가능"""
        # Given
        data = {
            "set_id": "ACTUAL_TEST_01",
            "title": "Test",
            "source": "ETS",
            "version": "v1.0",
        }

        # When
        schema = SetIngest.model_validate(data)

        # Then
        assert schema.created_at is None
        assert schema.updated_at is None


class TestItemIngest:
    """ItemIngest 스키마 검증"""

    def test_valid_independent_item(self):
        """유효한 independent 문항 파싱"""
        # Given
        data = {
            "item_id": "ITEM_INDEPENDENT_001",
            "set_id": "ACTUAL_TEST_01",
            "task_no": 1,
            "task_type": "independent",
            "prompt": "Do you agree or disagree?",
        }

        # When
        schema = ItemIngest.model_validate(data)

        # Then
        assert schema.item_id == "ITEM_INDEPENDENT_001"
        assert schema.task_type == "independent"
        assert schema.prep_seconds == 15  # 기본값
        assert schema.response_seconds == 45  # 기본값

    def test_valid_integrated_read_listen_item(self):
        """integrated_read_listen 타입 검증"""
        # Given
        data = {
            "item_id": "ITEM_INTEGRATED_001",
            "set_id": "ACTUAL_TEST_01",
            "task_no": 2,
            "task_type": "integrated_read_listen",
            "prompt": "Summarize the reading and lecture.",
            "prep_seconds": 30,
            "response_seconds": 60,
        }

        # When
        schema = ItemIngest.model_validate(data)

        # Then
        assert schema.task_type == "integrated_read_listen"
        assert schema.prep_seconds == 30
        assert schema.response_seconds == 60

    def test_invalid_task_type(self):
        """잘못된 task_type은 ValidationError 발생"""
        # Given
        data = {
            "item_id": "ITEM_001",
            "set_id": "SET_001",
            "task_no": 1,
            "task_type": "invalid_type",
            "prompt": "Test",
        }

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            ItemIngest.model_validate(data)

        assert "task_type" in str(exc_info.value)

    def test_task_no_must_be_positive(self):
        """task_no는 1 이상이어야 함"""
        # Given
        data = {
            "item_id": "ITEM_001",
            "set_id": "SET_001",
            "task_no": 0,
            "task_type": "independent",
            "prompt": "Test",
        }

        # When/Then
        with pytest.raises(ValidationError):
            ItemIngest.model_validate(data)

    def test_tags_default_empty_list(self):
        """tags 필드는 기본값으로 빈 리스트"""
        # Given
        data = {
            "item_id": "ITEM_001",
            "set_id": "SET_001",
            "task_no": 1,
            "task_type": "independent",
            "prompt": "Test",
        }

        # When
        schema = ItemIngest.model_validate(data)

        # Then
        assert schema.tags == []

    def test_tags_with_values(self):
        """tags 리스트가 올바르게 파싱됨"""
        # Given
        data = {
            "item_id": "ITEM_001",
            "set_id": "SET_001",
            "task_no": 1,
            "task_type": "independent",
            "prompt": "Test",
            "tags": ["education", "personal_preference"],
        }

        # When
        schema = ItemIngest.model_validate(data)

        # Then
        assert schema.tags == ["education", "personal_preference"]


class TestStimulusIngest:
    """StimulusIngest 스키마 검증"""

    def test_valid_reading_stimulus(self):
        """reading 타입 자극자료 파싱"""
        # Given
        data = {
            "stimulus_id": "STIMULUS_READING_001",
            "item_id": "ITEM_001",
            "kind": "reading",
            "title": "University Announcement",
            "content_text": "The university will close the library...",
        }

        # When
        schema = StimulusIngest.model_validate(data)

        # Then
        assert schema.kind == "reading"
        assert schema.notes_allowed is True  # 기본값

    def test_valid_listening_stimulus(self):
        """listening 타입 자극자료 파싱"""
        # Given
        data = {
            "stimulus_id": "STIMULUS_LISTENING_001",
            "item_id": "ITEM_001",
            "kind": "listening",
            "title": "Lecture on Biology",
            "asset_url": "https://example.com/audio.mp3",
            "duration_seconds": 90.5,
        }

        # When
        schema = StimulusIngest.model_validate(data)

        # Then
        assert schema.kind == "listening"
        assert schema.duration_seconds == 90.5

    def test_invalid_kind(self):
        """잘못된 kind는 ValidationError 발생"""
        # Given
        data = {
            "stimulus_id": "STIMULUS_001",
            "item_id": "ITEM_001",
            "kind": "invalid_kind",
            "title": "Test",
        }

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            StimulusIngest.model_validate(data)

        assert "kind" in str(exc_info.value)

    def test_order_must_be_non_negative(self):
        """order는 0 이상이어야 함"""
        # Given
        data = {
            "stimulus_id": "STIMULUS_001",
            "item_id": "ITEM_001",
            "kind": "reading",
            "title": "Test",
            "order": -1,
        }

        # When/Then
        with pytest.raises(ValidationError):
            StimulusIngest.model_validate(data)

    def test_optional_fields(self):
        """content_text, asset_url, duration_seconds는 선택 필드"""
        # Given: 필수 필드만 포함
        data = {
            "stimulus_id": "STIMULUS_001",
            "item_id": "ITEM_001",
            "kind": "direction",
            "title": "Instructions",
        }

        # When
        schema = StimulusIngest.model_validate(data)

        # Then
        assert schema.content_text is None
        assert schema.asset_url is None
        assert schema.duration_seconds is None


class TestAnswerKeyIngest:
    """AnswerKeyIngest 스키마 검증"""

    def test_valid_sample_response(self):
        """sample_response 타입 모범답안 파싱"""
        # Given
        data = {
            "answer_id": "ANSWER_SAMPLE_001",
            "item_id": "ITEM_001",
            "type": "sample_response",
            "level": "advanced",
            "content": "I strongly believe that...",
            "source": "ETS Official Guide",
        }

        # When
        schema = AnswerKeyIngest.model_validate(data)

        # Then
        assert schema.type == "sample_response"
        assert schema.level == "advanced"

    def test_valid_transcript(self):
        """transcript 타입 모범답안 파싱"""
        # Given
        data = {
            "answer_id": "ANSWER_TRANSCRIPT_001",
            "item_id": "ITEM_001",
            "type": "transcript",
            "content": "In this lecture, the professor discusses...",
            "source": "Official Test",
        }

        # When
        schema = AnswerKeyIngest.model_validate(data)

        # Then
        assert schema.type == "transcript"
        assert schema.level is None  # 선택 필드

    def test_invalid_type(self):
        """잘못된 type은 ValidationError 발생"""
        # Given
        data = {
            "answer_id": "ANSWER_001",
            "item_id": "ITEM_001",
            "type": "invalid_type",
            "content": "Test",
            "source": "Test",
        }

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            AnswerKeyIngest.model_validate(data)

        assert "type" in str(exc_info.value)

    def test_invalid_level(self):
        """잘못된 level은 ValidationError 발생"""
        # Given
        data = {
            "answer_id": "ANSWER_001",
            "item_id": "ITEM_001",
            "type": "sample_response",
            "level": "invalid_level",
            "content": "Test",
            "source": "Test",
        }

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            AnswerKeyIngest.model_validate(data)

        assert "level" in str(exc_info.value)

    def test_all_valid_levels(self):
        """basic, advanced, ultimate 레벨 모두 유효"""
        # Given/When/Then
        for level in ["basic", "advanced", "ultimate"]:
            data = {
                "answer_id": f"ANSWER_{level.upper()}",
                "item_id": "ITEM_001",
                "type": "sample_response",
                "level": level,
                "content": "Test",
                "source": "Test",
            }
            schema = AnswerKeyIngest.model_validate(data)
            assert schema.level == level


class TestIndependentTopicIngest:
    """IndependentTopicIngest 스키마 검증"""

    def test_valid_topic(self):
        """유효한 토픽 데이터 파싱"""
        # Given
        data = {
            "topic_id": "TOPIC_001",
            "number": 1,
            "prompt": "Do you agree or disagree with the following statement?",
            "source": "Independent_Topics.pdf",
        }

        # When
        schema = IndependentTopicIngest.model_validate(data)

        # Then
        assert schema.topic_id == "TOPIC_001"
        assert schema.number == 1
        assert schema.prompt == "Do you agree or disagree with the following statement?"
        assert schema.source == "Independent_Topics.pdf"

    def test_missing_required_fields(self):
        """필수 필드 누락 시 ValidationError 발생"""
        # Given: prompt가 누락
        data = {
            "topic_id": "TOPIC_001",
            "number": 1,
            "source": "Independent_Topics.pdf",
        }

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            IndependentTopicIngest.model_validate(data)

        assert "prompt" in str(exc_info.value)

    def test_number_must_be_positive(self):
        """number는 1 이상이어야 함"""
        # Given
        data = {
            "topic_id": "TOPIC_001",
            "number": 0,
            "prompt": "Test",
            "source": "Test",
        }

        # When/Then
        with pytest.raises(ValidationError):
            IndependentTopicIngest.model_validate(data)

    def test_topic_id_min_length(self):
        """topic_id는 빈 문자열 불가"""
        # Given
        data = {
            "topic_id": "",
            "number": 1,
            "prompt": "Test",
            "source": "Test",
        }

        # When/Then
        with pytest.raises(ValidationError):
            IndependentTopicIngest.model_validate(data)

    def test_prompt_min_length(self):
        """prompt는 빈 문자열 불가"""
        # Given
        data = {
            "topic_id": "TOPIC_001",
            "number": 1,
            "prompt": "",
            "source": "Test",
        }

        # When/Then
        with pytest.raises(ValidationError):
            IndependentTopicIngest.model_validate(data)


class TestRealWorldDataParsing:
    """실제 JSON 파일 데이터 파싱 시나리오"""

    def test_parse_actual_test_01_set(self):
        """external/sets.json의 ACTUAL_TEST_01 데이터 파싱"""
        # Given: 실제 JSON 데이터 구조
        data = {
            "set_id": "ACTUAL_TEST_01",
            "title": "TOEFL iBT Speaking - Actual Test 01",
            "source": "ETS Official Tests Vol.1",
            "version": "v1.0",
            "created_at": "2024-01-01T00:00:00Z",
        }

        # When
        schema = SetIngest.model_validate(data)

        # Then
        assert schema.set_id == "ACTUAL_TEST_01"
        assert "Actual Test 01" in schema.title

    def test_parse_independent_topic_from_json(self):
        """external/independent_topics.json 데이터 샘플 파싱"""
        # Given: 실제 토픽 데이터
        data = {
            "topic_id": "IND_TOPIC_001",
            "number": 1,
            "prompt": "Some people prefer to live in a small town. Others prefer to live in a big city. Which place would you prefer to live in?",
            "source": "Independent_Topics.pdf",
        }

        # When
        schema = IndependentTopicIngest.model_validate(data)

        # Then
        assert schema.number == 1
        assert "small town" in schema.prompt
        assert "big city" in schema.prompt
