import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def test_connection():
    # 정확한 Direct Connection URL
    database_url = "postgresql+asyncpg://postgres:eVmUDlupAo621TDt@db.fgbhcmrpwinlogjpwivp.supabase.co:5432/postgres"

    print("Supabase 연결 시도 중...\n")

    engine = create_async_engine(database_url, echo=False)

    try:
        async with engine.connect() as conn:
            # PostgreSQL 버전 확인
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            print("✅ Supabase 연결 성공!\n")
            print(f"PostgreSQL 버전: {version[:80]}...\n")

            # 현재 데이터베이스 정보
            result = await conn.execute(text("SELECT current_database(), current_user;"))
            db_info = result.fetchone()
            print(f"데이터베이스: {db_info[0]}")
            print(f"사용자: {db_info[1]}\n")

            # 테이블 목록 확인
            result = await conn.execute(
                text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
                LIMIT 10;
            """)
            )
            tables = result.fetchall()
            if tables:
                print(f"Public 스키마의 테이블 ({len(tables)}개):")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("Public 스키마에 테이블이 없습니다. (정상 - 새 프로젝트)")

    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_connection())
