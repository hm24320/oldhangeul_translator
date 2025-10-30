# -*- coding: utf-8 -*-
"""
중세국어 텍스트에서 등장한 '모든 유니코드 문자'를 수집해 저장하는 스크립트
- 스캔 경로: ./데이터셋 제작2/고문서/
- 결과:
    1) unique_chars.txt  (문자만, 한 줄에 하나)
    2) unique_chars.csv  (문자, U+코드포인트, 유니코드 이름)
"""

from pathlib import Path
import unicodedata

# ===== 설정 =====
ROOT_DIR = Path("데이터셋 제작2/고문서")
GLOB_PATTERN = "**/*.txt"      # 하위 폴더 포함 모든 .txt
INCLUDE_WHITESPACE = False     # True로 바꾸면 개행/탭/공백 등도 포함
OUTPUT_TXT = "unique_chars.txt"
# 검색 대상 기호: ASCII 플러스(+), 전각 플러스(＋), 대괄호 모양 〔 〕
TARGET_SYMBOLS = {"+", "＋", "〔", "〕"}

def read_text_safely(p: Path) -> str:
    """
    파일을 최대한 안전하게 텍스트로 읽는다.
    1) utf-8-sig
    2) utf-8(errors='replace')
    3) cp949(errors='replace')
    순으로 시도.
    """
    # 1) 시도: utf-8-sig
    try:
        return p.read_text(encoding="utf-8-sig")
    except Exception:
        pass
    # 2) 시도: utf-8 with replace
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        pass
    # 3) 시도: cp949 with replace (윈도우/국내 자료 대비)
    try:
        return p.read_text(encoding="cp949", errors="replace")
    except Exception:
        # 최종 실패 시 바이너리로 읽어 utf-8로 best-effort 디코드
        data = p.read_bytes()
        return data.decode("utf-8", errors="replace")

def is_included_char(ch: str) -> bool:
    """포함 여부 판단 (공백/제어문자 제외 옵션 지원)."""
    if INCLUDE_WHITESPACE:
        return True
    # 제어 문자(General Category 'C*')와 흔한 공백 제외
    cat = unicodedata.category(ch)
    if cat.startswith("C"):  # Cc, Cf, Cs, Co, Cn (제어/서식/비지정 등)
        return False
    if ch in {"\n", "\r", "\t"}:
        return False
    return True

def collect_unique_chars(root: Path) -> set[str]:
    unique = set()
    files = sorted(root.glob(GLOB_PATTERN))
    for i, fp in enumerate(files, 1):
        try:
            text = read_text_safely(fp)
        except Exception as e:
            print(f"[WARN] 파일 읽기 실패: {fp} ({e})")
            continue
        # 지정 기호 포함 파일명 출력
        if any((sym in text) for sym in TARGET_SYMBOLS):
            print(f"[HIT] 특수기호 포함: {fp.name}")
        for ch in text:
            if is_included_char(ch):
                unique.add(ch)
        if i % 50 == 0:
            print(f"[INFO] 처리 중... {i}/{len(files)} 파일")
    return unique

def save_results(chars: set[str], out_txt: str) -> None:
    # 코드포인트 순으로 정렬
    sorted_chars = sorted(chars, key=lambda c: ord(c))

    # 1) TXT: 문자만 저장
    with open(out_txt, "w", encoding="utf-8") as f:
        for ch in sorted_chars:
            f.write(ch + "\n")

if __name__ == "__main__":
    if not ROOT_DIR.exists():
        raise SystemExit(f"[ERROR] 경로가 없습니다: {ROOT_DIR.resolve()}")

    unique_chars = collect_unique_chars(ROOT_DIR)
    print(f"[INFO] 수집된 고유 문자 수: {len(unique_chars)}")

    save_results(unique_chars, OUTPUT_TXT)
    print(f"[OK] 저장 완료 → {OUTPUT_TXT}")
