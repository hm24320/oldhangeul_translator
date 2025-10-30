import os
import tiktoken


def count_tokens(text: str, model: str = "gpt-4") -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def read_text_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()


def scan_and_report_over_threshold(directories, threshold_tokens: int = 10000, model: str = "gpt-4") -> None:
    any_found = False
    for directory in directories:
        if not os.path.isdir(directory):
            print(f"경로가 폴더가 아닙니다: {directory}")
            continue

        for root, _, files in os.walk(directory):
            for name in files:
                if not name.lower().endswith(".txt"):
                    continue
                file_path = os.path.join(root, name)
                try:
                    text = read_text_file(file_path)
                    tokens = count_tokens(text, model=model)
                    if tokens > threshold_tokens:
                        print(f"초과: {name} ({tokens} tokens)")
                        any_found = True
                except Exception as e:
                    print(f"오류 발생: {file_path} - {e}")

    if not any_found:
        print("임계값(10000 tokens)을 초과한 파일이 없습니다.")


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gomunseo_dir = os.path.join(project_root, "데이터셋 제작2", "고문서")
    beonyeok_dir = os.path.join(project_root, "데이터셋 제작2", "번역본")
    scan_and_report_over_threshold([gomunseo_dir, beonyeok_dir], threshold_tokens=10000, model="gpt-4")


