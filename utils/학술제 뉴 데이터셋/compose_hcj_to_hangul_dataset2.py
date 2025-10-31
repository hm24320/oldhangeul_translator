import os
import sys
import unicodedata
from typing import Callable

# Ensure the dependency is declared and importable
try:
    from jamo import j2h  # noqa: F401  # imported to enforce dependency presence
except Exception as e:
    raise RuntimeError(
        "The 'jamo' package is required. Install with: pip install jamo"
    ) from e


def compose_text(text: str) -> str:
    # Convert compatibility jamo to canonical forms and compose
    # NFKC maps HCJ (U+3130 block) to conjoining jamo, NFC then composes to precomposed Hangul
    return unicodedata.normalize("NFC", unicodedata.normalize("NFKC", text))


def process_folder(src_dir: str, dst_dir: str, transform: Callable[[str], str]) -> None:
    for root, _, files in os.walk(src_dir):
        rel_root = os.path.relpath(root, src_dir)
        out_root = os.path.join(dst_dir, rel_root) if rel_root != "." else dst_dir
        os.makedirs(out_root, exist_ok=True)
        for filename in files:
            if not filename.lower().endswith(".txt"):
                continue
            src_path = os.path.join(root, filename)
            dst_path = os.path.join(out_root, filename)
            try:
                with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                    original = f.read()
                composed = transform(original)
                with open(dst_path, "w", encoding="utf-8", errors="ignore") as f:
                    f.write(composed)
            except Exception as e:
                print(f"[WARN] Failed to process {src_path}: {e}")


def main() -> None:
    # 파일 위치: utils/학술제 뉴 데이터셋/compose_hcj_to_hangul_dataset2.py
    # 프로젝트 루트로 가려면 3번 올라가야 함
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dataset_base = os.path.join(project_root, "데이터셋 제작2", "학술제 뉴 데이터셋")
    
    # 처리할 폴더 쌍: (소스 폴더, 대상 폴더)
    folder_pairs = [
        (os.path.join(dataset_base, "원문_치환"), os.path.join(dataset_base, "원문_완성형")),
        (os.path.join(dataset_base, "번역"), os.path.join(dataset_base, "번역_완성형"))
    ]

    for src_dir, dst_dir in folder_pairs:
        if not os.path.isdir(src_dir):
            print(f"[WARN] Not found: {src_dir}, skipping...")
            continue

        os.makedirs(dst_dir, exist_ok=True)
        print(f"[INFO] Source: {src_dir}")
        print(f"[INFO] Output: {dst_dir}")
        process_folder(src_dir, dst_dir, compose_text)
        print(f"[INFO] Completed processing: {src_dir}")
    
    print("[DONE] Hangul composition completed for all folders.")


if __name__ == "__main__":
    main()


