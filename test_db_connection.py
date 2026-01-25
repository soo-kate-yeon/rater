import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def test_connection():
    # .env 파일에서 DATABASE_URL 읽기
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    
    print(f"연결 시도 중: {database_url[:50]}...")
    
    engine = create_async_engine(database_url, echo=True)
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"\n✅ Supabase 연결 성공!")
            print(f"PostgreSQL 버전: {version}")
    except Exception as e:
        print(f"\n❌ 연결 실패: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    from sqlalchemy import text
    asyncio.run(test_connection())
