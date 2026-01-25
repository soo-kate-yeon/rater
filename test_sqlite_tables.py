import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_tables():
    database_url = "sqlite+aiosqlite:///./toefl_rater.db"

    print("SQLite 데이터베이스 테이블 확인 중...\n")

    engine = create_async_engine(database_url, echo=False)

    try:
        async with engine.connect() as conn:
            # 테이블 목록 확인
            result = await conn.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                ORDER BY name;
            """))
            tables = result.fetchall()

            print(f"✅ 생성된 테이블 ({len(tables)}개):")
            for table in tables:
                print(f"  - {table[0]}")

            print("\n각 테이블의 컬럼 정보:")
            for table in tables:
                table_name = table[0]
                if table_name != 'alembic_version':
                    result = await conn.execute(text(f"PRAGMA table_info({table_name});"))
                    columns = result.fetchall()
                    print(f"\n[{table_name}]")
                    for col in columns:
                        print(f"  {col[1]} ({col[2]})")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_tables())
