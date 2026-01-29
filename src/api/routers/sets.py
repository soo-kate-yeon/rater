"""
Set 관리 라우터.

문제 세트(Set) CRUD API를 제공합니다.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.set import Set
from src.schemas.set import (
    SetCreate,
    SetListResponse,
    SetResponse,
    SetUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=SetListResponse)
async def list_sets(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(100, ge=1, le=500, description="조회 개수"),
    source: str | None = Query(None, description="출처 필터"),
) -> SetListResponse:
    """
    Set 목록 조회

    Args:
        db: 데이터베이스 세션
        skip: 건너뛸 개수
        limit: 최대 조회 개수
        source: 출처 필터 (선택)

    Returns:
        Set 목록 및 페이징 정보
    """
    # 기본 쿼리
    query = select(Set)

    # 필터 적용
    if source:
        query = query.where(Set.source == source)

    # 전체 개수 조회
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 페이징 적용
    query = query.offset(skip).limit(limit).order_by(Set.created_at.desc())
    result = await db.execute(query)
    sets = result.scalars().all()

    # 응답 생성
    set_responses = []
    for s in sets:
        set_responses.append(
            SetResponse(
                id=s.id,
                title=s.title,
                source=s.source,
                version=s.version,
                description=s.description,
                created_at=s.created_at,
                updated_at=s.updated_at,
                item_count=len(s.items) if s.items else 0,
            )
        )

    return SetListResponse(
        items=set_responses,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=SetResponse, status_code=status.HTTP_201_CREATED)
async def create_set(
    set_data: SetCreate,
    db: AsyncSession = Depends(get_db),
) -> SetResponse:
    """
    새로운 Set 생성

    Args:
        set_data: Set 생성 정보
        db: 데이터베이스 세션

    Returns:
        생성된 Set 정보
    """
    # 중복 검사 (source + version)
    existing_query = select(Set).where(
        Set.source == set_data.source,
        Set.version == set_data.version,
    )
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Set with source='{set_data.source}' and version='{set_data.version}' already exists",
        )

    # 높은 버전 경고 (REQ-SCHEMA-004)
    version_check_query = select(Set).where(
        Set.source == set_data.source,
        Set.version > set_data.version,
    )
    version_result = await db.execute(version_check_query)
    if version_result.scalar_one_or_none():
        logger.warning(
            f"Creating Set with lower version: source='{set_data.source}', version='{set_data.version}'. "
            "Higher version already exists."
        )

    # Set 생성
    new_set = Set(
        id=uuid.uuid4(),
        title=set_data.title,
        source=set_data.source,
        version=set_data.version,
        description=set_data.description,
    )
    db.add(new_set)
    await db.commit()
    await db.refresh(new_set)

    return SetResponse(
        id=new_set.id,
        title=new_set.title,
        source=new_set.source,
        version=new_set.version,
        description=new_set.description,
        created_at=new_set.created_at,
        updated_at=new_set.updated_at,
        item_count=0,
    )


@router.get("/{set_id}", response_model=SetResponse)
async def get_set(
    set_id: str,
    db: AsyncSession = Depends(get_db),
) -> SetResponse:
    """
    특정 Set 조회

    Args:
        set_id: Set UUID
        db: 데이터베이스 세션

    Returns:
        Set 정보

    Raises:
        HTTPException: Set을 찾을 수 없는 경우 (404)
    """
    try:
        set_uuid = uuid.UUID(set_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid set_id format",
        )

    result = await db.execute(select(Set).where(Set.id == set_uuid))
    set_obj = result.scalar_one_or_none()

    if not set_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Set not found",
        )

    return SetResponse(
        id=set_obj.id,
        title=set_obj.title,
        source=set_obj.source,
        version=set_obj.version,
        description=set_obj.description,
        created_at=set_obj.created_at,
        updated_at=set_obj.updated_at,
        item_count=len(set_obj.items) if set_obj.items else 0,
    )


@router.patch("/{set_id}", response_model=SetResponse)
async def update_set(
    set_id: str,
    set_data: SetUpdate,
    db: AsyncSession = Depends(get_db),
) -> SetResponse:
    """
    Set 수정

    Args:
        set_id: Set UUID
        set_data: 수정할 정보
        db: 데이터베이스 세션

    Returns:
        수정된 Set 정보

    Raises:
        HTTPException: Set을 찾을 수 없는 경우 (404)
    """
    try:
        set_uuid = uuid.UUID(set_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid set_id format",
        )

    result = await db.execute(select(Set).where(Set.id == set_uuid))
    set_obj = result.scalar_one_or_none()

    if not set_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Set not found",
        )

    # 업데이트할 필드만 적용
    update_data = set_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(set_obj, field, value)

    await db.commit()
    await db.refresh(set_obj)

    return SetResponse(
        id=set_obj.id,
        title=set_obj.title,
        source=set_obj.source,
        version=set_obj.version,
        description=set_obj.description,
        created_at=set_obj.created_at,
        updated_at=set_obj.updated_at,
        item_count=len(set_obj.items) if set_obj.items else 0,
    )


@router.delete("/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_set(
    set_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Set 삭제

    Set 삭제 시 연결된 모든 Item, Stimulus, AnswerKey도 함께 삭제됩니다 (CASCADE).

    Args:
        set_id: Set UUID
        db: 데이터베이스 세션

    Raises:
        HTTPException: Set을 찾을 수 없는 경우 (404)
    """
    try:
        set_uuid = uuid.UUID(set_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid set_id format",
        )

    result = await db.execute(select(Set).where(Set.id == set_uuid))
    set_obj = result.scalar_one_or_none()

    if not set_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Set not found",
        )

    await db.delete(set_obj)
    await db.commit()
