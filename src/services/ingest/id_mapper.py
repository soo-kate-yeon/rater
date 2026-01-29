"""
ID 매핑 레이어 - String ID를 UUID로 변환.

uuid.uuid5()를 사용하여 deterministic한 매핑을 제공합니다.
같은 string ID는 항상 같은 UUID로 변환됩니다.
"""

import uuid
from uuid import UUID


class IDMapper:
    """
    String ID를 UUID로 매핑하는 유틸리티 클래스.

    각 엔티티 타입별로 별도의 네임스페이스를 사용하여
    동일한 string ID가 다른 엔티티에서 다른 UUID로 매핑되도록 합니다.
    """

    # 네임스페이스 정의 (각 엔티티 타입별)
    NAMESPACE_SET = uuid.uuid5(uuid.NAMESPACE_DNS, "toefl.speaking.set")
    NAMESPACE_ITEM = uuid.uuid5(uuid.NAMESPACE_DNS, "toefl.speaking.item")
    NAMESPACE_STIMULUS = uuid.uuid5(uuid.NAMESPACE_DNS, "toefl.speaking.stimulus")
    NAMESPACE_ANSWER_KEY = uuid.uuid5(uuid.NAMESPACE_DNS, "toefl.speaking.answer_key")
    NAMESPACE_TOPIC = uuid.uuid5(uuid.NAMESPACE_DNS, "toefl.speaking.topic")

    @classmethod
    def to_set_uuid(cls, set_id: str) -> UUID:
        """
        Set ID를 UUID로 변환.

        Args:
            set_id: Set의 string ID (예: "ACTUAL_TEST_01")

        Returns:
            변환된 UUID

        Examples:
            >>> mapper = IDMapper()
            >>> uuid1 = mapper.to_set_uuid("ACTUAL_TEST_01")
            >>> uuid2 = mapper.to_set_uuid("ACTUAL_TEST_01")
            >>> uuid1 == uuid2  # True (deterministic)
        """
        return uuid.uuid5(cls.NAMESPACE_SET, set_id)

    @classmethod
    def to_item_uuid(cls, item_id: str) -> UUID:
        """
        Item ID를 UUID로 변환.

        Args:
            item_id: Item의 string ID

        Returns:
            변환된 UUID
        """
        return uuid.uuid5(cls.NAMESPACE_ITEM, item_id)

    @classmethod
    def to_stimulus_uuid(cls, stimulus_id: str) -> UUID:
        """
        Stimulus ID를 UUID로 변환.

        Args:
            stimulus_id: Stimulus의 string ID

        Returns:
            변환된 UUID
        """
        return uuid.uuid5(cls.NAMESPACE_STIMULUS, stimulus_id)

    @classmethod
    def to_answer_key_uuid(cls, answer_id: str) -> UUID:
        """
        AnswerKey ID를 UUID로 변환.

        Args:
            answer_id: AnswerKey의 string ID

        Returns:
            변환된 UUID
        """
        return uuid.uuid5(cls.NAMESPACE_ANSWER_KEY, answer_id)

    @classmethod
    def to_topic_uuid(cls, topic_id: str) -> UUID:
        """
        IndependentTopic ID를 UUID로 변환.

        Args:
            topic_id: IndependentTopic의 string ID

        Returns:
            변환된 UUID
        """
        return uuid.uuid5(cls.NAMESPACE_TOPIC, topic_id)
