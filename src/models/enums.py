"""
TOEFL Speaking 스키마 확장을 위한 Enum 정의.

이 모듈은 Set, Item, Stimulus, AnswerKey 모델에서 사용되는 열거형을 정의합니다.
"""

import enum


class TopicType(str, enum.Enum):
    """
    Independent 문제의 주제 유형.

    Independent 문제에서 다루는 질문의 형태를 정의합니다.
    """

    PREFERENCE = "preference"  # "Do you prefer A or B?"
    AGREE_DISAGREE = "agree_disagree"  # "Do you agree or disagree..."
    DESCRIPTION = "description"  # "Describe a..."
    OPINION = "opinion"  # "What is your opinion..."
    HYPOTHETICAL = "hypothetical"  # "If you could..."


class TopicCategory(str, enum.Enum):
    """
    Independent 문제의 주제 카테고리.

    문제가 다루는 주제 영역을 분류합니다.
    """

    EDUCATION = "education"
    TECHNOLOGY = "technology"
    LIFESTYLE = "lifestyle"
    WORK = "work"
    RELATIONSHIPS = "relationships"
    SOCIETY = "society"


class StimulusKind(str, enum.Enum):
    """
    자극자료(Stimulus) 유형.

    문제에 제공되는 자료의 형태를 정의합니다.
    """

    READING = "reading"  # 읽기 지문
    AUDIO = "audio"  # 음성 자료
    IMAGE = "image"  # 이미지
    DIRECTION = "direction"  # 문제 지시문


class AnswerKeyType(str, enum.Enum):
    """
    모범답안(AnswerKey) 유형.

    모범답안 또는 채점 기준의 형태를 정의합니다.
    """

    SAMPLE_RESPONSE = "sample_response"  # 모범 응답
    TRANSCRIPT = "transcript"  # 듣기 자료 스크립트
    OUTLINE = "outline"  # 답변 개요
    POINTS = "points"  # 핵심 포인트
    BLUEPRINT = "blueprint"  # 구조화된 채점 기준


class AnswerKeyLevel(str, enum.Enum):
    """
    모범답안 수준.

    모범답안의 품질 수준을 나타냅니다.
    """

    HIGH = "high"  # 고득점 수준 (4점)
    MID = "mid"  # 중간 수준 (2-3점)
    LOW = "low"  # 저득점 수준 (1점)


class Difficulty(str, enum.Enum):
    """
    문제 난이도.

    Item의 난이도 수준을 정의합니다.
    """

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
