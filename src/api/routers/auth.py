"""인증 라우터"""


from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from src.models.user import User
from src.schemas.auth import Token, UserRegister, UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    회원가입 엔드포인트

    Args:
        user_data: 회원가입 정보 (이메일, 비밀번호, 이름)
        db: 데이터베이스 세션

    Returns:
        생성된 사용자 정보

    Raises:
        HTTPException: 이메일이 이미 존재하는 경우 (409)
    """
    # 이메일 중복 확인
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # 비밀번호 해싱
    hashed_pw = hash_password(user_data.password)

    # 사용자 생성
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pw,
        name=user_data.name,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse.model_validate(new_user)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    로그인 엔드포인트

    Args:
        form_data: OAuth2 로그인 폼 (username=이메일, password)
        db: 데이터베이스 세션

    Returns:
        JWT 액세스 토큰

    Raises:
        HTTPException: 인증 실패 시 (401)
    """
    # 사용자 조회 (username은 이메일)
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    # 사용자 존재 및 비밀번호 확인
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # JWT 토큰 생성
    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token, token_type="bearer")
