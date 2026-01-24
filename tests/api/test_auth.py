"""인증 API 테스트"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_register_success(test_client: AsyncClient, test_db: AsyncSession):
    """회원가입 성공 테스트"""
    # 회원가입 요청
    response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepassword123",
            "name": "New User",
        },
    )

    # 검증
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["name"] == "New User"
    assert "id" in data
    assert "password" not in data  # 비밀번호는 응답에 포함되지 않아야 함


@pytest.mark.asyncio
async def test_register_duplicate_email(test_client: AsyncClient, test_db: AsyncSession):
    """중복 이메일로 회원가입 실패 테스트"""
    # 첫 번째 회원가입
    await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
            "name": "First User",
        },
    )

    # 동일한 이메일로 두 번째 회원가입 시도
    response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "differentpassword",
            "name": "Second User",
        },
    )

    # 검증
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_invalid_email(test_client: AsyncClient):
    """잘못된 이메일 형식으로 회원가입 실패 테스트"""
    response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "invalid-email",
            "password": "password123",
            "name": "Test User",
        },
    )

    # 검증 (Pydantic 검증 실패)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(test_client: AsyncClient, test_user):
    """로그인 성공 테스트"""
    response = await test_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )

    # 검증
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


@pytest.mark.asyncio
async def test_login_wrong_password(test_client: AsyncClient, test_user):
    """잘못된 비밀번호로 로그인 실패 테스트"""
    response = await test_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
    )

    # 검증
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(test_client: AsyncClient):
    """존재하지 않는 사용자로 로그인 실패 테스트"""
    response = await test_client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "password123",
        },
    )

    # 검증
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_missing_fields(test_client: AsyncClient):
    """필수 필드 누락 시 회원가입 실패 테스트"""
    response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "incomplete@example.com",
            # password와 name 누락
        },
    )

    # 검증
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_missing_fields(test_client: AsyncClient):
    """필수 필드 누락 시 로그인 실패 테스트"""
    response = await test_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            # password 누락
        },
    )

    # 검증
    assert response.status_code == 422
