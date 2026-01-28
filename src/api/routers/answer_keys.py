"""
AnswerKey 관리 라우터.

모범답안(AnswerKey) CRUD API를 제공합니다.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.answer_key import AnswerKey
from src.models.enums import AnswerKeyType
from src.models.item import Item
from src.schemas.answer_key import (
    AnswerKeyCreate,
    AnswerKeyCreateWithBlueprint,
    AnswerKeyListResponse,
    AnswerKeyResponse,
    AnswerKeyUpdate,
)

router = APIRouter()


@router.get("", response_model=AnswerKeyListResponse)
async def list_answer_keys(
    db: AsyncSession = Depends(get_db),
    item_id: Optional[str] = Query(None, description="Item UUID 필터"),
    answer_type: Optional[AnswerKeyType] = Query(None, description="유형 필터"),
) -> AnswerKeyListResponse:
    """
    AnswerKey 목록 조회

    Args:
        db: 데이터베이스 세션
        item_id: Item UUID 필터 (선택)
        answer_type: 유형 필터 (선택)

    Returns:
        AnswerKey 목록
    """
    query = select(AnswerKey)

    if item_id:
        try:
            item_uuid = uuid.UUID(item_id)
            query = query.where(AnswerKey.item_id == item_uuid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid item_id format",
            )

    if answer_type:
        query = query.where(AnswerKey.answer_type == answer_type)

    query = query.order_by(AnswerKey.item_id, AnswerKey.answer_type)
    result = await db.execute(query)
    answer_keys = result.scalars().all()

    return AnswerKeyListResponse(
        items=[AnswerKeyResponse.model_validate(ak) for ak in answer_keys],
        total=len(answer_keys),
    )


@router.post("", response_model=AnswerKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_answer_key(
    answer_key_data: AnswerKeyCreate,
    db: AsyncSession = Depends(get_db),
) -> AnswerKeyResponse:
    """
    새로운 AnswerKey 생성

    Args:
        answer_key_data: AnswerKey 생성 정보
        db: 데이터베이스 세션

    Returns:
        생성된 AnswerKey 정보

    Raises:
        HTTPException: Item을 찾을 수 없는 경우
    """
    # Item 존재 확인
    item_result = await db.execute(select(Item).where(Item.id == answer_key_data.item_id))
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id '{answer_key_data.item_id}' not found",
        )

    # AnswerKey 생성
    new_answer_key = AnswerKey(
        id=uuid.uuid4(),
        item_id=answer_key_data.item_id,
        answer_type=answer_key_data.answer_type,
        level=answer_key_data.level,
        content=answer_key_data.content,
        source=answer_key_data.source,
    )
    db.add(new_answer_key)
    await db.commit()
    await db.refresh(new_answer_key)

    return AnswerKeyResponse.model_validate(new_answer_key)


@router.post("/blueprint", response_model=AnswerKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_blueprint_answer_key(
    blueprint_data: AnswerKeyCreateWithBlueprint,
    db: AsyncSession = Depends(get_db),
) -> AnswerKeyResponse:
    """
    Blueprint 유형의 AnswerKey 생성

    Blueprint 스키마 검증을 포함한 AnswerKey를 생성합니다.

    Args:
        blueprint_data: Blueprint AnswerKey 생성 정보
        db: 데이터베이스 세션

    Returns:
        생성된 AnswerKey 정보

    Raises:
        HTTPException: Item을 찾을 수 없거나 Blueprint 검증 실패
    """
    # Item 존재 확인
    item_result = await db.execute(select(Item).where(Item.id == blueprint_data.item_id))
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id '{blueprint_data.item_id}' not found",
        )

    # AnswerKeyCreate로 변환 후 생성
    answer_key_data = blueprint_data.to_answer_key_create()

    new_answer_key = AnswerKey(
        id=uuid.uuid4(),
        item_id=answer_key_data.item_id,
        answer_type=answer_key_data.answer_type,
        level=answer_key_data.level,
        content=answer_key_data.content,
        source=answer_key_data.source,
    )
    db.add(new_answer_key)
    await db.commit()
    await db.refresh(new_answer_key)

    return AnswerKeyResponse.model_validate(new_answer_key)


@router.get("/{answer_key_id}", response_model=AnswerKeyResponse)
async def get_answer_key(
    answer_key_id: str,
    db: AsyncSession = Depends(get_db),
) -> AnswerKeyResponse:
    """
    특정 AnswerKey 조회

    Args:
        answer_key_id: AnswerKey UUID
        db: 데이터베이스 세션

    Returns:
        AnswerKey 정보

    Raises:
        HTTPException: AnswerKey를 찾을 수 없는 경우 (404)
    """
    try:
        answer_key_uuid = uuid.UUID(answer_key_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid answer_key_id format",
        )

    result = await db.execute(select(AnswerKey).where(AnswerKey.id == answer_key_uuid))
    answer_key = result.scalar_one_or_none()

    if not answer_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AnswerKey not found",
        )

    return AnswerKeyResponse.model_validate(answer_key)


@router.patch("/{answer_key_id}", response_model=AnswerKeyResponse)
async def update_answer_key(
    answer_key_id: str,
    answer_key_data: AnswerKeyUpdate,
    db: AsyncSession = Depends(get_db),
) -> AnswerKeyResponse:
    """
    AnswerKey 수정

    Args:
        answer_key_id: AnswerKey UUID
        answer_key_data: 수정할 정보
        db: 데이터베이스 세션

    Returns:
        수정된 AnswerKey 정보

    Raises:
        HTTPException: AnswerKey를 찾을 수 없는 경우 (404)
    """
    try:
        answer_key_uuid = uuid.UUID(answer_key_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid answer_key_id format",
        )

    result = await db.execute(select(AnswerKey).where(AnswerKey.id == answer_key_uuid))
    answer_key = result.scalar_one_or_none()

    if not answer_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AnswerKey not found",
        )

    # 업데이트할 필드만 적용
    update_data = answer_key_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(answer_key, field, value)

    await db.commit()
    await db.refresh(answer_key)

    return AnswerKeyResponse.model_validate(answer_key)


@router.delete("/{answer_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_answer_key(
    answer_key_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    AnswerKey 삭제

    Args:
        answer_key_id: AnswerKey UUID
        db: 데이터베이스 세션

    Raises:
        HTTPException: AnswerKey를 찾을 수 없는 경우 (404)
    """
    try:
        answer_key_uuid = uuid.UUID(answer_key_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid answer_key_id format",
        )

    result = await db.execute(select(AnswerKey).where(AnswerKey.id == answer_key_uuid))
    answer_key = result.scalar_one_or_none()

    if not answer_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AnswerKey not found",
        )

    await db.delete(answer_key)
    await db.commit()
