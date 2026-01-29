"""인증 관련 Pydantic 스키마"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """회원가입 요청 스키마"""

    email: EmailStr = Field(..., description="사용자 이메일")
    password: str = Field(..., min_length=8, description="비밀번호 (최소 8자)")
    name: Optional[str] = Field(None, max_length=100, description="사용자 이름")


class UserLogin(BaseModel):
    """로그인 요청 스키마"""

    email: EmailStr = Field(..., description="사용자 이메일")
    password: str = Field(..., description="비밀번호")


class Token(BaseModel):
    """JWT 토큰 응답 스키마"""

    access_token: str = Field(..., description="JWT 액세스 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")


class UserResponse(BaseModel):
    """사용자 정보 응답 스키마"""

    id: UUID = Field(..., description="사용자 ID")
    email: str = Field(..., description="사용자 이메일")
    name: Optional[str] = Field(None, description="사용자 이름")

    model_config = {"from_attributes": True}
