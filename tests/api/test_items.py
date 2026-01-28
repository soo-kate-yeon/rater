"""Item API 엔드포인트 테스트"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.item import Item
from src.models.set import Set
from src.models.task import TaskType


@pytest.fixture
async def api_test_set(test_db: AsyncSession) -> Set:
    """테스트용 Set"""
    new_set = Set(
        id=uuid.uuid4(),
        title="API Test Set",
        source="Test",
        version="v1.0",
    )
    test_db.add(new_set)
    await test_db.commit()
    await test_db.refresh(new_set)
    return new_set


@pytest.fixture
async def api_test_item(test_db: AsyncSession, api_test_set: Set) -> Item:
    """테스트용 Item"""
    item = Item(
        id=uuid.uuid4(),
        set_id=api_test_set.id,
        task_no=1,
        task_type=TaskType.INDEPENDENT,
        prompt="Test prompt",
        topic_type="preference",
        topic_category="education",
    )
    test_db.add(item)
    await test_db.commit()
    await test_db.refresh(item)
    return item


# === POST /v1/items ===


@pytest.mark.asyncio
async def test_create_independent_item(test_client: AsyncClient, api_test_set: Set):
    """Independent Item 생성"""
    response = await test_client.post(
        "/v1/items",
        json={
            "set_id": str(api_test_set.id),
            "task_no": 1,
            "task_type": "INDEPENDENT",
            "prompt": "Do you agree or disagree?",
            "prep_seconds": 15,
            "response_seconds": 45,
            "topic_type": "agree_disagree",
            "topic_category": "education",
            "difficulty": "medium",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["task_type"] == "INDEPENDENT"
    assert data["topic_type"] == "agree_disagree"
    assert data["topic_category"] == "education"


@pytest.mark.asyncio
async def test_create_integrated_item(test_client: AsyncClient, api_test_set: Set):
    """Integrated Item 생성"""
    response = await test_client.post(
        "/v1/items",
        json={
            "set_id": str(api_test_set.id),
            "task_no": 3,
            "task_type": "INTEGRATED",
            "prompt": "Summarize the lecture.",
            "prep_seconds": 30,
            "response_seconds": 60,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["task_type"] == "INTEGRATED"
    assert data["topic_type"] is None


@pytest.mark.asyncio
async def test_create_independent_item_missing_topic_type(test_client: AsyncClient, api_test_set: Set):
    """Independent Item 생성 시 topic_type 누락 - 422 오류"""
    response = await test_client.post(
        "/v1/items",
        json={
            "set_id": str(api_test_set.id),
            "task_no": 1,
            "task_type": "INDEPENDENT",
            "prompt": "Test",
            # topic_type 누락
            "topic_category": "education",
        },
    )
    assert response.status_code == 422
    assert "topic_type" in str(response.json())


@pytest.mark.asyncio
async def test_create_item_duplicate_task_no(test_client: AsyncClient, api_test_set: Set, api_test_item: Item):
    """중복 task_no로 Item 생성 시 409 오류"""
    response = await test_client.post(
        "/v1/items",
        json={
            "set_id": str(api_test_set.id),
            "task_no": api_test_item.task_no,  # 중복
            "task_type": "INDEPENDENT",
            "prompt": "Another prompt",
            "topic_type": "preference",
            "topic_category": "technology",
        },
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_item_set_not_found(test_client: AsyncClient):
    """존재하지 않는 Set에 Item 생성 시 404"""
    fake_set_id = str(uuid.uuid4())
    response = await test_client.post(
        "/v1/items",
        json={
            "set_id": fake_set_id,
            "task_no": 1,
            "task_type": "INDEPENDENT",
            "prompt": "Test",
            "topic_type": "preference",
            "topic_category": "education",
        },
    )
    assert response.status_code == 404


# === GET /v1/items ===


@pytest.mark.asyncio
async def test_list_items(test_client: AsyncClient, api_test_item: Item):
    """Item 목록 조회"""
    response = await test_client.get("/v1/items")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_items_filter_by_set(test_client: AsyncClient, api_test_set: Set, api_test_item: Item):
    """Set별 Item 목록 조회"""
    response = await test_client.get(f"/v1/items?set_id={api_test_set.id}")
    assert response.status_code == 200
    data = response.json()
    assert all(item["set_id"] == str(api_test_set.id) for item in data["items"])


@pytest.mark.asyncio
async def test_list_items_filter_by_task_type(test_client: AsyncClient, api_test_item: Item):
    """task_type별 Item 목록 조회"""
    response = await test_client.get("/v1/items?task_type=INDEPENDENT")
    assert response.status_code == 200
    data = response.json()
    assert all(item["task_type"] == "INDEPENDENT" for item in data["items"])


# === GET /v1/items/{item_id} ===


@pytest.mark.asyncio
async def test_get_item(test_client: AsyncClient, api_test_item: Item):
    """단일 Item 조회"""
    response = await test_client.get(f"/v1/items/{api_test_item.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(api_test_item.id)
    assert data["prompt"] == api_test_item.prompt


@pytest.mark.asyncio
async def test_get_item_not_found(test_client: AsyncClient):
    """존재하지 않는 Item 조회 시 404"""
    fake_id = str(uuid.uuid4())
    response = await test_client.get(f"/v1/items/{fake_id}")
    assert response.status_code == 404


# === PATCH /v1/items/{item_id} ===


@pytest.mark.asyncio
async def test_update_item(test_client: AsyncClient, api_test_item: Item):
    """Item 수정"""
    response = await test_client.patch(
        f"/v1/items/{api_test_item.id}",
        json={
            "prompt": "Updated prompt",
            "difficulty": "hard",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["prompt"] == "Updated prompt"
    assert data["difficulty"] == "hard"


# === DELETE /v1/items/{item_id} ===


@pytest.mark.asyncio
async def test_delete_item(test_client: AsyncClient, api_test_item: Item):
    """Item 삭제"""
    response = await test_client.delete(f"/v1/items/{api_test_item.id}")
    assert response.status_code == 204

    # 삭제 확인
    get_response = await test_client.get(f"/v1/items/{api_test_item.id}")
    assert get_response.status_code == 404


# === GET /v1/items/{item_id}/with-relations ===


@pytest.mark.asyncio
async def test_get_item_with_relations(test_client: AsyncClient, api_test_item: Item):
    """Item과 관련 데이터 함께 조회"""
    response = await test_client.get(f"/v1/items/{api_test_item.id}/with-relations")
    assert response.status_code == 200
    data = response.json()
    assert "item" in data
    assert "stimuli" in data
    assert "answer_keys" in data
    assert data["item"]["id"] == str(api_test_item.id)
