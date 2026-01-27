"""
Ingest 서비스 - JSON 데이터 수집 파이프라인.

external/*.json 파일을 파싱하고 데이터베이스에 시딩하는 서비스를 제공합니다.
"""
from .id_mapper import IDMapper

__all__ = [
    "IDMapper",
]
