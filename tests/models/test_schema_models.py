"""정규화 스키마 모델 테스트 (Set, Item, Stimulus, AnswerKey)"""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.answer_key import AnswerKey
from src.models.enums import (
    AnswerKeyLevel,
    AnswerKeyType,
    Difficulty,
    StimulusKind,
    TopicCategory,
    TopicType,
)
from src.models.item import Item
from src.models.set import Set
from src.models.stimulus import Stimulus
from src.models.task import TaskType


# === Set 모델 테스트 ===


@pytest.mark.asyncio
async def test_create_set(test_db: AsyncSession):
    """Set 생성 테스트"""
    new_set = Set(
        id=uuid.uuid4(),
        title="ETS Practice Set 1",
        source="ETS Official",
        version="v1.0",
        description="공식 연습 문제 세트",
    )
    test_db.add(new_set)
    await test_db.commit()
    await test_db.refresh(new_set)

    assert new_set.id is not None
    assert new_set.title == "ETS Practice Set 1"
    assert new_set.source == "ETS Official"
    assert new_set.version == "v1.0"
    assert new_set.created_at is not None
    assert new_set.updated_at is not None


@pytest.mark.asyncio
async def test_set_repr(test_db: AsyncSession):
    """Set __repr__ 테스트"""
    new_set = Set(
        id=uuid.uuid4(),
        title="Test Set",
        source="Test Source",
        version="v1.0",
    )
    test_db.add(new_set)
    await test_db.commit()
    await test_db.refresh(new_set)

    repr_str = repr(new_set)
    assert "Set(" in repr_str
    assert "Test Set" in repr_str
    assert "Test Source" in repr_str


# === Item 모델 테스트 ===


@pytest.fixture
async def test_set(test_db: AsyncSession) -> Set:
    """테스트용 Set"""
    new_set = Set(
        id=uuid.uuid4(),
        title="Test Set",
        source="Test",
        version="v1.0",
    )
    test_db.add(new_set)
    await test_db.commit()
    await test_db.refresh(new_set)
    return new_set


@pytest.mark.asyncio
async def test_create_independent_item(test_db: AsyncSession, test_set: Set):
    """Independent Item 생성 테스트"""
    item = Item(
        id=uuid.uuid4(),
        set_id=test_set.id,
        task_no=1,
        task_type=TaskType.INDEPENDENT,
        prompt="Do you agree or disagree with the following statement?",
        prep_seconds=15,
        response_seconds=45,
        topic_type=TopicType.AGREE_DISAGREE,
        topic_category=TopicCategory.EDUCATION,
        difficulty=Difficulty.MEDIUM,
    )
    test_db.add(item)
    await test_db.commit()
    await test_db.refresh(item)

    assert item.id is not None
    assert item.set_id == test_set.id
    assert item.task_no == 1
    assert item.task_type == TaskType.INDEPENDENT
    assert item.topic_type == TopicType.AGREE_DISAGREE
    assert item.topic_category == TopicCategory.EDUCATION


@pytest.mark.asyncio
async def test_create_integrated_item(test_db: AsyncSession, test_set: Set):
    """Integrated Item 생성 테스트"""
    item = Item(
        id=uuid.uuid4(),
        set_id=test_set.id,
        task_no=3,
        task_type=TaskType.INTEGRATED,
        prompt="Summarize the reading passage and the lecture.",
        prep_seconds=30,
        response_seconds=60,
        difficulty=Difficulty.HARD,
    )
    test_db.add(item)
    await test_db.commit()
    await test_db.refresh(item)

    assert item.task_type == TaskType.INTEGRATED
    assert item.topic_type is None
    assert item.topic_category is None


@pytest.mark.asyncio
async def test_item_set_relationship(test_db: AsyncSession, test_set: Set):
    """Item-Set 관계 테스트"""
    item = Item(
        id=uuid.uuid4(),
        set_id=test_set.id,
        task_no=1,
        task_type=TaskType.INDEPENDENT,
        prompt="Test prompt",
    )
    test_db.add(item)
    await test_db.commit()
    await test_db.refresh(item)

    # Item -> Set 관계
    assert item.set is not None
    assert item.set.id == test_set.id
    assert item.set.title == "Test Set"


@pytest.mark.asyncio
async def test_set_items_relationship(test_db: AsyncSession, test_set: Set):
    """Set-Items 관계 테스트"""
    # 여러 Item 생성
    for i in range(1, 5):
        item = Item(
            id=uuid.uuid4(),
            set_id=test_set.id,
            task_no=i,
            task_type=TaskType.INDEPENDENT if i <= 2 else TaskType.INTEGRATED,
            prompt=f"Task {i} prompt",
        )
        test_db.add(item)

    await test_db.commit()
    await test_db.refresh(test_set)

    # Set -> Items 관계
    assert len(test_set.items) == 4
    assert all(item.set_id == test_set.id for item in test_set.items)


# === Stimulus 모델 테스트 ===


@pytest.fixture
async def test_item(test_db: AsyncSession, test_set: Set) -> Item:
    """테스트용 Item"""
    item = Item(
        id=uuid.uuid4(),
        set_id=test_set.id,
        task_no=1,
        task_type=TaskType.INTEGRATED,
        prompt="Test prompt",
    )
    test_db.add(item)
    await test_db.commit()
    await test_db.refresh(item)
    return item


@pytest.mark.asyncio
async def test_create_reading_stimulus(test_db: AsyncSession, test_item: Item):
    """Reading Stimulus 생성 테스트"""
    stimulus = Stimulus(
        id=uuid.uuid4(),
        item_id=test_item.id,
        kind=StimulusKind.READING,
        title="Reading Passage",
        content_text="This is a sample reading passage for the test.",
        display_order=0,
        notes_allowed=True,
    )
    test_db.add(stimulus)
    await test_db.commit()
    await test_db.refresh(stimulus)

    assert stimulus.kind == StimulusKind.READING
    assert stimulus.content_text is not None
    assert stimulus.notes_allowed is True


@pytest.mark.asyncio
async def test_create_audio_stimulus(test_db: AsyncSession, test_item: Item):
    """Audio Stimulus 생성 테스트"""
    stimulus = Stimulus(
        id=uuid.uuid4(),
        item_id=test_item.id,
        kind=StimulusKind.AUDIO,
        title="Lecture Audio",
        asset_url="https://example.com/audio/lecture.mp3",
        duration_seconds=120,
        display_order=1,
    )
    test_db.add(stimulus)
    await test_db.commit()
    await test_db.refresh(stimulus)

    assert stimulus.kind == StimulusKind.AUDIO
    assert stimulus.asset_url is not None
    assert stimulus.duration_seconds == 120


@pytest.mark.asyncio
async def test_stimulus_display_order(test_db: AsyncSession, test_item: Item):
    """Stimulus display_order 정렬 테스트"""
    # 여러 Stimulus 생성 (순서를 섞어서)
    stimuli_data = [
        (StimulusKind.READING, 0),
        (StimulusKind.AUDIO, 2),
        (StimulusKind.DIRECTION, 1),
    ]
    for kind, order in stimuli_data:
        stimulus = Stimulus(
            id=uuid.uuid4(),
            item_id=test_item.id,
            kind=kind,
            content_text="Test" if kind != StimulusKind.AUDIO else None,
            asset_url="https://example.com/audio.mp3" if kind == StimulusKind.AUDIO else None,
            display_order=order,
        )
        test_db.add(stimulus)

    await test_db.commit()
    await test_db.refresh(test_item)

    # 정렬 확인
    assert len(test_item.stimuli) == 3
    orders = [s.display_order for s in test_item.stimuli]
    assert orders == [0, 1, 2]


# === AnswerKey 모델 테스트 ===


@pytest.mark.asyncio
async def test_create_sample_response_answer_key(test_db: AsyncSession, test_item: Item):
    """sample_response AnswerKey 생성 테스트"""
    answer_key = AnswerKey(
        id=uuid.uuid4(),
        item_id=test_item.id,
        answer_type=AnswerKeyType.SAMPLE_RESPONSE,
        level=AnswerKeyLevel.HIGH,
        content={"text": "This is a high-quality sample response."},
        source="ETS Official",
    )
    test_db.add(answer_key)
    await test_db.commit()
    await test_db.refresh(answer_key)

    assert answer_key.answer_type == AnswerKeyType.SAMPLE_RESPONSE
    assert answer_key.level == AnswerKeyLevel.HIGH
    assert answer_key.content["text"] is not None


@pytest.mark.asyncio
async def test_create_blueprint_answer_key(test_db: AsyncSession, test_item: Item):
    """blueprint AnswerKey 생성 테스트"""
    blueprint_content = {
        "blueprint_type": "integrated",
        "data": {
            "schema_version": "1.0",
            "info_units": [
                {"source": "reading", "label": "Main Point", "content": "The main idea..."},
                {"source": "listening", "label": "Example", "content": "The professor explains..."},
            ],
            "recommended_order": ["Main Point", "Example"],
            "linking_moves": [],
            "coverage_expectations": {"reading": 0.3, "listening": 0.7},
            "time_budget": {
                "intro_seconds": 10,
                "reading_summary_seconds": 15,
                "listening_summary_seconds": 20,
                "conclusion_seconds": 5,
            },
        },
    }
    answer_key = AnswerKey(
        id=uuid.uuid4(),
        item_id=test_item.id,
        answer_type=AnswerKeyType.BLUEPRINT,
        content=blueprint_content,
        source="Expert Review",
    )
    test_db.add(answer_key)
    await test_db.commit()
    await test_db.refresh(answer_key)

    assert answer_key.answer_type == AnswerKeyType.BLUEPRINT
    assert answer_key.content["blueprint_type"] == "integrated"


@pytest.mark.asyncio
async def test_answer_key_levels(test_db: AsyncSession, test_item: Item):
    """AnswerKey level 테스트"""
    levels = [AnswerKeyLevel.HIGH, AnswerKeyLevel.MID, AnswerKeyLevel.LOW]

    for level in levels:
        answer_key = AnswerKey(
            id=uuid.uuid4(),
            item_id=test_item.id,
            answer_type=AnswerKeyType.SAMPLE_RESPONSE,
            level=level,
            content={"text": f"Sample response for {level.value} level"},
        )
        test_db.add(answer_key)

    await test_db.commit()
    await test_db.refresh(test_item)

    assert len(test_item.answer_keys) == 3


# === CASCADE 삭제 테스트 ===


@pytest.mark.asyncio
async def test_set_cascade_delete(test_db: AsyncSession):
    """Set 삭제 시 Item, Stimulus, AnswerKey CASCADE 삭제 테스트"""
    # Set 생성
    new_set = Set(
        id=uuid.uuid4(),
        title="Cascade Test Set",
        source="Test",
        version="v1.0",
    )
    test_db.add(new_set)
    await test_db.commit()

    # Item 생성
    item = Item(
        id=uuid.uuid4(),
        set_id=new_set.id,
        task_no=1,
        task_type=TaskType.INDEPENDENT,
        prompt="Test",
    )
    test_db.add(item)
    await test_db.commit()

    item_id = item.id

    # Stimulus 생성
    stimulus = Stimulus(
        id=uuid.uuid4(),
        item_id=item.id,
        kind=StimulusKind.DIRECTION,
        content_text="Test direction",
    )
    test_db.add(stimulus)
    await test_db.commit()

    stimulus_id = stimulus.id

    # AnswerKey 생성
    answer_key = AnswerKey(
        id=uuid.uuid4(),
        item_id=item.id,
        answer_type=AnswerKeyType.POINTS,
        content={"key_points": ["Point 1"]},
    )
    test_db.add(answer_key)
    await test_db.commit()

    answer_key_id = answer_key.id

    # Set 삭제
    await test_db.delete(new_set)
    await test_db.commit()

    # CASCADE 삭제 확인
    item_result = await test_db.execute(select(Item).where(Item.id == item_id))
    assert item_result.scalar_one_or_none() is None

    stimulus_result = await test_db.execute(select(Stimulus).where(Stimulus.id == stimulus_id))
    assert stimulus_result.scalar_one_or_none() is None

    answer_key_result = await test_db.execute(select(AnswerKey).where(AnswerKey.id == answer_key_id))
    assert answer_key_result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_item_cascade_delete(test_db: AsyncSession, test_set: Set):
    """Item 삭제 시 Stimulus, AnswerKey CASCADE 삭제 테스트"""
    # Item 생성
    item = Item(
        id=uuid.uuid4(),
        set_id=test_set.id,
        task_no=1,
        task_type=TaskType.INDEPENDENT,
        prompt="Test",
    )
    test_db.add(item)
    await test_db.commit()

    # Stimulus 및 AnswerKey 생성
    stimulus = Stimulus(
        id=uuid.uuid4(),
        item_id=item.id,
        kind=StimulusKind.DIRECTION,
        content_text="Test",
    )
    answer_key = AnswerKey(
        id=uuid.uuid4(),
        item_id=item.id,
        answer_type=AnswerKeyType.POINTS,
        content={"key_points": []},
    )
    test_db.add_all([stimulus, answer_key])
    await test_db.commit()

    stimulus_id = stimulus.id
    answer_key_id = answer_key.id

    # Item 삭제
    await test_db.delete(item)
    await test_db.commit()

    # CASCADE 삭제 확인
    stimulus_result = await test_db.execute(select(Stimulus).where(Stimulus.id == stimulus_id))
    assert stimulus_result.scalar_one_or_none() is None

    answer_key_result = await test_db.execute(select(AnswerKey).where(AnswerKey.id == answer_key_id))
    assert answer_key_result.scalar_one_or_none() is None


# === Enum 테스트 ===


def test_topic_type_enum_values():
    """TopicType Enum 값 테스트"""
    assert TopicType.PREFERENCE.value == "preference"
    assert TopicType.AGREE_DISAGREE.value == "agree_disagree"
    assert TopicType.DESCRIPTION.value == "description"
    assert TopicType.OPINION.value == "opinion"
    assert TopicType.HYPOTHETICAL.value == "hypothetical"


def test_topic_category_enum_values():
    """TopicCategory Enum 값 테스트"""
    assert TopicCategory.EDUCATION.value == "education"
    assert TopicCategory.TECHNOLOGY.value == "technology"
    assert TopicCategory.LIFESTYLE.value == "lifestyle"
    assert TopicCategory.WORK.value == "work"
    assert TopicCategory.RELATIONSHIPS.value == "relationships"
    assert TopicCategory.SOCIETY.value == "society"


def test_stimulus_kind_enum_values():
    """StimulusKind Enum 값 테스트"""
    assert StimulusKind.READING.value == "reading"
    assert StimulusKind.AUDIO.value == "audio"
    assert StimulusKind.IMAGE.value == "image"
    assert StimulusKind.DIRECTION.value == "direction"


def test_answer_key_type_enum_values():
    """AnswerKeyType Enum 값 테스트"""
    assert AnswerKeyType.SAMPLE_RESPONSE.value == "sample_response"
    assert AnswerKeyType.TRANSCRIPT.value == "transcript"
    assert AnswerKeyType.OUTLINE.value == "outline"
    assert AnswerKeyType.POINTS.value == "points"
    assert AnswerKeyType.BLUEPRINT.value == "blueprint"


def test_answer_key_level_enum_values():
    """AnswerKeyLevel Enum 값 테스트"""
    assert AnswerKeyLevel.HIGH.value == "high"
    assert AnswerKeyLevel.MID.value == "mid"
    assert AnswerKeyLevel.LOW.value == "low"
