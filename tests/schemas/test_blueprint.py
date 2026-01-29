"""Blueprint 스키마 검증 테스트"""

import pytest
from pydantic import ValidationError

from src.models.enums import TopicType
from src.schemas.blueprint import (
    BlueprintContent,
    IndependentBlueprint,
    InfoUnit,
    IntegratedBlueprint,
    LinkingMove,
    ScoreExpectation,
    TimeBudget,
)

# === InfoUnit 테스트 ===


def test_info_unit_valid():
    """유효한 InfoUnit"""
    unit = InfoUnit(
        source="reading",
        label="Main Point",
        content="The article discusses the benefits of renewable energy.",
        importance="essential",
    )
    assert unit.source == "reading"
    assert unit.label == "Main Point"
    assert unit.importance == "essential"


def test_info_unit_default_importance():
    """InfoUnit 기본 importance 값"""
    unit = InfoUnit(
        source="listening",
        label="Example",
        content="The professor gives an example.",
    )
    assert unit.importance == "supporting"


def test_info_unit_invalid_source():
    """잘못된 source 값"""
    with pytest.raises(ValidationError) as exc_info:
        InfoUnit(
            source="video",  # Invalid
            label="Test",
            content="Test content",
        )
    assert "source" in str(exc_info.value)


# === LinkingMove 테스트 ===


def test_linking_move_valid():
    """유효한 LinkingMove"""
    move = LinkingMove(
        position="transition_to_listening",
        phrases=["According to the lecture", "The professor explains that"],
    )
    assert move.position == "transition_to_listening"
    assert len(move.phrases) == 2


def test_linking_move_empty_phrases():
    """빈 phrases 목록"""
    with pytest.raises(ValidationError) as exc_info:
        LinkingMove(
            position="contrast",
            phrases=[],  # Empty
        )
    assert "phrases" in str(exc_info.value)


# === TimeBudget 테스트 ===


def test_time_budget_valid():
    """유효한 TimeBudget"""
    budget = TimeBudget(
        intro_seconds=10,
        reading_summary_seconds=15,
        listening_summary_seconds=20,
        conclusion_seconds=5,
    )
    assert budget.intro_seconds == 10


def test_time_budget_defaults():
    """TimeBudget 기본값"""
    budget = TimeBudget()
    assert budget.intro_seconds == 10
    assert budget.reading_summary_seconds == 15
    assert budget.listening_summary_seconds == 20
    assert budget.conclusion_seconds == 5


def test_time_budget_out_of_range():
    """범위를 벗어난 시간 값"""
    with pytest.raises(ValidationError):
        TimeBudget(intro_seconds=20)  # max 15

    with pytest.raises(ValidationError):
        TimeBudget(intro_seconds=2)  # min 5


# === ScoreExpectation 테스트 ===


def test_score_expectation_valid():
    """유효한 ScoreExpectation (합 1.0)"""
    score = ScoreExpectation(
        structure_weight=0.3,
        language_weight=0.4,
        delivery_weight=0.3,
    )
    assert score.structure_weight + score.language_weight + score.delivery_weight == 1.0


def test_score_expectation_defaults():
    """ScoreExpectation 기본값"""
    score = ScoreExpectation()
    total = score.structure_weight + score.language_weight + score.delivery_weight
    assert abs(total - 1.0) < 0.01


def test_score_expectation_invalid_sum():
    """가중치 합이 1.0이 아닌 경우"""
    with pytest.raises(ValidationError) as exc_info:
        ScoreExpectation(
            structure_weight=0.5,
            language_weight=0.5,
            delivery_weight=0.5,  # 합 1.5
        )
    assert "가중치 합이 1.0이어야" in str(exc_info.value)


# === IntegratedBlueprint 테스트 ===


def test_integrated_blueprint_valid():
    """유효한 IntegratedBlueprint"""
    blueprint = IntegratedBlueprint(
        info_units=[
            InfoUnit(source="reading", label="Main Idea", content="The reading explains..."),
            InfoUnit(source="listening", label="Example 1", content="The professor mentions..."),
        ],
        recommended_order=["Main Idea", "Example 1"],
        linking_moves=[
            LinkingMove(position="transition", phrases=["However", "In contrast"]),
        ],
        coverage_expectations={"reading": 0.3, "listening": 0.7},
    )
    assert blueprint.schema_version == "1.0"
    assert len(blueprint.info_units) == 2


def test_integrated_blueprint_invalid_coverage_sum():
    """coverage_expectations 합이 1.0이 아닌 경우"""
    with pytest.raises(ValidationError) as exc_info:
        IntegratedBlueprint(
            info_units=[
                InfoUnit(source="reading", label="Test", content="Test"),
            ],
            recommended_order=["Test"],
            coverage_expectations={"reading": 0.5, "listening": 0.3},  # 합 0.8
        )
    assert "커버리지 합이 1.0이어야" in str(exc_info.value)


def test_integrated_blueprint_missing_coverage_keys():
    """coverage_expectations에 필수 키 누락"""
    with pytest.raises(ValidationError) as exc_info:
        IntegratedBlueprint(
            info_units=[
                InfoUnit(source="reading", label="Test", content="Test"),
            ],
            recommended_order=["Test"],
            coverage_expectations={"reading": 1.0},  # listening 누락
        )
    assert "reading과 listening이 필요" in str(exc_info.value)


def test_integrated_blueprint_extra_fields_forbidden():
    """추가 필드 금지"""
    with pytest.raises(ValidationError):
        IntegratedBlueprint(
            info_units=[
                InfoUnit(source="reading", label="Test", content="Test"),
            ],
            recommended_order=["Test"],
            extra_field="Not allowed",  # Extra field
        )


# === IndependentBlueprint 테스트 ===


def test_independent_blueprint_valid():
    """유효한 IndependentBlueprint"""
    blueprint = IndependentBlueprint(
        topic_type=TopicType.AGREE_DISAGREE,
        recommended_structure=["intro", "reason_1", "example_1", "conclusion"],
        linking_moves=[
            LinkingMove(position="intro", phrases=["I believe that"]),
        ],
        score_expectations=ScoreExpectation(),
        topic_specific_vocabulary=["education", "learning", "students"],
    )
    assert blueprint.topic_type == TopicType.AGREE_DISAGREE
    assert len(blueprint.recommended_structure) == 4


def test_independent_blueprint_defaults():
    """IndependentBlueprint 기본값"""
    blueprint = IndependentBlueprint(
        topic_type=TopicType.PREFERENCE,
        recommended_structure=["intro", "body", "conclusion"],
    )
    assert blueprint.schema_version == "1.0"
    assert len(blueprint.linking_moves) == 0
    assert len(blueprint.topic_specific_vocabulary) == 0


# === BlueprintContent 테스트 ===


def test_blueprint_content_integrated_valid():
    """유효한 Integrated BlueprintContent"""
    content = BlueprintContent(
        blueprint_type="integrated",
        data={
            "schema_version": "1.0",
            "info_units": [
                {"source": "reading", "label": "Main", "content": "Test"},
            ],
            "recommended_order": ["Main"],
            "linking_moves": [],
            "coverage_expectations": {"reading": 0.3, "listening": 0.7},
            "time_budget": {
                "intro_seconds": 10,
                "reading_summary_seconds": 15,
                "listening_summary_seconds": 20,
                "conclusion_seconds": 5,
            },
        },
    )
    assert content.blueprint_type == "integrated"


def test_blueprint_content_independent_valid():
    """유효한 Independent BlueprintContent"""
    content = BlueprintContent(
        blueprint_type="independent",
        data={
            "schema_version": "1.0",
            "topic_type": "agree_disagree",
            "recommended_structure": ["intro", "body", "conclusion"],
            "linking_moves": [],
            "score_expectations": {
                "structure_weight": 0.3,
                "language_weight": 0.4,
                "delivery_weight": 0.3,
            },
            "topic_specific_vocabulary": [],
            "time_budget": {
                "intro_seconds": 10,
                "body_seconds": 30,
                "conclusion_seconds": 5,
            },
        },
    )
    assert content.blueprint_type == "independent"


def test_blueprint_content_invalid_type():
    """잘못된 blueprint_type"""
    with pytest.raises(ValidationError):
        BlueprintContent(
            blueprint_type="invalid_type",
            data={},
        )


def test_blueprint_content_invalid_data():
    """blueprint_type과 맞지 않는 data"""
    with pytest.raises(ValidationError):
        BlueprintContent(
            blueprint_type="integrated",
            data={
                # Independent 스키마 데이터를 Integrated로 전달
                "topic_type": "preference",
                "recommended_structure": ["intro"],
            },
        )
