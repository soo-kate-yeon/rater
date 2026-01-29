"""
IndependentTopic 모델 테스트 - SQLAlchemy ORM 동작 검증.

PRESERVE 단계: 모델 동작 검증
- 모델 생성 및 필드 설정
- 타임스탬프 자동 생성 (created_at, updated_at)
- 데이터베이스 저장 및 조회
- unique 제약조건 (number 필드)
"""

import sys
from pathlib import Path

# src 디렉토리를 sys.path에 추가하여 직접 임포트
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest

# models/__init__.py를 우회하여 직접 임포트
from models.independent_topic import IndependentTopic
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class TestIndependentTopicModel:
    """IndependentTopic 모델 기본 동작 검증"""

    @pytest.mark.asyncio
    async def test_model_creation(self, test_db: AsyncSession):
        """모델 인스턴스 생성 및 필드 설정"""
        # Given
        topic = IndependentTopic(
            number=1,
            prompt="Do you agree or disagree with the following statement?",
            source="Independent_Topics.pdf",
        )

        # Then: 필드가 올바르게 설정됨
        assert topic.number == 1
        assert topic.prompt == "Do you agree or disagree with the following statement?"
        assert topic.source == "Independent_Topics.pdf"

    @pytest.mark.asyncio
    async def test_database_persistence(self, test_db: AsyncSession):
        """데이터베이스에 저장 및 조회"""
        # Given
        topic = IndependentTopic(
            number=1,
            prompt="Test prompt",
            source="Test source",
        )
        test_db.add(topic)
        await test_db.commit()
        await test_db.refresh(topic)

        # When: 데이터베이스에서 조회
        result = await test_db.execute(select(IndependentTopic).where(IndependentTopic.number == 1))
        retrieved_topic = result.scalar_one_or_none()

        # Then: 저장된 데이터가 조회됨
        assert retrieved_topic is not None
        assert retrieved_topic.number == 1
        assert retrieved_topic.prompt == "Test prompt"
        assert retrieved_topic.source == "Test source"

    @pytest.mark.asyncio
    async def test_uuid_primary_key_auto_generated(self, test_db: AsyncSession):
        """UUID 기본 키가 자동 생성됨 (BaseModel에서 상속)"""
        # Given
        topic = IndependentTopic(
            number=1,
            prompt="Test",
            source="Test",
        )
        test_db.add(topic)
        await test_db.commit()
        await test_db.refresh(topic)

        # Then: UUID가 자동 생성됨
        assert topic.id is not None
        assert len(str(topic.id)) == 36  # UUID 형식

    @pytest.mark.asyncio
    async def test_timestamp_auto_generation(self, test_db: AsyncSession):
        """created_at, updated_at 타임스탬프가 자동 생성됨"""
        # Given
        topic = IndependentTopic(
            number=1,
            prompt="Test",
            source="Test",
        )

        # When: 데이터베이스에 저장
        test_db.add(topic)
        await test_db.commit()
        await test_db.refresh(topic)

        # Then: 타임스탬프가 자동 생성됨
        assert topic.created_at is not None
        assert topic.updated_at is not None
        assert topic.created_at == topic.updated_at  # 생성 시점에는 동일

    @pytest.mark.asyncio
    async def test_number_unique_constraint(self, test_db: AsyncSession):
        """number 필드의 unique 제약조건 검증"""
        # Given: 첫 번째 토픽 저장
        topic1 = IndependentTopic(
            number=1,
            prompt="First topic",
            source="Source 1",
        )
        test_db.add(topic1)
        await test_db.commit()

        # When: 같은 number로 두 번째 토픽 저장 시도
        topic2 = IndependentTopic(
            number=1,  # 중복
            prompt="Second topic",
            source="Source 2",
        )
        test_db.add(topic2)

        # Then: IntegrityError 발생
        with pytest.raises(IntegrityError):
            await test_db.commit()

    @pytest.mark.asyncio
    async def test_repr_method(self, test_db: AsyncSession):
        """__repr__ 메서드가 올바르게 동작함"""
        # Given
        topic = IndependentTopic(
            number=1,
            prompt="Test",
            source="Test",
        )
        test_db.add(topic)
        await test_db.commit()
        await test_db.refresh(topic)

        # When
        repr_str = repr(topic)

        # Then: ID, number, source가 포함됨
        assert "IndependentTopic" in repr_str
        assert str(topic.id) in repr_str
        assert "number=1" in repr_str
        assert "Test" in repr_str


class TestIndependentTopicFieldConstraints:
    """필드 제약조건 검증"""

    @pytest.mark.asyncio
    async def test_number_cannot_be_null(self, test_db: AsyncSession):
        """number는 nullable=False"""
        # Given: number 없이 생성 시도
        topic = IndependentTopic(
            prompt="Test",
            source="Test",
        )

        # When/Then: 데이터베이스 저장 시 오류 발생
        test_db.add(topic)
        with pytest.raises(IntegrityError):
            await test_db.commit()

    @pytest.mark.asyncio
    async def test_prompt_cannot_be_null(self, test_db: AsyncSession):
        """prompt는 nullable=False"""
        # Given: prompt 없이 생성 시도
        topic = IndependentTopic(
            number=1,
            source="Test",
        )

        # When/Then
        test_db.add(topic)
        with pytest.raises(IntegrityError):
            await test_db.commit()

    @pytest.mark.asyncio
    async def test_source_cannot_be_null(self, test_db: AsyncSession):
        """source는 nullable=False"""
        # Given: source 없이 생성 시도
        topic = IndependentTopic(
            number=1,
            prompt="Test",
        )

        # When/Then
        test_db.add(topic)
        with pytest.raises(IntegrityError):
            await test_db.commit()

    @pytest.mark.asyncio
    async def test_prompt_text_type(self, test_db: AsyncSession):
        """prompt는 Text 타입으로 긴 텍스트 저장 가능"""
        # Given: 매우 긴 prompt
        long_prompt = "A" * 10000

        topic = IndependentTopic(
            number=1,
            prompt=long_prompt,
            source="Test",
        )

        # When
        test_db.add(topic)
        await test_db.commit()
        await test_db.refresh(topic)

        # Then: 긴 텍스트가 저장됨
        assert len(topic.prompt) == 10000


class TestIndependentTopicQueries:
    """모델 쿼리 동작 검증"""

    @pytest.mark.asyncio
    async def test_filter_by_number(self, test_db: AsyncSession):
        """number로 필터링 쿼리"""
        # Given: 여러 토픽 저장
        topics = [
            IndependentTopic(number=1, prompt="Prompt 1", source="Source 1"),
            IndependentTopic(number=2, prompt="Prompt 2", source="Source 2"),
            IndependentTopic(number=3, prompt="Prompt 3", source="Source 3"),
        ]
        for topic in topics:
            test_db.add(topic)
        await test_db.commit()

        # When: number=2 조회
        result = await test_db.execute(select(IndependentTopic).where(IndependentTopic.number == 2))
        topic = result.scalar_one_or_none()

        # Then
        assert topic is not None
        assert topic.number == 2
        assert topic.prompt == "Prompt 2"

    @pytest.mark.asyncio
    async def test_filter_by_source(self, test_db: AsyncSession):
        """source로 필터링 쿼리"""
        # Given
        topics = [
            IndependentTopic(number=1, prompt="P1", source="Source A"),
            IndependentTopic(number=2, prompt="P2", source="Source A"),
            IndependentTopic(number=3, prompt="P3", source="Source B"),
        ]
        for topic in topics:
            test_db.add(topic)
        await test_db.commit()

        # When: Source A 조회
        result = await test_db.execute(
            select(IndependentTopic).where(IndependentTopic.source == "Source A")
        )
        topics_from_source_a = result.scalars().all()

        # Then: 2개 조회됨
        assert len(topics_from_source_a) == 2
        assert all(t.source == "Source A" for t in topics_from_source_a)

    @pytest.mark.asyncio
    async def test_order_by_number(self, test_db: AsyncSession):
        """number 순서로 정렬"""
        # Given: 역순으로 저장
        topics = [
            IndependentTopic(number=3, prompt="P3", source="S"),
            IndependentTopic(number=1, prompt="P1", source="S"),
            IndependentTopic(number=2, prompt="P2", source="S"),
        ]
        for topic in topics:
            test_db.add(topic)
        await test_db.commit()

        # When: number 오름차순 조회
        result = await test_db.execute(select(IndependentTopic).order_by(IndependentTopic.number))
        ordered_topics = result.scalars().all()

        # Then: 1, 2, 3 순서
        assert [t.number for t in ordered_topics] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_count_topics(self, test_db: AsyncSession):
        """토픽 개수 카운트"""
        # Given: 5개 토픽 저장
        for i in range(1, 6):
            topic = IndependentTopic(number=i, prompt=f"P{i}", source="S")
            test_db.add(topic)
        await test_db.commit()

        # When: 전체 개수 조회
        result = await test_db.execute(select(IndependentTopic))
        topics = result.scalars().all()

        # Then: 5개
        assert len(topics) == 5


class TestIndependentTopicRealWorldScenarios:
    """실제 사용 시나리오 테스트"""

    @pytest.mark.asyncio
    async def test_bulk_insert_294_topics(self, test_db: AsyncSession):
        """294개 토픽 대량 삽입 (실제 independent_topics.json 크기)"""
        # Given: 294개 토픽 생성
        topics = [
            IndependentTopic(
                number=i,
                prompt=f"Topic prompt {i}",
                source="Independent_Topics.pdf",
            )
            for i in range(1, 295)
        ]

        # When: 대량 삽입
        for topic in topics:
            test_db.add(topic)
        await test_db.commit()

        # Then: 294개 모두 저장됨
        result = await test_db.execute(select(IndependentTopic))
        all_topics = result.scalars().all()
        assert len(all_topics) == 294

    @pytest.mark.asyncio
    async def test_update_prompt(self, test_db: AsyncSession):
        """토픽의 prompt 업데이트"""
        # Given: 토픽 생성
        topic = IndependentTopic(
            number=1,
            prompt="Original prompt",
            source="Test",
        )
        test_db.add(topic)
        await test_db.commit()
        await test_db.refresh(topic)

        original_created_at = topic.created_at

        # When: prompt 수정
        topic.prompt = "Updated prompt"
        await test_db.commit()
        await test_db.refresh(topic)

        # Then: prompt가 변경되고 updated_at이 갱신됨
        assert topic.prompt == "Updated prompt"
        assert topic.created_at == original_created_at  # created_at은 불변
        assert topic.updated_at >= original_created_at  # updated_at은 갱신

    @pytest.mark.asyncio
    async def test_delete_topic(self, test_db: AsyncSession):
        """토픽 삭제"""
        # Given
        topic = IndependentTopic(
            number=1,
            prompt="Test",
            source="Test",
        )
        test_db.add(topic)
        await test_db.commit()

        # When: 삭제
        await test_db.delete(topic)
        await test_db.commit()

        # Then: 조회 불가
        result = await test_db.execute(select(IndependentTopic).where(IndependentTopic.number == 1))
        deleted_topic = result.scalar_one_or_none()
        assert deleted_topic is None
