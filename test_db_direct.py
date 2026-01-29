import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def test_connection():
    # Direct Connection URL
    database_url = "postgresql+asyncpg://postgres:eVmUDlupAo621TDt@db.fgbhcmrpwinlogjpwivp.supabase.co:5432/postgres"

    print("Direct Connection 시도 중...")
    print(f"URL: {database_url[:60]}...")

    engine = create_async_engine(database_url, echo=False)

    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            print("\n✅ Supabase 연결 성공!")
            print(f"PostgreSQL 버전: {version[:80]}")

            # 테이블 목록 확인
            result = await conn.execute(
                text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                LIMIT 5;
            """)
            )
            tables = result.fetchall()
            print(f"\n현재 public 스키마의 테이블: {[t[0] for t in tables]}")

    except Exception as e:
        print(f"\n❌ 연결 실패: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_connection())
