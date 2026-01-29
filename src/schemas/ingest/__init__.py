"""
Ingest 스키마 - JSON 파일 파싱용 Pydantic 모델.

external/*.json 파일을 파싱하고 검증하기 위한 스키마를 정의합니다.
API 스키마와 달리 string ID를 사용하며, UUID 변환은 매핑 레이어에서 처리합니다.
"""

from .answer_key import AnswerKeyIngest
from .item import ItemIngest
from .set import SetIngest
from .stimulus import StimulusIngest
from .topic import IndependentTopicIngest

__all__ = [
    "SetIngest",
    "ItemIngest",
    "StimulusIngest",
    "AnswerKeyIngest",
    "IndependentTopicIngest",
]
