"""
IDMapper 테스트 - uuid.uuid5() 기반 deterministic UUID 매핑 검증.

PRESERVE 단계: 기존 동작 검증
- 같은 string ID는 항상 같은 UUID로 변환됨 (deterministic)
- 서로 다른 네임스페이스는 같은 string ID에 대해 다른 UUID 생성
- 5개 엔티티 타입 모두 올바르게 동작함
"""

import uuid
from uuid import UUID

from src.services.ingest.id_mapper import IDMapper


class TestIDMapperDeterministic:
    """IDMapper의 deterministic 특성 검증"""

    def test_to_set_uuid_deterministic(self):
        """같은 set_id는 항상 같은 UUID를 반환해야 함"""
        # Given: 동일한 set_id
        set_id = "ACTUAL_TEST_01"

        # When: 두 번 변환
        uuid1 = IDMapper.to_set_uuid(set_id)
        uuid2 = IDMapper.to_set_uuid(set_id)

        # Then: 같은 UUID가 생성됨
        assert uuid1 == uuid2
        assert isinstance(uuid1, UUID)
        assert isinstance(uuid2, UUID)

    def test_to_item_uuid_deterministic(self):
        """같은 item_id는 항상 같은 UUID를 반환해야 함"""
        # Given
        item_id = "ITEM_INDEPENDENT_001"

        # When
        uuid1 = IDMapper.to_item_uuid(item_id)
        uuid2 = IDMapper.to_item_uuid(item_id)

        # Then
        assert uuid1 == uuid2
        assert isinstance(uuid1, UUID)

    def test_to_stimulus_uuid_deterministic(self):
        """같은 stimulus_id는 항상 같은 UUID를 반환해야 함"""
        # Given
        stimulus_id = "STIMULUS_READING_001"

        # When
        uuid1 = IDMapper.to_stimulus_uuid(stimulus_id)
        uuid2 = IDMapper.to_stimulus_uuid(stimulus_id)

        # Then
        assert uuid1 == uuid2
        assert isinstance(uuid1, UUID)

    def test_to_answer_key_uuid_deterministic(self):
        """같은 answer_id는 항상 같은 UUID를 반환해야 함"""
        # Given
        answer_id = "ANSWER_SAMPLE_001"

        # When
        uuid1 = IDMapper.to_answer_key_uuid(answer_id)
        uuid2 = IDMapper.to_answer_key_uuid(answer_id)

        # Then
        assert uuid1 == uuid2
        assert isinstance(uuid1, UUID)

    def test_to_topic_uuid_deterministic(self):
        """같은 topic_id는 항상 같은 UUID를 반환해야 함"""
        # Given
        topic_id = "TOPIC_001"

        # When
        uuid1 = IDMapper.to_topic_uuid(topic_id)
        uuid2 = IDMapper.to_topic_uuid(topic_id)

        # Then
        assert uuid1 == uuid2
        assert isinstance(uuid1, UUID)


class TestIDMapperNamespaceSeparation:
    """네임스페이스 분리 검증 - 같은 string ID라도 엔티티 타입별로 다른 UUID 생성"""

    def test_different_namespace_produces_different_uuid(self):
        """같은 string ID라도 네임스페이스가 다르면 다른 UUID가 생성됨"""
        # Given: 모든 엔티티에 동일한 string ID 사용
        same_string_id = "TEST_001"

        # When: 5개 엔티티 타입으로 변환
        set_uuid = IDMapper.to_set_uuid(same_string_id)
        item_uuid = IDMapper.to_item_uuid(same_string_id)
        stimulus_uuid = IDMapper.to_stimulus_uuid(same_string_id)
        answer_uuid = IDMapper.to_answer_key_uuid(same_string_id)
        topic_uuid = IDMapper.to_topic_uuid(same_string_id)

        # Then: 모두 다른 UUID가 생성됨
        all_uuids = {set_uuid, item_uuid, stimulus_uuid, answer_uuid, topic_uuid}
        assert len(all_uuids) == 5, "같은 string ID라도 네임스페이스별로 다른 UUID가 생성되어야 함"

    def test_set_and_item_namespace_collision_prevented(self):
        """Set과 Item이 같은 ID를 사용해도 충돌하지 않음"""
        # Given
        same_id = "RESOURCE_001"

        # When
        set_uuid = IDMapper.to_set_uuid(same_id)
        item_uuid = IDMapper.to_item_uuid(same_id)

        # Then
        assert set_uuid != item_uuid


class TestIDMapperNamespaceConstants:
    """네임스페이스 상수 검증"""

    def test_namespaces_are_valid_uuids(self):
        """모든 네임스페이스 상수가 유효한 UUID임을 검증"""
        # Then: 모든 네임스페이스가 UUID 타입
        assert isinstance(IDMapper.NAMESPACE_SET, UUID)
        assert isinstance(IDMapper.NAMESPACE_ITEM, UUID)
        assert isinstance(IDMapper.NAMESPACE_STIMULUS, UUID)
        assert isinstance(IDMapper.NAMESPACE_ANSWER_KEY, UUID)
        assert isinstance(IDMapper.NAMESPACE_TOPIC, UUID)

    def test_namespaces_are_different(self):
        """모든 네임스페이스가 서로 다름을 검증"""
        # Given
        namespaces = {
            IDMapper.NAMESPACE_SET,
            IDMapper.NAMESPACE_ITEM,
            IDMapper.NAMESPACE_STIMULUS,
            IDMapper.NAMESPACE_ANSWER_KEY,
            IDMapper.NAMESPACE_TOPIC,
        }

        # Then: 5개의 고유한 네임스페이스
        assert len(namespaces) == 5

    def test_namespace_derived_from_dns(self):
        """네임스페이스가 DNS 네임스페이스로부터 파생됨을 검증"""
        # When: 수동으로 네임스페이스 생성
        expected_set_namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "toefl.speaking.set")

        # Then: IDMapper의 네임스페이스와 일치
        assert IDMapper.NAMESPACE_SET == expected_set_namespace


class TestIDMapperEdgeCases:
    """경계 조건 및 예외 케이스 테스트"""

    def test_empty_string_id(self):
        """빈 문자열도 UUID로 변환 가능 (Pydantic validation은 별도)"""
        # Given
        empty_id = ""

        # When
        result = IDMapper.to_set_uuid(empty_id)

        # Then: UUID가 생성됨 (validation은 스키마 레벨에서)
        assert isinstance(result, UUID)

    def test_special_characters_in_id(self):
        """특수문자가 포함된 ID도 처리 가능"""
        # Given
        special_id = "SET@#$%^&*()_+-=[]{}|;':,.<>?/"

        # When
        result = IDMapper.to_set_uuid(special_id)

        # Then
        assert isinstance(result, UUID)

    def test_unicode_characters_in_id(self):
        """유니코드 문자가 포함된 ID도 처리 가능"""
        # Given
        unicode_id = "세트_001_テスト"

        # When
        result = IDMapper.to_set_uuid(unicode_id)

        # Then
        assert isinstance(result, UUID)

    def test_very_long_id(self):
        """매우 긴 ID도 처리 가능"""
        # Given
        long_id = "A" * 10000

        # When
        result = IDMapper.to_set_uuid(long_id)

        # Then
        assert isinstance(result, UUID)


class TestIDMapperRealWorldScenarios:
    """실제 사용 시나리오 테스트"""

    def test_actual_test_01_to_uuid(self):
        """실제 JSON 파일의 set_id가 올바르게 변환됨"""
        # Given: external/sets.json의 실제 set_id
        set_id = "ACTUAL_TEST_01"

        # When
        result = IDMapper.to_set_uuid(set_id)

        # Then: 예상되는 UUID (uuid.uuid5로 미리 계산)
        expected_uuid = uuid.uuid5(IDMapper.NAMESPACE_SET, set_id)
        assert result == expected_uuid
        assert str(result) == "4fccfa9b-40ee-57f6-8e94-18569daec687"

    def test_multiple_entities_mapping(self):
        """여러 엔티티의 ID를 동시에 매핑"""
        # Given: 하나의 Set과 3개의 Item
        set_id = "SET_001"
        item_ids = ["ITEM_001", "ITEM_002", "ITEM_003"]

        # When
        set_uuid = IDMapper.to_set_uuid(set_id)
        item_uuids = [IDMapper.to_item_uuid(item_id) for item_id in item_ids]

        # Then: 모든 UUID가 고유함
        all_uuids = [set_uuid] + item_uuids
        assert len(set(all_uuids)) == 4

        # And: Item UUID들이 서로 다름
        assert len(set(item_uuids)) == 3


class TestIDMapperPerformance:
    """성능 관련 테스트 (선택적)"""

    def test_batch_conversion_performance(self):
        """대량의 ID 변환이 빠르게 처리됨"""
        # Given: 1000개의 서로 다른 ID
        ids = [f"SET_{i:04d}" for i in range(1000)]

        # When: 모두 변환
        uuids = [IDMapper.to_set_uuid(id_) for id_ in ids]

        # Then: 모두 고유한 UUID
        assert len(set(uuids)) == 1000

    def test_repeated_conversion_consistent(self):
        """같은 ID를 반복 변환해도 일관성 유지"""
        # Given
        set_id = "PERFORMANCE_TEST"

        # When: 100번 변환
        uuids = [IDMapper.to_set_uuid(set_id) for _ in range(100)]

        # Then: 모두 동일
        assert len(set(uuids)) == 1
