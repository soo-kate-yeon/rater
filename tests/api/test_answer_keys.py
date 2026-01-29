"""AnswerKey API 엔드포인트 테스트"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.answer_key import AnswerKey
from src.models.enums import AnswerKeyType, AnswerKeyLevel
from src.models.item import Item
from src.models.set import Set
from src.models.task import TaskType


@pytest_asyncio.fixture
async def test_set_for_answer_key(test_db: AsyncSession) -> Set:
    """테스트용 Set"""
    new_set = Set(
        id=uuid.uuid4(),
        title="Answer Key Test Set",
        source="Test",
        version="v1.0",
    )
    test_db.add(new_set)
    await test_db.commit()
    await test_db.refresh(new_set)
    return new_set


@pytest_asyncio.fixture
async def test_item_for_answer_key(test_db: AsyncSession, test_set_for_answer_key: Set) -> Item:
    """테스트용 Item"""
    item = Item(
        id=uuid.uuid4(),
        set_id=test_set_for_answer_key.id,
        task_no=1,
        task_type=TaskType.INTEGRATED,
        prompt="Summarize the lecture.",
        topic_type=None,
        topic_category=None,
    )
    test_db.add(item)
    await test_db.commit()
    await test_db.refresh(item)
    return item


@pytest_asyncio.fixture
async def test_answer_key(test_db: AsyncSession, test_item_for_answer_key: Item) -> AnswerKey:
    """테스트용 AnswerKey"""
    answer_key = AnswerKey(
        id=uuid.uuid4(),
        item_id=test_item_for_answer_key.id,
        answer_type=AnswerKeyType.SAMPLE_RESPONSE,
        level=AnswerKeyLevel.HIGH,
        content={"text": "This is a high-level sample answer for the integrated task."},
        source="official",
    )
    test_db.add(answer_key)
    await test_db.commit()
    await test_db.refresh(answer_key)
    return answer_key


# ============================================================================
# GET /api/v1/answer-keys - 목록 조회
# ============================================================================


@pytest.mark.asyncio
async def test_list_answer_keys_success(test_client: AsyncClient, test_answer_key: AnswerKey):
    """AnswerKey 목록 조회 성공"""
    response = await test_client.get("/api/v1/answer-keys")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_answer_keys_filter_by_item_id(
    test_client: AsyncClient, test_item_for_answer_key: Item, test_answer_key: AnswerKey
):
    """item_id 필터로 AnswerKey 목록 조회"""
    response = await test_client.get(f"/api/v1/answer-keys?item_id={test_item_for_answer_key.id}")

    assert response.status_code == 200
    data = response.json()
    assert all(item["item_id"] == str(test_item_for_answer_key.id) for item in data["items"])


@pytest.mark.asyncio
async def test_list_answer_keys_filter_by_answer_type(test_client: AsyncClient, test_answer_key: AnswerKey):
    """answer_type 필터로 AnswerKey 목록 조회"""
    response = await test_client.get(f"/api/v1/answer-keys?answer_type={AnswerKeyType.SAMPLE_RESPONSE.value}")

    assert response.status_code == 200
    data = response.json()
    assert all(item["answer_type"] == AnswerKeyType.SAMPLE_RESPONSE.value for item in data["items"])


@pytest.mark.asyncio
async def test_list_answer_keys_invalid_item_id(test_client: AsyncClient):
    """잘못된 item_id 형식으로 목록 조회 시 400 에러"""
    response = await test_client.get("/api/v1/answer-keys?item_id=invalid-uuid")

    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


# ============================================================================
# POST /api/v1/answer-keys - 생성
# ============================================================================


@pytest.mark.asyncio
async def test_create_answer_key_success(test_client: AsyncClient, test_item_for_answer_key: Item):
    """AnswerKey 생성 성공"""
    response = await test_client.post(
        "/api/v1/answer-keys",
        json={
            "item_id": str(test_item_for_answer_key.id),
            "answer_type": AnswerKeyType.SAMPLE_RESPONSE.value,
            "level": AnswerKeyLevel.MID.value,
            "content": {"text": "This is a medium-level sample answer."},
            "source": "custom",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["item_id"] == str(test_item_for_answer_key.id)
    assert data["answer_type"] == AnswerKeyType.SAMPLE_RESPONSE.value
    assert data["level"] == AnswerKeyLevel.MID.value
    assert data["content"]["text"] == "This is a medium-level sample answer."


@pytest.mark.asyncio
async def test_create_answer_key_item_not_found(test_client: AsyncClient):
    """존재하지 않는 Item으로 AnswerKey 생성 시 404 에러"""
    fake_item_id = str(uuid.uuid4())
    response = await test_client.post(
        "/api/v1/answer-keys",
        json={
            "item_id": fake_item_id,
            "answer_type": AnswerKeyType.SAMPLE_RESPONSE.value,
            "level": AnswerKeyLevel.HIGH.value,
            "content": {"text": "Test content"},
            "source": "test",
        },
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_answer_key_missing_fields(test_client: AsyncClient):
    """필수 필드 누락 시 422 에러"""
    response = await test_client.post(
        "/api/v1/answer-keys",
        json={
            "item_id": str(uuid.uuid4()),
            # answer_type, content 누락
        },
    )

    assert response.status_code == 422


# ============================================================================
# POST /api/v1/answer-keys/blueprint - Blueprint 생성
# ============================================================================


@pytest.mark.asyncio
async def test_create_blueprint_answer_key_success(test_client: AsyncClient, test_item_for_answer_key: Item):
    """Blueprint AnswerKey 생성 성공"""
    info_units = [
        {
            "source": "reading",
            "label": "Main Point",
            "content": "Main point about topic",
            "importance": "essential",
        },
        {
            "source": "listening",
            "label": "Supporting Detail",
            "content": "Supporting detail",
            "importance": "supporting",
        },
    ]

    response = await test_client.post(
        "/api/v1/answer-keys/blueprint",
        json={
            "item_id": str(test_item_for_answer_key.id),
            "level": AnswerKeyLevel.HIGH.value,
            "blueprint": {
                "blueprint_type": "integrated",
                "data": {
                    "info_units": info_units,
                    "recommended_order": ["Main Point", "Supporting Detail"],
                },
            },
            "source": "official",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["item_id"] == str(test_item_for_answer_key.id)
    assert data["answer_type"] == AnswerKeyType.BLUEPRINT.value


@pytest.mark.asyncio
async def test_create_blueprint_answer_key_item_not_found(test_client: AsyncClient):
    """존재하지 않는 Item으로 Blueprint 생성 시 404 에러"""
    fake_item_id = str(uuid.uuid4())
    response = await test_client.post(
        "/api/v1/answer-keys/blueprint",
        json={
            "item_id": fake_item_id,
            "level": AnswerKeyLevel.HIGH.value,
            "blueprint": {
                "blueprint_type": "integrated",
                "data": {
                    "info_units": [],
                    "recommended_order": [],
                },
            },
            "source": "test",
        },
    )

    assert response.status_code == 404


# ============================================================================
# GET /api/v1/answer-keys/{answer_key_id} - 단일 조회
# ============================================================================


@pytest.mark.asyncio
async def test_get_answer_key_success(test_client: AsyncClient, test_answer_key: AnswerKey):
    """AnswerKey 단일 조회 성공"""
    response = await test_client.get(f"/api/v1/answer-keys/{test_answer_key.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_answer_key.id)
    assert data["content"] == test_answer_key.content


@pytest.mark.asyncio
async def test_get_answer_key_not_found(test_client: AsyncClient):
    """존재하지 않는 AnswerKey 조회 시 404 에러"""
    fake_id = str(uuid.uuid4())
    response = await test_client.get(f"/api/v1/answer-keys/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_answer_key_invalid_uuid(test_client: AsyncClient):
    """잘못된 UUID 형식으로 조회 시 400 에러"""
    response = await test_client.get("/api/v1/answer-keys/invalid-uuid")

    assert response.status_code == 400


# ============================================================================
# PATCH /api/v1/answer-keys/{answer_key_id} - 수정
# ============================================================================


@pytest.mark.asyncio
async def test_update_answer_key_success(test_client: AsyncClient, test_answer_key: AnswerKey):
    """AnswerKey 수정 성공"""
    response = await test_client.patch(
        f"/api/v1/answer-keys/{test_answer_key.id}",
        json={
            "content": {"text": "Updated answer content"},
            "level": AnswerKeyLevel.LOW.value,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["content"]["text"] == "Updated answer content"
    assert data["level"] == AnswerKeyLevel.LOW.value


@pytest.mark.asyncio
async def test_update_answer_key_partial(test_client: AsyncClient, test_answer_key: AnswerKey):
    """AnswerKey 일부 필드만 수정"""
    original_content = test_answer_key.content
    response = await test_client.patch(
        f"/api/v1/answer-keys/{test_answer_key.id}",
        json={
            "source": "updated_source",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "updated_source"
    assert data["content"] == original_content  # content는 변경되지 않음


@pytest.mark.asyncio
async def test_update_answer_key_not_found(test_client: AsyncClient):
    """존재하지 않는 AnswerKey 수정 시 404 에러"""
    fake_id = str(uuid.uuid4())
    response = await test_client.patch(
        f"/api/v1/answer-keys/{fake_id}",
        json={"content": {"text": "Updated content"}},
    )

    assert response.status_code == 404


# ============================================================================
# DELETE /api/v1/answer-keys/{answer_key_id} - 삭제
# ============================================================================


@pytest.mark.asyncio
async def test_delete_answer_key_success(test_client: AsyncClient, test_answer_key: AnswerKey):
    """AnswerKey 삭제 성공"""
    response = await test_client.delete(f"/api/v1/answer-keys/{test_answer_key.id}")

    assert response.status_code == 204

    # 삭제 확인
    get_response = await test_client.get(f"/api/v1/answer-keys/{test_answer_key.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_answer_key_not_found(test_client: AsyncClient):
    """존재하지 않는 AnswerKey 삭제 시 404 에러"""
    fake_id = str(uuid.uuid4())
    response = await test_client.delete(f"/api/v1/answer-keys/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_answer_key_invalid_uuid(test_client: AsyncClient):
    """잘못된 UUID 형식으로 삭제 시 400 에러"""
    response = await test_client.delete("/api/v1/answer-keys/invalid-uuid")

    assert response.status_code == 400


# ============================================================================
# 복합 시나리오 테스트
# ============================================================================


@pytest.mark.asyncio
async def test_answer_key_lifecycle(test_client: AsyncClient, test_item_for_answer_key: Item):
    """AnswerKey 생명주기 테스트: 생성 → 조회 → 수정 → 삭제"""
    # 1. 생성
    create_response = await test_client.post(
        "/api/v1/answer-keys",
        json={
            "item_id": str(test_item_for_answer_key.id),
            "answer_type": AnswerKeyType.SAMPLE_RESPONSE.value,
            "level": AnswerKeyLevel.HIGH.value,
            "content": {"text": "Initial content"},
            "source": "test",
        },
    )
    assert create_response.status_code == 201
    answer_key_id = create_response.json()["id"]

    # 2. 조회
    get_response = await test_client.get(f"/api/v1/answer-keys/{answer_key_id}")
    assert get_response.status_code == 200
    assert get_response.json()["content"]["text"] == "Initial content"

    # 3. 수정
    update_response = await test_client.patch(
        f"/api/v1/answer-keys/{answer_key_id}",
        json={"content": {"text": "Updated content"}},
    )
    assert update_response.status_code == 200
    assert update_response.json()["content"]["text"] == "Updated content"

    # 4. 삭제
    delete_response = await test_client.delete(f"/api/v1/answer-keys/{answer_key_id}")
    assert delete_response.status_code == 204

    # 5. 삭제 확인
    final_get = await test_client.get(f"/api/v1/answer-keys/{answer_key_id}")
    assert final_get.status_code == 404


@pytest.mark.asyncio
async def test_multiple_answer_keys_per_item(
    test_client: AsyncClient, test_item_for_answer_key: Item, test_db: AsyncSession
):
    """하나의 Item에 여러 AnswerKey 생성 가능"""
    # HIGH, MEDIUM, LOW 레벨의 샘플 답변 생성
    for level in [AnswerKeyLevel.HIGH, AnswerKeyLevel.MID, AnswerKeyLevel.LOW]:
        response = await test_client.post(
            "/api/v1/answer-keys",
            json={
                "item_id": str(test_item_for_answer_key.id),
                "answer_type": AnswerKeyType.SAMPLE_RESPONSE.value,
                "level": level.value,
                "content": {"text": f"Sample answer for {level.value} level"},
                "source": "test",
            },
        )
        assert response.status_code == 201

    # 해당 Item의 AnswerKey 목록 조회
    list_response = await test_client.get(f"/api/v1/answer-keys?item_id={test_item_for_answer_key.id}")
    assert list_response.status_code == 200
    data = list_response.json()
    assert data["total"] >= 3  # 최소 3개 이상
