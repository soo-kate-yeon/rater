"""
Stimulus 관리 라우터.

자극자료(Stimulus) CRUD API를 제공합니다.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.item import Item
from src.models.stimulus import Stimulus
from src.schemas.stimulus import (
    StimulusCreate,
    StimulusListResponse,
    StimulusResponse,
    StimulusUpdate,
)

router = APIRouter()


@router.get("", response_model=StimulusListResponse)
async def list_stimuli(
    db: AsyncSession = Depends(get_db),
    item_id: str | None = Query(None, description="Item UUID 필터"),
) -> StimulusListResponse:
    """
    Stimulus 목록 조회

    Args:
        db: 데이터베이스 세션
        item_id: Item UUID 필터 (선택)

    Returns:
        Stimulus 목록
    """
    query = select(Stimulus)

    if item_id:
        try:
            item_uuid = uuid.UUID(item_id)
            query = query.where(Stimulus.item_id == item_uuid)
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid item_id format",
            ) from err

    query = query.order_by(Stimulus.item_id, Stimulus.display_order)
    result = await db.execute(query)
    stimuli = result.scalars().all()

    return StimulusListResponse(
        items=[StimulusResponse.model_validate(s) for s in stimuli],
        total=len(stimuli),
    )


@router.post("", response_model=StimulusResponse, status_code=status.HTTP_201_CREATED)
async def create_stimulus(
    stimulus_data: StimulusCreate,
    db: AsyncSession = Depends(get_db),
) -> StimulusResponse:
    """
    새로운 Stimulus 생성

    Args:
        stimulus_data: Stimulus 생성 정보
        db: 데이터베이스 세션

    Returns:
        생성된 Stimulus 정보

    Raises:
        HTTPException: Item을 찾을 수 없는 경우
    """
    # Item 존재 확인
    item_result = await db.execute(select(Item).where(Item.id == stimulus_data.item_id))
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id '{stimulus_data.item_id}' not found",
        )

    # Stimulus 생성
    new_stimulus = Stimulus(
        id=uuid.uuid4(),
        item_id=stimulus_data.item_id,
        kind=stimulus_data.kind,
        title=stimulus_data.title,
        content_text=stimulus_data.content_text,
        asset_url=stimulus_data.asset_url,
        duration_seconds=stimulus_data.duration_seconds,
        display_order=stimulus_data.display_order,
        notes_allowed=stimulus_data.notes_allowed,
    )
    db.add(new_stimulus)
    await db.commit()
    await db.refresh(new_stimulus)

    return StimulusResponse.model_validate(new_stimulus)


@router.get("/{stimulus_id}", response_model=StimulusResponse)
async def get_stimulus(
    stimulus_id: str,
    db: AsyncSession = Depends(get_db),
) -> StimulusResponse:
    """
    특정 Stimulus 조회

    Args:
        stimulus_id: Stimulus UUID
        db: 데이터베이스 세션

    Returns:
        Stimulus 정보

    Raises:
        HTTPException: Stimulus를 찾을 수 없는 경우 (404)
    """
    try:
        stimulus_uuid = uuid.UUID(stimulus_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid stimulus_id format",
        ) from err

    result = await db.execute(select(Stimulus).where(Stimulus.id == stimulus_uuid))
    stimulus = result.scalar_one_or_none()

    if not stimulus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stimulus not found",
        )

    return StimulusResponse.model_validate(stimulus)


@router.patch("/{stimulus_id}", response_model=StimulusResponse)
async def update_stimulus(
    stimulus_id: str,
    stimulus_data: StimulusUpdate,
    db: AsyncSession = Depends(get_db),
) -> StimulusResponse:
    """
    Stimulus 수정

    Args:
        stimulus_id: Stimulus UUID
        stimulus_data: 수정할 정보
        db: 데이터베이스 세션

    Returns:
        수정된 Stimulus 정보

    Raises:
        HTTPException: Stimulus를 찾을 수 없는 경우 (404)
    """
    try:
        stimulus_uuid = uuid.UUID(stimulus_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid stimulus_id format",
        ) from err

    result = await db.execute(select(Stimulus).where(Stimulus.id == stimulus_uuid))
    stimulus = result.scalar_one_or_none()

    if not stimulus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stimulus not found",
        )

    # 업데이트할 필드만 적용
    update_data = stimulus_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stimulus, field, value)

    await db.commit()
    await db.refresh(stimulus)

    return StimulusResponse.model_validate(stimulus)


@router.delete("/{stimulus_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stimulus(
    stimulus_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Stimulus 삭제

    Args:
        stimulus_id: Stimulus UUID
        db: 데이터베이스 세션

    Raises:
        HTTPException: Stimulus를 찾을 수 없는 경우 (404)
    """
    try:
        stimulus_uuid = uuid.UUID(stimulus_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid stimulus_id format",
        ) from err

    result = await db.execute(select(Stimulus).where(Stimulus.id == stimulus_uuid))
    stimulus = result.scalar_one_or_none()

    if not stimulus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stimulus not found",
        )

    await db.delete(stimulus)
    await db.commit()
