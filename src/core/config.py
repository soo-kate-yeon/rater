"""환경 변수 및 설정 관리"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/toefl_rater",
        description="PostgreSQL 데이터베이스 연결 URL",
    )

    # Redis
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis 연결 URL (Celery 브로커)",
    )

    # OpenAI
    openai_api_key: str = Field(
        default="",
        description="OpenAI API 키 (Whisper + GPT-4)",
    )

    # Anthropic (선택사항)
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API 키 (Claude)",
    )

    # Storage
    storage_path: str = Field(
        default="./storage",
        description="로컬 파일 저장소 경로",
    )
    aws_s3_bucket: str = Field(
        default="",
        description="S3 버킷 이름",
    )
    aws_access_key_id: str = Field(
        default="",
        description="AWS Access Key ID",
    )
    aws_secret_access_key: str = Field(
        default="",
        description="AWS Secret Access Key",
    )
    aws_region: str = Field(
        default="ap-northeast-2",
        description="AWS 리전",
    )

    # JWT
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT 시크릿 키",
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT 알고리즘",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="액세스 토큰 만료 시간 (분)",
    )

    # Server
    api_host: str = Field(
        default="0.0.0.0",
        description="API 서버 호스트",
    )
    api_port: int = Field(
        default=8000,
        description="API 서버 포트",
    )
    debug: bool = Field(
        default=True,
        description="디버그 모드",
    )

    # Whisper
    whisper_model: Literal["tiny", "base", "small", "medium", "large"] = Field(
        default="base",
        description="Whisper 모델 크기",
    )
    whisper_device: Literal["cpu", "cuda"] = Field(
        default="cpu",
        description="Whisper 실행 디바이스",
    )

    # Feature Flags
    use_local_whisper: bool = Field(
        default=True,
        description="로컬 Whisper 사용 여부",
    )
    use_openai_whisper: bool = Field(
        default=False,
        description="OpenAI Whisper API 사용 여부",
    )

    @property
    def database_url_str(self) -> str:
        """SQLAlchemy용 문자열 URL 반환"""
        return str(self.database_url)

    @property
    def redis_url_str(self) -> str:
        """Redis용 문자열 URL 반환"""
        return str(self.redis_url)


@lru_cache
def get_settings() -> Settings:
    """설정 싱글톤 인스턴스 반환"""
    return Settings()


# 전역 설정 인스턴스
settings = get_settings()
