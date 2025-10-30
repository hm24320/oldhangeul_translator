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
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_base = os.path.join(project_root, "데이터셋 제작2")
    default_src = os.path.join(default_base, "고문서_치환")
    default_dst = os.path.join(default_base, "고문서_완성형")

    src_dir = sys.argv[1] if len(sys.argv) > 1 else default_src
    dst_dir = sys.argv[2] if len(sys.argv) > 2 else default_dst

    if not os.path.isdir(src_dir):
        print(f"[ERROR] Not found: {src_dir}")
        sys.exit(1)

    os.makedirs(dst_dir, exist_ok=True)
    print(f"[INFO] Source: {src_dir}")
    print(f"[INFO] Output: {dst_dir}")
    process_folder(src_dir, dst_dir, compose_text)
    print("[DONE] Hangul composition completed.")


if __name__ == "__main__":
    main()


