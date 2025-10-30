import csv
import os
import sys
from typing import Dict


def load_mapping(csv_path: str) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        if "old_char" not in reader.fieldnames or "mapped_char" not in reader.fieldnames:
            raise ValueError("CSV must have headers: old_char,mapped_char")
        for row in reader:
            old = row["old_char"].strip()
            new = row["mapped_char"].strip()
            if not old:
                continue
            mapping[old] = new
    return mapping


def replace_text(text: str, mapping: Dict[str, str]) -> str:
    # Per-codepoint replacement using the mapping
    # Avoid str.translate because keys are not ord-int mapped consistently for non-BMP in all envs
    return "".join(mapping.get(ch, ch) for ch in text)


def process_documents_folder(docs_dir: str, out_dir: str, mapping: Dict[str, str]) -> None:
    for root, _, files in os.walk(docs_dir):
        rel_root = os.path.relpath(root, docs_dir)
        target_root = os.path.join(out_dir, rel_root) if rel_root != "." else out_dir
        os.makedirs(target_root, exist_ok=True)

        for filename in files:
            if not filename.lower().endswith(".txt"):
                continue
            src_path = os.path.join(root, filename)
            dst_path = os.path.join(target_root, filename)
            try:
                with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                    original = f.read()
                replaced = replace_text(original, mapping)
                with open(dst_path, "w", encoding="utf-8", errors="ignore") as f:
                    f.write(replaced)
            except Exception as e:
                print(f"[WARN] Failed to process {src_path}: {e}")


def main() -> None:
    # Project root inferred from this file location
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Defaults
    default_base_dir = os.path.join(project_root, "데이터셋 제작2")
    default_docs_dir = os.path.join(default_base_dir, "고문서")
    default_out_dir = os.path.join(default_base_dir, "고문서_치환")
    default_map_path = os.path.join(project_root, "map", "combined_old_mapped.csv")

    # CLI args: [docs_dir] [out_dir] [map_csv]
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else default_docs_dir
    out_dir = sys.argv[2] if len(sys.argv) > 2 else default_out_dir
    map_path = sys.argv[3] if len(sys.argv) > 3 else default_map_path

    if not os.path.isfile(map_path):
        print(f"[ERROR] Mapping CSV not found: {map_path}")
        sys.exit(1)
    if not os.path.isdir(docs_dir):
        print(f"[ERROR] Documents folder not found: {docs_dir}")
        sys.exit(1)

    print(f"[INFO] Loading mapping: {map_path}")
    mapping = load_mapping(map_path)
    print(f"[INFO] Mapping entries: {len(mapping)}")

    print(f"[INFO] Processing docs: {docs_dir}")
    print(f"[INFO] Output folder: {out_dir}")
    os.makedirs(out_dir, exist_ok=True)
    process_documents_folder(docs_dir, out_dir, mapping)
    print("[DONE] Replacement completed.")


if __name__ == "__main__":
    main()


