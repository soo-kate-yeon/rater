"""Set API 엔드포인트 테스트"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.set import Set


@pytest.fixture
async def test_set_fixture(test_db: AsyncSession) -> Set:
    """테스트용 Set 생성"""
    new_set = Set(
        id=uuid.uuid4(),
        title="ETS Practice Test 1",
        source="ETS Official",
        version="v1.0",
        description="공식 연습 문제",
    )
    test_db.add(new_set)
    await test_db.commit()
    await test_db.refresh(new_set)
    return new_set


# === POST /v1/sets ===


@pytest.mark.asyncio
async def test_create_set(test_client: AsyncClient):
    """Set 생성 테스트"""
    response = await test_client.post(
        "/v1/sets",
        json={
            "title": "New Practice Set",
            "source": "Kaplan",
            "version": "v2.0",
            "description": "Kaplan 연습 문제",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Practice Set"
    assert data["source"] == "Kaplan"
    assert data["version"] == "v2.0"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_set_duplicate(test_client: AsyncClient, test_set_fixture: Set):
    """중복 Set 생성 시 409 오류"""
    response = await test_client.post(
        "/v1/sets",
        json={
            "title": "Another Title",
            "source": test_set_fixture.source,  # 동일 source
            "version": test_set_fixture.version,  # 동일 version
        },
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_set_missing_required_field(test_client: AsyncClient):
    """필수 필드 누락 시 422 오류"""
    response = await test_client.post(
        "/v1/sets",
        json={
            "title": "Test",
            # source 누락
            "version": "v1.0",
        },
    )
    assert response.status_code == 422


# === GET /v1/sets ===


@pytest.mark.asyncio
async def test_list_sets(test_client: AsyncClient, test_set_fixture: Set):
    """Set 목록 조회 테스트"""
    response = await test_client.get("/v1/sets")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_sets_with_filter(test_client: AsyncClient, test_set_fixture: Set):
    """Set 목록 필터 조회"""
    response = await test_client.get(f"/v1/sets?source={test_set_fixture.source}")
    assert response.status_code == 200
    data = response.json()
    assert all(item["source"] == test_set_fixture.source for item in data["items"])


@pytest.mark.asyncio
async def test_list_sets_pagination(test_client: AsyncClient):
    """Set 목록 페이징"""
    response = await test_client.get("/v1/sets?skip=0&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == 0
    assert data["limit"] == 5


# === GET /v1/sets/{set_id} ===


@pytest.mark.asyncio
async def test_get_set(test_client: AsyncClient, test_set_fixture: Set):
    """단일 Set 조회"""
    response = await test_client.get(f"/v1/sets/{test_set_fixture.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_set_fixture.id)
    assert data["title"] == test_set_fixture.title


@pytest.mark.asyncio
async def test_get_set_not_found(test_client: AsyncClient):
    """존재하지 않는 Set 조회 시 404"""
    fake_id = str(uuid.uuid4())
    response = await test_client.get(f"/v1/sets/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_set_invalid_uuid(test_client: AsyncClient):
    """잘못된 UUID 형식 시 400"""
    response = await test_client.get("/v1/sets/invalid-uuid")
    assert response.status_code == 400
    assert "Invalid set_id format" in response.json()["detail"]


# === PATCH /v1/sets/{set_id} ===


@pytest.mark.asyncio
async def test_update_set(test_client: AsyncClient, test_set_fixture: Set):
    """Set 수정"""
    response = await test_client.patch(
        f"/v1/sets/{test_set_fixture.id}",
        json={"title": "Updated Title", "description": "Updated description"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated description"
    # 변경하지 않은 필드는 유지
    assert data["source"] == test_set_fixture.source


@pytest.mark.asyncio
async def test_update_set_not_found(test_client: AsyncClient):
    """존재하지 않는 Set 수정 시 404"""
    fake_id = str(uuid.uuid4())
    response = await test_client.patch(f"/v1/sets/{fake_id}", json={"title": "New"})
    assert response.status_code == 404


# === DELETE /v1/sets/{set_id} ===


@pytest.mark.asyncio
async def test_delete_set(test_client: AsyncClient, test_set_fixture: Set):
    """Set 삭제"""
    response = await test_client.delete(f"/v1/sets/{test_set_fixture.id}")
    assert response.status_code == 204

    # 삭제 확인
    get_response = await test_client.get(f"/v1/sets/{test_set_fixture.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_set_not_found(test_client: AsyncClient):
    """존재하지 않는 Set 삭제 시 404"""
    fake_id = str(uuid.uuid4())
    response = await test_client.delete(f"/v1/sets/{fake_id}")
    assert response.status_code == 404
