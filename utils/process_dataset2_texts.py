import os
import re
import sys


def remove_square_brackets_content(text: str) -> str:
    # Remove [ ... ] including content; repeat to handle multiple occurrences and nesting
    pattern = re.compile(r"\[[^\[\]]*\]", re.DOTALL)
    previous = None
    current = text
    while previous != current:
        previous = current
        current = pattern.sub("", current)
    return current


def remove_parentheses_content(text: str) -> str:
    # Remove ( ... ) including content; repeat to handle multiple occurrences and nesting
    pattern = re.compile(r"\([^()]*\)", re.DOTALL)
    previous = None
    current = text
    while previous != current:
        previous = current
        current = pattern.sub("", current)
    return current


def clean_text_common(text: str) -> str:
    # Remove 〃 symbol
    text = text.replace("〃", "")
    # Remove content within square brackets
    text = remove_square_brackets_content(text)
    # Remove tabs
    text = text.replace("\t", "")
    return text


def clean_document_text(text: str) -> str:
    cleaned = clean_text_common(text)
    # Remove empty lines
    lines = cleaned.splitlines()
    non_empty_lines = [line for line in lines if line.strip() != ""]
    return "\n".join(non_empty_lines)


def clean_translation_text(text: str) -> str:
    cleaned = clean_text_common(text)
    # Additionally remove parentheses and their content for translations
    cleaned = remove_parentheses_content(cleaned)
    # Remove empty lines first, then replace line breaks with spaces
    lines = cleaned.splitlines()
    non_empty_lines = [line for line in lines if line.strip() != ""]
    # Join with single spaces to replace all line breaks with spaces
    joined = " ".join(non_empty_lines)
    # Collapse runs of 7 or more spaces into a single space
    joined = re.sub(r" {7,}", " ", joined)
    # Replace double spaces with single space (iterate to handle longer runs)
    while "  " in joined:
        joined = joined.replace("  ", " ")
    return joined


def process_folder(folder_path: str, is_translation: bool) -> None:
    for root, _, files in os.walk(folder_path):
        for filename in files:
            if not filename.lower().endswith(".txt"):
                continue
            file_path = os.path.join(root, filename)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    original = f.read()
                cleaned = (
                    clean_translation_text(original)
                    if is_translation
                    else clean_document_text(original)
                )
                if cleaned != original:
                    with open(file_path, "w", encoding="utf-8", errors="ignore") as f:
                        f.write(cleaned)
            except Exception as e:
                print(f"[WARN] Failed to process {file_path}: {e}")


def main(base_dir: str) -> None:
    docs_dir = os.path.join(base_dir, "고문서")
    trans_dir = os.path.join(base_dir, "번역본")

    if not os.path.isdir(docs_dir):
        print(f"[ERROR] Not found: {docs_dir}")
    else:
        print(f"[INFO] Processing document folder: {docs_dir}")
        process_folder(docs_dir, is_translation=False)

    if not os.path.isdir(trans_dir):
        print(f"[ERROR] Not found: {trans_dir}")
    else:
        print(f"[INFO] Processing translation folder: {trans_dir}")
        process_folder(trans_dir, is_translation=True)


if __name__ == "__main__":
    # Default base directory is 데이터셋 제작2 in project root
    if len(sys.argv) > 1:
        base = sys.argv[1]
    else:
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "데이터셋 제작2")
    main(base)


