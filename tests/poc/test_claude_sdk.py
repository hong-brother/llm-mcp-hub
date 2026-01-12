"""
Claude SDK POC Test
- OAuth 토큰 기반 인증으로 Claude 구독 플랜 활용
- CLAUDE_CODE_OAUTH_TOKEN 환경변수 필요
"""
import asyncio
import os
import sys


def check_oauth_token() -> bool:
    """OAuth 토큰 환경변수 확인"""
    token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if not token:
        print("[WARN] CLAUDE_CODE_OAUTH_TOKEN 환경변수가 설정되지 않았습니다.")
        print("       토큰 없이 SDK import 테스트만 진행합니다.")
        return False
    print(f"[OK] OAuth 토큰 감지됨 (길이: {len(token)})")
    return True


def test_sdk_import():
    """SDK import 테스트"""
    print("\n=== Claude SDK Import 테스트 ===")
    try:
        from claude_code_sdk import query, ClaudeSDKError, ClaudeCodeOptions
        print("[OK] claude_code_sdk 패키지 import 성공")
        print(f"     - query 함수: {query}")
        print(f"     - ClaudeSDKError: {ClaudeSDKError}")
        print(f"     - ClaudeCodeOptions: {ClaudeCodeOptions}")
        return True
    except ImportError as e:
        print(f"[FAIL] Import 실패: {e}")
        return False


async def test_simple_query():
    """간단한 쿼리 테스트"""
    print("\n=== Claude SDK 쿼리 테스트 ===")

    if not check_oauth_token():
        print("[SKIP] OAuth 토큰 없이 쿼리 테스트를 건너뜁니다.")
        return None

    try:
        from claude_code_sdk import query, ClaudeCodeOptions

        prompt = "Say 'Hello from Claude SDK!' in exactly those words."
        print(f"[INFO] 프롬프트: {prompt}")

        options = ClaudeCodeOptions(max_turns=1)
        result = []
        async for message in query(prompt=prompt, options=options):
            result.append(str(message))
            print(f"[STREAM] {message}")

        response = "".join(result)
        print(f"\n[OK] 응답 수신 완료")
        print(f"     응답 길이: {len(response)} chars")
        return response

    except Exception as e:
        print(f"[FAIL] 쿼리 실패: {type(e).__name__}: {e}")
        return None


async def test_streaming():
    """스트리밍 응답 테스트"""
    print("\n=== Claude SDK 스트리밍 테스트 ===")

    if not check_oauth_token():
        print("[SKIP] OAuth 토큰 없이 스트리밍 테스트를 건너뜁니다.")
        return None

    try:
        from claude_code_sdk import query, ClaudeCodeOptions

        prompt = "Count from 1 to 5, one number per line."
        print(f"[INFO] 프롬프트: {prompt}")

        options = ClaudeCodeOptions(max_turns=1)
        chunk_count = 0
        async for message in query(prompt=prompt, options=options):
            chunk_count += 1
            # 스트리밍 청크 수신 확인

        print(f"[OK] 스트리밍 완료: {chunk_count}개 청크 수신")
        return chunk_count > 0

    except Exception as e:
        print(f"[FAIL] 스트리밍 실패: {type(e).__name__}: {e}")
        return None


def main():
    """메인 테스트 실행"""
    print("=" * 50)
    print("Claude SDK POC 테스트")
    print("=" * 50)

    results = {
        "import": False,
        "query": None,
        "streaming": None,
    }

    # 1. Import 테스트
    results["import"] = test_sdk_import()

    if not results["import"]:
        print("\n[결과] SDK import 실패 - 의존성 설치 필요")
        print("       pip install claude-code-sdk")
        sys.exit(1)

    # 2. 쿼리 테스트
    results["query"] = asyncio.run(test_simple_query())

    # 3. 스트리밍 테스트
    results["streaming"] = asyncio.run(test_streaming())

    # 결과 요약
    print("\n" + "=" * 50)
    print("테스트 결과 요약")
    print("=" * 50)
    print(f"  Import:    {'PASS' if results['import'] else 'FAIL'}")
    print(f"  Query:     {'PASS' if results['query'] else 'SKIP' if results['query'] is None else 'FAIL'}")
    print(f"  Streaming: {'PASS' if results['streaming'] else 'SKIP' if results['streaming'] is None else 'FAIL'}")

    if results["query"] is None:
        print("\n[INFO] 실제 API 테스트를 위해 OAuth 토큰을 설정하세요:")
        print("       export CLAUDE_CODE_OAUTH_TOKEN='your-token-here'")


if __name__ == "__main__":
    main()
