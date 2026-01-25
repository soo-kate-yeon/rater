"""
시스템 통합 테스트 스크립트
API 서버의 주요 엔드포인트를 테스트합니다.
"""
import asyncio
import httpx
from pathlib import Path

BASE_URL = "http://localhost:8000"

async def test_system():
    print("=" * 60)
    print("TOEFL Rater 시스템 테스트")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        # 1. Health Check
        print("\n[1/6] Health Check 테스트...")
        try:
            response = await client.get(f"{BASE_URL}/")
            print(f"  ✅ 상태 코드: {response.status_code}")
            print(f"  응답: {response.json()}")
        except Exception as e:
            print(f"  ❌ 실패: {e}")
            return

        # 2. 사용자 등록
        print("\n[2/6] 사용자 등록 테스트...")
        try:
            user_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            response = await client.post(f"{BASE_URL}/v1/auth/register", json=user_data)
            print(f"  ✅ 상태 코드: {response.status_code}")
            if response.status_code == 200:
                user_info = response.json()
                print(f"  생성된 사용자 ID: {user_info.get('id')}")
            else:
                print(f"  응답: {response.json()}")
        except Exception as e:
            print(f"  ❌ 실패: {e}")

        # 3. 로그인
        print("\n[3/6] 로그인 테스트...")
        try:
            login_data = {
                "username": "test@example.com",
                "password": "testpassword123"
            }
            response = await client.post(
                f"{BASE_URL}/v1/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            print(f"  ✅ 상태 코드: {response.status_code}")
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                print(f"  토큰 타입: {token_data.get('token_type')}")
                print(f"  액세스 토큰: {access_token[:50]}...")

                # 이후 요청에 사용할 헤더
                auth_headers = {"Authorization": f"Bearer {access_token}"}
            else:
                print(f"  응답: {response.json()}")
                auth_headers = {}
        except Exception as e:
            print(f"  ❌ 실패: {e}")
            auth_headers = {}

        # 4. Task 목록 조회
        print("\n[4/6] Task 목록 조회 테스트...")
        try:
            response = await client.get(f"{BASE_URL}/v1/tasks")
            print(f"  ✅ 상태 코드: {response.status_code}")
            if response.status_code == 200:
                tasks = response.json()
                print(f"  등록된 Task 개수: {len(tasks)}")
            else:
                print(f"  응답: {response.json()}")
        except Exception as e:
            print(f"  ❌ 실패: {e}")

        # 5. Task 생성
        print("\n[5/6] Task 생성 테스트...")
        try:
            task_data = {
                "task_type": "INDEPENDENT",
                "prompt": "Do you agree or disagree with the following statement? It is better to work in a team than to work alone.",
                "tags": {"difficulty": "medium", "topic": "work"}
            }
            response = await client.post(
                f"{BASE_URL}/v1/tasks",
                json=task_data,
                headers=auth_headers
            )
            print(f"  ✅ 상태 코드: {response.status_code}")
            if response.status_code == 200:
                task_info = response.json()
                task_id = task_info.get("id")
                print(f"  생성된 Task ID: {task_id}")
                print(f"  Task 타입: {task_info.get('task_type')}")
            else:
                print(f"  응답: {response.json()}")
                task_id = None
        except Exception as e:
            print(f"  ❌ 실패: {e}")
            task_id = None

        # 6. Job 생성 (Redis 필요 - 실패 예상)
        print("\n[6/6] Job 생성 테스트 (Redis 필요)...")
        if not auth_headers:
            print("  ⚠️  건너뜀: 인증 토큰 없음")
        elif not task_id:
            print("  ⚠️  건너뜀: Task ID 없음")
        else:
            try:
                # 테스트용 오디오 파일 생성
                audio_content = b"fake audio data for testing"
                files = {"file": ("test.mp3", audio_content, "audio/mpeg")}
                data = {"task_id": task_id}

                response = await client.post(
                    f"{BASE_URL}/v1/jobs",
                    files=files,
                    data=data,
                    headers=auth_headers
                )
                print(f"  상태 코드: {response.status_code}")
                if response.status_code == 200:
                    print("  ✅ Job 생성 성공")
                    job_info = response.json()
                    print(f"  Job ID: {job_info.get('id')}")
                    print(f"  상태: {job_info.get('status')}")
                else:
                    print(f"  ⚠️  응답: {response.json()}")
            except Exception as e:
                print(f"  ⚠️  예상된 실패 (Redis 미설치): {e}")

        print("\n" + "=" * 60)
        print("테스트 완료")
        print("=" * 60)
        print("\n참고사항:")
        print("- Job 생성을 위해서는 Redis와 Celery Worker가 필요합니다")
        print("- Redis 설치: brew install redis")
        print("- Redis 실행: redis-server")
        print("- Worker 실행: uv run celery -A src.workers.celery_app worker --loglevel=info")

if __name__ == "__main__":
    asyncio.run(test_system())
