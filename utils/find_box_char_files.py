from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    docs_dir = root / "데이터셋 제작2" / "고문서"
    translations_dir = root / "데이터셋 제작2" / "번역본"

    if not docs_dir.exists():
        print(str(docs_dir))
        print("[ERROR] Target directory does not exist.")
        return

    matched_files = []
    for path in docs_dir.rglob("*.txt"):
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            # Fallback if BOM/encoding oddities
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                continue
        except Exception:
            continue

        if ("□" in text) or ("#" in text):
            matched_files.append(path)

    if not matched_files:
        print("[INFO] No files contain '□' or '#'.")
        return

    # Report matches
    names = sorted(p.name for p in matched_files)
    for name in names:
        print(name)

    # Delete files in 고문서 and corresponding files in 번역본 with same name
    deleted_count_docs = 0
    deleted_count_trans = 0
    for doc_path in matched_files:
        try:
            doc_path.unlink()
            deleted_count_docs += 1
        except FileNotFoundError:
            pass
        except Exception:
            pass

        if translations_dir.exists():
            trans_path = translations_dir / doc_path.name
            try:
                trans_path.unlink()
                deleted_count_trans += 1
            except FileNotFoundError:
                pass
            except Exception:
                pass

    print(f"[DELETED] docs: {deleted_count_docs}, translations: {deleted_count_trans}")


if __name__ == "__main__":
    main()


