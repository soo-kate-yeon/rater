import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_sqlite():
    # SQLite (aiosqlite)
    database_url = "sqlite+aiosqlite:///./toefl_rater.db"
    
    print("SQLite 연결 테스트...\n")
    
    engine = create_async_engine(database_url, echo=False)
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT sqlite_version();"))
            version = result.scalar()
            print("✅ SQLite 연결 성공!")
            print(f"SQLite 버전: {version}\n")
            print("데이터베이스 파일: ./toefl_rater.db")
            print("\n로컬 개발 환경으로 사용 가능합니다.")
            
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_sqlite())
