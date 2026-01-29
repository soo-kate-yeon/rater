"""Stimulus API 엔드포인트 테스트"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.enums import StimulusKind
from src.models.item import Item
from src.models.set import Set
from src.models.stimulus import Stimulus
from src.models.task import TaskType


@pytest_asyncio.fixture
async def test_set_for_stimulus(test_db: AsyncSession) -> Set:
    """테스트용 Set"""
    new_set = Set(
        id=uuid.uuid4(),
        title="Stimulus Test Set",
        source="Test",
        version="v1.0",
    )
    test_db.add(new_set)
    await test_db.commit()
    await test_db.refresh(new_set)
    return new_set


@pytest_asyncio.fixture
async def test_item_for_stimulus(test_db: AsyncSession, test_set_for_stimulus: Set) -> Item:
    """테스트용 Item (Integrated Task)"""
    item = Item(
        id=uuid.uuid4(),
        set_id=test_set_for_stimulus.id,
        task_no=2,
        task_type=TaskType.INTEGRATED,
        prompt="Summarize the points made in the lecture.",
        topic_type=None,
        topic_category=None,
    )
    test_db.add(item)
    await test_db.commit()
    await test_db.refresh(item)
    return item


@pytest_asyncio.fixture
async def test_stimulus(test_db: AsyncSession, test_item_for_stimulus: Item) -> Stimulus:
    """테스트용 Stimulus (Reading)"""
    stimulus = Stimulus(
        id=uuid.uuid4(),
        item_id=test_item_for_stimulus.id,
        kind=StimulusKind.READING,
        title="Academic Reading Passage",
        content_text="This is a sample academic reading passage about environmental science.",
        asset_url=None,
        duration_seconds=None,
        display_order=1,
        notes_allowed=True,
    )
    test_db.add(stimulus)
    await test_db.commit()
    await test_db.refresh(stimulus)
    return stimulus


# ============================================================================
# GET /api/v1/stimuli - 목록 조회
# ============================================================================


@pytest.mark.asyncio
async def test_list_stimuli_success(test_client: AsyncClient, test_stimulus: Stimulus):
    """Stimulus 목록 조회 성공"""
    response = await test_client.get("/api/v1/stimuli")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_stimuli_filter_by_item_id(
    test_client: AsyncClient, test_item_for_stimulus: Item, test_stimulus: Stimulus
):
    """item_id 필터로 Stimulus 목록 조회"""
    response = await test_client.get(f"/api/v1/stimuli?item_id={test_item_for_stimulus.id}")

    assert response.status_code == 200
    data = response.json()
    assert all(item["item_id"] == str(test_item_for_stimulus.id) for item in data["items"])


@pytest.mark.asyncio
async def test_list_stimuli_invalid_item_id(test_client: AsyncClient):
    """잘못된 item_id 형식으로 목록 조회 시 400 에러"""
    response = await test_client.get("/api/v1/stimuli?item_id=invalid-uuid")

    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_stimuli_ordered_by_display_order(
    test_client: AsyncClient, test_db: AsyncSession, test_item_for_stimulus: Item
):
    """Stimulus 목록이 display_order 순으로 정렬되는지 확인"""
    # 여러 개의 Stimulus 생성 (display_order가 다름)
    stimuli_data = [
        {"kind": StimulusKind.READING, "display_order": 2},
        {"kind": StimulusKind.AUDIO, "display_order": 1},
        {"kind": StimulusKind.AUDIO, "display_order": 3},
    ]

    for data in stimuli_data:
        stimulus = Stimulus(
            id=uuid.uuid4(),
            item_id=test_item_for_stimulus.id,
            kind=data["kind"],
            title=f"Test {data['kind'].value}",
            content_text=f"Content for {data['kind'].value}",
            display_order=data["display_order"],
        )
        test_db.add(stimulus)
    await test_db.commit()

    # 목록 조회
    response = await test_client.get(f"/api/v1/stimuli?item_id={test_item_for_stimulus.id}")

    assert response.status_code == 200
    items = response.json()["items"]

    # display_order 순으로 정렬되어 있는지 확인
    orders = [item["display_order"] for item in items]
    assert orders == sorted(orders)


# ============================================================================
# POST /api/v1/stimuli - 생성
# ============================================================================


@pytest.mark.asyncio
async def test_create_reading_stimulus_success(
    test_client: AsyncClient, test_item_for_stimulus: Item
):
    """Reading Stimulus 생성 성공"""
    response = await test_client.post(
        "/api/v1/stimuli",
        json={
            "item_id": str(test_item_for_stimulus.id),
            "kind": StimulusKind.READING.value,
            "title": "Reading Passage",
            "content_text": "This is the reading passage content.",
            "display_order": 1,
            "notes_allowed": True,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["item_id"] == str(test_item_for_stimulus.id)
    assert data["kind"] == StimulusKind.READING.value
    assert data["content_text"] == "This is the reading passage content."


@pytest.mark.asyncio
async def test_create_listening_stimulus_success(
    test_client: AsyncClient, test_item_for_stimulus: Item
):
    """Listening Stimulus 생성 성공 (audio URL 포함)"""
    response = await test_client.post(
        "/api/v1/stimuli",
        json={
            "item_id": str(test_item_for_stimulus.id),
            "kind": StimulusKind.AUDIO.value,
            "title": "Lecture Audio",
            "content_text": "Transcript of the lecture.",
            "asset_url": "https://example.com/audio/lecture.mp3",
            "duration_seconds": 180,
            "display_order": 2,
            "notes_allowed": True,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["kind"] == StimulusKind.AUDIO.value
    assert data["asset_url"] == "https://example.com/audio/lecture.mp3"
    assert data["duration_seconds"] == 180


@pytest.mark.asyncio
async def test_create_stimulus_item_not_found(test_client: AsyncClient):
    """존재하지 않는 Item으로 Stimulus 생성 시 404 에러"""
    fake_item_id = str(uuid.uuid4())
    response = await test_client.post(
        "/api/v1/stimuli",
        json={
            "item_id": fake_item_id,
            "kind": StimulusKind.READING.value,
            "title": "Test",
            "content_text": "Test content",
            "display_order": 1,
        },
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_stimulus_missing_fields(test_client: AsyncClient):
    """필수 필드 누락 시 422 에러"""
    response = await test_client.post(
        "/api/v1/stimuli",
        json={
            "item_id": str(uuid.uuid4()),
            # kind, title, display_order 누락
        },
    )

    assert response.status_code == 422


# ============================================================================
# GET /api/v1/stimuli/{stimulus_id} - 단일 조회
# ============================================================================


@pytest.mark.asyncio
async def test_get_stimulus_success(test_client: AsyncClient, test_stimulus: Stimulus):
    """Stimulus 단일 조회 성공"""
    response = await test_client.get(f"/api/v1/stimuli/{test_stimulus.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_stimulus.id)
    assert data["title"] == test_stimulus.title
    assert data["content_text"] == test_stimulus.content_text


@pytest.mark.asyncio
async def test_get_stimulus_not_found(test_client: AsyncClient):
    """존재하지 않는 Stimulus 조회 시 404 에러"""
    fake_id = str(uuid.uuid4())
    response = await test_client.get(f"/api/v1/stimuli/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_stimulus_invalid_uuid(test_client: AsyncClient):
    """잘못된 UUID 형식으로 조회 시 400 에러"""
    response = await test_client.get("/api/v1/stimuli/invalid-uuid")

    assert response.status_code == 400


# ============================================================================
# PATCH /api/v1/stimuli/{stimulus_id} - 수정
# ============================================================================


@pytest.mark.asyncio
async def test_update_stimulus_success(test_client: AsyncClient, test_stimulus: Stimulus):
    """Stimulus 수정 성공"""
    response = await test_client.patch(
        f"/api/v1/stimuli/{test_stimulus.id}",
        json={
            "title": "Updated Title",
            "content_text": "Updated content text",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["content_text"] == "Updated content text"


@pytest.mark.asyncio
async def test_update_stimulus_partial(test_client: AsyncClient, test_stimulus: Stimulus):
    """Stimulus 일부 필드만 수정"""
    original_title = test_stimulus.title
    response = await test_client.patch(
        f"/api/v1/stimuli/{test_stimulus.id}",
        json={
            "notes_allowed": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["notes_allowed"] is False
    assert data["title"] == original_title  # title은 변경되지 않음


@pytest.mark.asyncio
async def test_update_stimulus_not_found(test_client: AsyncClient):
    """존재하지 않는 Stimulus 수정 시 404 에러"""
    fake_id = str(uuid.uuid4())
    response = await test_client.patch(
        f"/api/v1/stimuli/{fake_id}",
        json={"title": "Updated Title"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_stimulus_display_order(test_client: AsyncClient, test_stimulus: Stimulus):
    """Stimulus display_order 변경"""
    response = await test_client.patch(
        f"/api/v1/stimuli/{test_stimulus.id}",
        json={"display_order": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["display_order"] == 5


# ============================================================================
# DELETE /api/v1/stimuli/{stimulus_id} - 삭제
# ============================================================================


@pytest.mark.asyncio
async def test_delete_stimulus_success(test_client: AsyncClient, test_stimulus: Stimulus):
    """Stimulus 삭제 성공"""
    response = await test_client.delete(f"/api/v1/stimuli/{test_stimulus.id}")

    assert response.status_code == 204

    # 삭제 확인
    get_response = await test_client.get(f"/api/v1/stimuli/{test_stimulus.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_stimulus_not_found(test_client: AsyncClient):
    """존재하지 않는 Stimulus 삭제 시 404 에러"""
    fake_id = str(uuid.uuid4())
    response = await test_client.delete(f"/api/v1/stimuli/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_stimulus_invalid_uuid(test_client: AsyncClient):
    """잘못된 UUID 형식으로 삭제 시 400 에러"""
    response = await test_client.delete("/api/v1/stimuli/invalid-uuid")

    assert response.status_code == 400


# ============================================================================
# 복합 시나리오 테스트
# ============================================================================


@pytest.mark.asyncio
async def test_stimulus_lifecycle(test_client: AsyncClient, test_item_for_stimulus: Item):
    """Stimulus 생명주기 테스트: 생성 → 조회 → 수정 → 삭제"""
    # 1. 생성
    create_response = await test_client.post(
        "/api/v1/stimuli",
        json={
            "item_id": str(test_item_for_stimulus.id),
            "kind": StimulusKind.READING.value,
            "title": "Initial Title",
            "content_text": "Initial content",
            "display_order": 1,
        },
    )
    assert create_response.status_code == 201
    stimulus_id = create_response.json()["id"]

    # 2. 조회
    get_response = await test_client.get(f"/api/v1/stimuli/{stimulus_id}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Initial Title"

    # 3. 수정
    update_response = await test_client.patch(
        f"/api/v1/stimuli/{stimulus_id}",
        json={"title": "Updated Title"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated Title"

    # 4. 삭제
    delete_response = await test_client.delete(f"/api/v1/stimuli/{stimulus_id}")
    assert delete_response.status_code == 204

    # 5. 삭제 확인
    final_get = await test_client.get(f"/api/v1/stimuli/{stimulus_id}")
    assert final_get.status_code == 404


@pytest.mark.asyncio
async def test_multiple_stimuli_per_item(
    test_client: AsyncClient, test_item_for_stimulus: Item, test_db: AsyncSession
):
    """하나의 Item에 여러 Stimulus 생성 가능 (Reading + Listening)"""
    # Reading stimulus
    reading_response = await test_client.post(
        "/api/v1/stimuli",
        json={
            "item_id": str(test_item_for_stimulus.id),
            "kind": StimulusKind.READING.value,
            "title": "Reading Passage",
            "content_text": "Reading content",
            "display_order": 1,
        },
    )
    assert reading_response.status_code == 201

    # Listening stimulus
    listening_response = await test_client.post(
        "/api/v1/stimuli",
        json={
            "item_id": str(test_item_for_stimulus.id),
            "kind": StimulusKind.AUDIO.value,
            "title": "Lecture Audio",
            "content_text": "Lecture transcript",
            "asset_url": "https://example.com/lecture.mp3",
            "duration_seconds": 120,
            "display_order": 2,
        },
    )
    assert listening_response.status_code == 201

    # 해당 Item의 Stimulus 목록 조회
    list_response = await test_client.get(f"/api/v1/stimuli?item_id={test_item_for_stimulus.id}")
    assert list_response.status_code == 200
    data = list_response.json()
    assert data["total"] >= 2  # 최소 2개 이상


@pytest.mark.asyncio
async def test_stimulus_kinds_variety(test_client: AsyncClient, test_item_for_stimulus: Item):
    """다양한 StimulusKind 테스트"""
    test_data = [
        {
            "kind": StimulusKind.READING,
            "title": "Reading Stimulus",
            "content_text": "Content for reading",
        },
        {
            "kind": StimulusKind.AUDIO,
            "title": "Audio Stimulus",
            "asset_url": "https://example.com/audio1.mp3",
            "duration_seconds": 120,
        },
        {
            "kind": StimulusKind.IMAGE,
            "title": "Image Stimulus",
            "asset_url": "https://example.com/image1.jpg",
        },
        {
            "kind": StimulusKind.DIRECTION,
            "title": "Direction Stimulus",
            "content_text": "Direction content",
        },
    ]

    for i, data in enumerate(test_data, start=1):
        payload = {
            "item_id": str(test_item_for_stimulus.id),
            "display_order": i,
            **data,
        }
        response = await test_client.post(
            "/api/v1/stimuli",
            json=payload,
        )
        assert response.status_code == 201
        assert response.json()["kind"] == data["kind"].value
