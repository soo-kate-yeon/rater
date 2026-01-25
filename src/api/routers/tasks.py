"""Task 관리 라우터"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.task import Task, TaskType
from src.schemas.tasks import TaskCreate, TaskResponse

router = APIRouter()


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> List[TaskResponse]:
    """
    Task 목록 조회

    Args:
        db: 데이터베이스 세션
        skip: 건너뛸 개수
        limit: 최대 조회 개수

    Returns:
        Task 목록
    """
    result = await db.execute(
        select(Task).offset(skip).limit(limit).order_by(Task.created_at.desc())
    )
    tasks = result.scalars().all()
    return [TaskResponse.model_validate(task) for task in tasks]


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """
    새로운 Task 생성

    Args:
        task_data: Task 생성 정보
        db: 데이터베이스 세션

    Returns:
        생성된 Task 정보
    """
    new_task = Task(
        id=uuid.uuid4(),
        task_type=TaskType(task_data.task_type),
        prompt=task_data.prompt,
        source_reading=task_data.source_reading,
        source_listening=task_data.source_listening,
        tags=task_data.tags or {},
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return TaskResponse.model_validate(new_task)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """
    특정 Task 조회

    Args:
        task_id: Task UUID
        db: 데이터베이스 세션

    Returns:
        Task 정보

    Raises:
        HTTPException: Task를 찾을 수 없는 경우 (404)
    """
    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task_id format",
        )

    result = await db.execute(select(Task).where(Task.id == task_uuid))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return TaskResponse.model_validate(task)
