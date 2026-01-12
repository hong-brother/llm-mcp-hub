"""
Gemini PTY POC Test
- ptyprocess를 사용하여 Gemini CLI 래핑
- Gemini CLI 설치 필요 (npm install -g @google/gemini-cli)
- OAuth 인증 완료 필요 (~/.gemini/oauth_creds.json)
"""
import asyncio
import os
import re
import shutil
import sys
from pathlib import Path


def check_gemini_cli() -> bool:
    """Gemini CLI 설치 확인"""
    print("\n=== Gemini CLI 설치 확인 ===")
    gemini_path = shutil.which("gemini")
    if gemini_path:
        print(f"[OK] Gemini CLI 발견: {gemini_path}")
        return True
    else:
        print("[FAIL] Gemini CLI가 설치되지 않았습니다.")
        print("       npm install -g @google/gemini-cli")
        return False


def check_oauth_credentials() -> bool:
    """OAuth 인증 파일 확인"""
    print("\n=== Gemini OAuth 인증 확인 ===")

    # 환경변수로 지정된 경로 확인
    auth_path = os.environ.get("GEMINI_AUTH_PATH")
    if auth_path:
        if Path(auth_path).exists():
            print(f"[OK] OAuth 파일 발견 (env): {auth_path}")
            return True
        else:
            print(f"[WARN] GEMINI_AUTH_PATH 지정됨: {auth_path}")
            print("       하지만 파일이 존재하지 않습니다.")

    # 기본 경로 확인
    default_path = Path.home() / ".gemini" / "oauth_creds.json"
    if default_path.exists():
        print(f"[OK] OAuth 파일 발견: {default_path}")
        return True

    print(f"[WARN] OAuth 파일 없음: {default_path}")
    print("       gemini 명령어로 먼저 로그인하세요.")
    return False


def test_ptyprocess_import():
    """ptyprocess import 테스트"""
    print("\n=== ptyprocess Import 테스트 ===")
    try:
        from ptyprocess import PtyProcess
        print(f"[OK] ptyprocess 패키지 import 성공")
        print(f"     - PtyProcess: {PtyProcess}")
        return True
    except ImportError as e:
        print(f"[FAIL] Import 실패: {e}")
        print("       pip install ptyprocess")
        return False


def clean_ansi(text: str) -> str:
    """ANSI escape 코드 제거"""
    ansi_pattern = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
    return ansi_pattern.sub('', text)


def sync_gemini_query(prompt: str, timeout: int = 30) -> str:
    """동기 방식 Gemini PTY 쿼리"""
    from ptyprocess import PtyProcess
    import time

    # Gemini CLI 실행 (-p: prompt 모드)
    proc = PtyProcess.spawn(
        ["gemini", "-p", prompt],
        env={**os.environ, "HOME": str(Path.home())},
        dimensions=(24, 200)  # 터미널 크기 설정
    )

    output = ""
    start_time = time.time()

    while proc.isalive():
        if time.time() - start_time > timeout:
            proc.terminate(force=True)
            raise TimeoutError(f"Gemini 응답 타임아웃 ({timeout}초)")

        try:
            chunk = proc.read(1024)
            if chunk:
                output += chunk.decode('utf-8', errors='ignore')
        except EOFError:
            break
        except Exception:
            break

    # 프로세스 종료 대기
    proc.close()

    # ANSI 코드 정리
    clean_output = clean_ansi(output)
    return clean_output.strip()


async def test_simple_query():
    """간단한 쿼리 테스트"""
    print("\n=== Gemini PTY 쿼리 테스트 ===")

    if not check_gemini_cli():
        print("[SKIP] Gemini CLI 없이 테스트를 건너뜁니다.")
        return None

    if not check_oauth_credentials():
        print("[SKIP] OAuth 인증 없이 테스트를 건너뜁니다.")
        return None

    try:
        prompt = "Say 'Hello from Gemini!' in exactly those words."
        print(f"[INFO] 프롬프트: {prompt}")

        # asyncio.to_thread로 동기 코드 래핑
        response = await asyncio.to_thread(sync_gemini_query, prompt)

        print(f"\n[OK] 응답 수신 완료")
        print(f"     응답 길이: {len(response)} chars")
        print(f"     응답 미리보기: {response[:200]}...")
        return response

    except TimeoutError as e:
        print(f"[FAIL] 타임아웃: {e}")
        return None
    except Exception as e:
        print(f"[FAIL] 쿼리 실패: {type(e).__name__}: {e}")
        return None


async def test_pty_behavior():
    """PTY 동작 테스트 (TTY 시뮬레이션 확인)"""
    print("\n=== PTY 동작 테스트 ===")

    try:
        from ptyprocess import PtyProcess

        # 간단한 명령어로 PTY 동작 확인
        proc = PtyProcess.spawn(["echo", "PTY Test"])
        output = ""

        while proc.isalive():
            try:
                output += proc.read(1024).decode()
            except EOFError:
                break

        proc.close()

        if "PTY Test" in output:
            print("[OK] PTY 정상 동작 확인")
            return True
        else:
            print(f"[WARN] PTY 출력 이상: {output}")
            return False

    except Exception as e:
        print(f"[FAIL] PTY 테스트 실패: {e}")
        return False


def main():
    """메인 테스트 실행"""
    print("=" * 50)
    print("Gemini PTY POC 테스트")
    print("=" * 50)

    results = {
        "ptyprocess_import": False,
        "pty_behavior": False,
        "gemini_cli": False,
        "oauth": False,
        "query": None,
    }

    # 1. ptyprocess import 테스트
    results["ptyprocess_import"] = test_ptyprocess_import()

    if not results["ptyprocess_import"]:
        print("\n[결과] ptyprocess import 실패 - 의존성 설치 필요")
        sys.exit(1)

    # 2. PTY 동작 테스트
    results["pty_behavior"] = asyncio.run(test_pty_behavior())

    # 3. Gemini CLI 확인
    results["gemini_cli"] = check_gemini_cli()

    # 4. OAuth 확인
    results["oauth"] = check_oauth_credentials()

    # 5. 실제 쿼리 테스트
    if results["gemini_cli"] and results["oauth"]:
        results["query"] = asyncio.run(test_simple_query())
    else:
        print("\n[SKIP] Gemini CLI 또는 OAuth 미설정으로 쿼리 테스트 건너뜀")

    # 결과 요약
    print("\n" + "=" * 50)
    print("테스트 결과 요약")
    print("=" * 50)
    print(f"  ptyprocess Import: {'PASS' if results['ptyprocess_import'] else 'FAIL'}")
    print(f"  PTY 동작:          {'PASS' if results['pty_behavior'] else 'FAIL'}")
    print(f"  Gemini CLI:        {'PASS' if results['gemini_cli'] else 'FAIL'}")
    print(f"  OAuth 인증:        {'PASS' if results['oauth'] else 'FAIL'}")
    print(f"  Gemini 쿼리:       {'PASS' if results['query'] else 'SKIP' if results['query'] is None else 'FAIL'}")

    if not results["gemini_cli"]:
        print("\n[INFO] Gemini CLI 설치:")
        print("       npm install -g @google/gemini-cli")

    if not results["oauth"]:
        print("\n[INFO] Gemini 로그인:")
        print("       gemini (처음 실행 시 브라우저 인증)")


if __name__ == "__main__":
    main()
