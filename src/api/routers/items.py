"""
Item 관리 라우터.

개별 문항(Item) CRUD API를 제공합니다.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database import get_db
from src.models.item import Item
from src.models.set import Set
from src.models.task import TaskType
from src.schemas.item import (
    ItemCreate,
    ItemListResponse,
    ItemResponse,
    ItemUpdate,
)

router = APIRouter()


@router.get("", response_model=ItemListResponse)
async def list_items(
    db: AsyncSession = Depends(get_db),
    set_id: str | None = Query(None, description="Set UUID 필터"),
    task_type: TaskType | None = Query(None, description="문항 유형 필터"),
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(100, ge=1, le=500, description="조회 개수"),
) -> ItemListResponse:
    """
    Item 목록 조회

    Args:
        db: 데이터베이스 세션
        set_id: Set UUID 필터 (선택)
        task_type: 문항 유형 필터 (선택)
        skip: 건너뛸 개수
        limit: 최대 조회 개수

    Returns:
        Item 목록 및 페이징 정보
    """
    # 기본 쿼리
    query = select(Item)

    # 필터 적용
    if set_id:
        try:
            set_uuid = uuid.UUID(set_id)
            query = query.where(Item.set_id == set_uuid)
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid set_id format",
            ) from err

    if task_type:
        query = query.where(Item.task_type == task_type)

    # 전체 개수 조회
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 페이징 적용
    query = query.offset(skip).limit(limit).order_by(Item.set_id, Item.task_no)
    result = await db.execute(query)
    items = result.scalars().all()

    return ItemListResponse(
        items=[ItemResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item_data: ItemCreate,
    db: AsyncSession = Depends(get_db),
) -> ItemResponse:
    """
    새로운 Item 생성

    Args:
        item_data: Item 생성 정보
        db: 데이터베이스 세션

    Returns:
        생성된 Item 정보

    Raises:
        HTTPException: Set을 찾을 수 없거나 중복된 task_no인 경우
    """
    # Set 존재 확인
    set_result = await db.execute(select(Set).where(Set.id == item_data.set_id))
    set_obj = set_result.scalar_one_or_none()
    if not set_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Set with id '{item_data.set_id}' not found",
        )

    # task_no 중복 확인
    existing_query = select(Item).where(
        Item.set_id == item_data.set_id,
        Item.task_no == item_data.task_no,
    )
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Item with task_no={item_data.task_no} already exists in this Set",
        )

    # Item 생성
    new_item = Item(
        id=uuid.uuid4(),
        set_id=item_data.set_id,
        task_no=item_data.task_no,
        task_type=item_data.task_type,
        prompt=item_data.prompt,
        prep_seconds=item_data.prep_seconds,
        response_seconds=item_data.response_seconds,
        topic_type=item_data.topic_type,
        topic_category=item_data.topic_category,
        question_pattern=item_data.question_pattern,
        tags=item_data.tags,
        difficulty=item_data.difficulty,
        scoring_focus=item_data.scoring_focus,
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)

    return ItemResponse.model_validate(new_item)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
) -> ItemResponse:
    """
    특정 Item 조회

    Args:
        item_id: Item UUID
        db: 데이터베이스 세션

    Returns:
        Item 정보

    Raises:
        HTTPException: Item을 찾을 수 없는 경우 (404)
    """
    try:
        item_uuid = uuid.UUID(item_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item_id format",
        ) from err

    result = await db.execute(select(Item).where(Item.id == item_uuid))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    return ItemResponse.model_validate(item)


@router.patch("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: str,
    item_data: ItemUpdate,
    db: AsyncSession = Depends(get_db),
) -> ItemResponse:
    """
    Item 수정

    Args:
        item_id: Item UUID
        item_data: 수정할 정보
        db: 데이터베이스 세션

    Returns:
        수정된 Item 정보

    Raises:
        HTTPException: Item을 찾을 수 없는 경우 (404)
    """
    try:
        item_uuid = uuid.UUID(item_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item_id format",
        ) from err

    result = await db.execute(select(Item).where(Item.id == item_uuid))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    # 업데이트할 필드만 적용
    update_data = item_data.model_dump(exclude_unset=True)

    # task_no 중복 검사 (변경된 경우)
    if "task_no" in update_data and update_data["task_no"] != item.task_no:
        existing_query = select(Item).where(
            Item.set_id == item.set_id,
            Item.task_no == update_data["task_no"],
        )
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Item with task_no={update_data['task_no']} already exists in this Set",
            )

    for field, value in update_data.items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)

    return ItemResponse.model_validate(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Item 삭제

    Item 삭제 시 연결된 모든 Stimulus, AnswerKey도 함께 삭제됩니다 (CASCADE).

    Args:
        item_id: Item UUID
        db: 데이터베이스 세션

    Raises:
        HTTPException: Item을 찾을 수 없는 경우 (404)
    """
    try:
        item_uuid = uuid.UUID(item_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item_id format",
        ) from err

    result = await db.execute(select(Item).where(Item.id == item_uuid))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    await db.delete(item)
    await db.commit()


@router.get("/{item_id}/with-relations", response_model=dict)
async def get_item_with_relations(
    item_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Item과 관련된 Stimulus, AnswerKey를 함께 조회

    Args:
        item_id: Item UUID
        db: 데이터베이스 세션

    Returns:
        Item, Stimulus 목록, AnswerKey 목록

    Raises:
        HTTPException: Item을 찾을 수 없는 경우 (404)
    """
    try:
        item_uuid = uuid.UUID(item_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item_id format",
        ) from err

    # Load item with relationships using selectinload
    query = (
        select(Item)
        .where(Item.id == item_uuid)
        .options(selectinload(Item.stimuli), selectinload(Item.answer_keys))
    )
    result = await db.execute(query)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    return {
        "item": ItemResponse.model_validate(item),
        "stimuli": [
            {
                "id": str(s.id),
                "kind": s.kind.value,
                "title": s.title,
                "content_text": s.content_text,
                "asset_url": s.asset_url,
                "duration_seconds": s.duration_seconds,
                "display_order": s.display_order,
                "notes_allowed": s.notes_allowed,
                "created_at": s.created_at.isoformat(),
            }
            for s in item.stimuli
        ],
        "answer_keys": [
            {
                "id": str(ak.id),
                "answer_type": ak.answer_type.value,
                "level": ak.level.value if ak.level else None,
                "content": ak.content,
                "source": ak.source,
                "created_at": ak.created_at.isoformat(),
            }
            for ak in item.answer_keys
        ],
    }
