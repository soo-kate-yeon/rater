"""
End-to-End 시스템 테스트
전체 채점 파이프라인 테스트: 오디오 업로드 → Job 생성 → 비동기 채점 → 결과 확인
"""
import asyncio
import time
from pathlib import Path
import httpx

BASE_URL = "http://localhost:8000"

async def test_end_to_end():
    print("=" * 70)
    print("TOEFL Rater End-to-End 테스트")
    print("=" * 70)

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        # 1. 사용자 등록
        print("\n[1/7] 사용자 등록...")
        user_data = {
            "email": "e2e_test@example.com",
            "password": "testpass123"
        }
        try:
            response = await client.post(f"{BASE_URL}/v1/auth/register", json=user_data)
            if response.status_code == 201:
                user_info = response.json()
                print(f"  ✅ 사용자 생성: {user_info['email']}")
            elif response.status_code == 409:
                print(f"  ℹ️  이미 존재하는 사용자 (계속 진행)")
            else:
                print(f"  ❌ 등록 실패: {response.status_code}")
                return
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            return

        # 2. 로그인
        print("\n[2/7] 로그인...")
        try:
            login_data = {
                "username": "e2e_test@example.com",
                "password": "testpass123"
            }
            response = await client.post(
                f"{BASE_URL}/v1/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data["access_token"]
                auth_headers = {"Authorization": f"Bearer {access_token}"}
                print(f"  ✅ 로그인 성공")
            else:
                print(f"  ❌ 로그인 실패: {response.status_code}")
                return
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            return

        # 3. Task 생성
        print("\n[3/7] TOEFL Task 생성...")
        try:
            task_data = {
                "task_type": "INDEPENDENT",
                "prompt": "Some people prefer to work independently. Others prefer to work in teams. Which do you prefer? Use specific reasons and examples to support your answer.",
                "tags": {"difficulty": "medium", "category": "work-preference"}
            }
            response = await client.post(
                f"{BASE_URL}/v1/tasks",
                json=task_data,
                headers=auth_headers
            )
            if response.status_code == 201:
                task_info = response.json()
                task_id = task_info["id"]
                print(f"  ✅ Task 생성: {task_id}")
            else:
                print(f"  ❌ Task 생성 실패: {response.status_code}")
                return
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            return

        # 4. 오디오 파일 업로드
        print("\n[4/7] 오디오 파일 업로드...")
        try:
            # 테스트용 더미 오디오 데이터 (실제로는 MP3/WAV 파일)
            audio_content = b"RIFF" + b"\x00" * 100  # 더미 WAV 헤더
            files = {"file": ("test_speaking.wav", audio_content, "audio/wav")}

            response = await client.post(
                f"{BASE_URL}/v1/uploads/audio",
                files=files,
                headers=auth_headers
            )
            if response.status_code == 200:
                upload_info = response.json()
                audio_key = upload_info["audio_key"]
                print(f"  ✅ 업로드 성공: {audio_key}")
            else:
                print(f"  ❌ 업로드 실패: {response.status_code} - {response.text}")
                return
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            return

        # 5. Job 생성 (비동기 채점 시작)
        print("\n[5/7] 채점 Job 생성...")
        try:
            job_data = {
                "audio_key": audio_key,
                "task_id": task_id
            }
            response = await client.post(
                f"{BASE_URL}/v1/jobs",
                json=job_data,
                headers=auth_headers
            )
            if response.status_code == 201:
                job_info = response.json()
                job_id = job_info["job_id"]
                print(f"  ✅ Job 생성: {job_id}")
                print(f"  초기 상태: {job_info['status']}")
            else:
                print(f"  ❌ Job 생성 실패: {response.status_code} - {response.text}")
                return
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            return

        # 6. Job 상태 폴링 (최대 60초 대기)
        print("\n[6/7] 채점 진행 상태 모니터링...")
        max_wait = 60
        start_time = time.time()
        job_done = False

        while time.time() - start_time < max_wait:
            try:
                response = await client.get(
                    f"{BASE_URL}/v1/jobs/{job_id}",
                    headers=auth_headers
                )
                if response.status_code == 200:
                    job_status = response.json()
                    status = job_status["status"]
                    progress = job_status["progress"]

                    print(f"  [{int(time.time() - start_time)}s] 상태: {status} ({progress}%)")

                    if status == "DONE":
                        job_done = True
                        print(f"  ✅ 채점 완료!")
                        break
                    elif status == "FAILED":
                        error_msg = job_status.get("error_message", "Unknown error")
                        print(f"  ❌ 채점 실패: {error_msg}")
                        return

                    await asyncio.sleep(3)
                else:
                    print(f"  ❌ 상태 조회 실패: {response.status_code}")
                    return
            except Exception as e:
                print(f"  ❌ 오류: {e}")
                return

        if not job_done:
            print(f"  ⚠️  타임아웃 ({max_wait}초 초과)")
            return

        # 7. 최종 리포트 조회
        print("\n[7/7] 최종 피드백 리포트 조회...")
        try:
            response = await client.get(
                f"{BASE_URL}/v1/jobs/{job_id}/report",
                headers=auth_headers
            )
            if response.status_code == 200:
                report_data = response.json()
                report = report_data["report"]

                print(f"\n{'=' * 70}")
                print("📊 채점 결과")
                print(f"{'=' * 70}")
                print(f"\n점수대: {report['score_band']['min']}-{report['score_band']['max']}")
                print(f"\n요약:")
                for i, line in enumerate(report['summary_3lines'], 1):
                    print(f"  {i}. {line}")

                print(f"\n주요 병목:")
                print(f"  {report['bottleneck']}")

                print(f"\n개선 액션 아이템:")
                for i, action in enumerate(report['action_items'], 1):
                    print(f"  {i}. {action}")

                print(f"\n구조 점수: {report['structure']['score']}/30")
                print(f"  강점: {', '.join(report['structure']['strengths'])}")
                print(f"  약점: {', '.join(report['structure']['weaknesses'])}")

                print(f"\n언어 점수: {report['language']['score']}/30")
                print(f"  강점: {', '.join(report['language']['strengths'])}")
                print(f"  약점: {', '.join(report['language']['weaknesses'])}")

                print(f"\n전달 점수: {report['delivery']['score']}/30")
                print(f"  강점: {', '.join(report['delivery']['strengths'])}")
                print(f"  약점: {', '.join(report['delivery']['weaknesses'])}")

                print(f"\n{'=' * 70}")
                print("✅ End-to-End 테스트 성공!")
                print(f"{'=' * 70}")
            else:
                print(f"  ❌ 리포트 조회 실패: {response.status_code} - {response.text}")
                return
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            return

if __name__ == "__main__":
    asyncio.run(test_end_to_end())
