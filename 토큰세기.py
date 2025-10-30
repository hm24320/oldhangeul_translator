import os
import csv
import tiktoken

def count_tokens(text: str, model_name: str = "gpt-4o-mini") -> int:
    """텍스트를 토큰 단위로 인코딩하여 토큰 수 반환"""
    encoding = tiktoken.encoding_for_model(model_name)
    return len(encoding.encode(text))

def count_tokens_in_directory(base_dir: str, model_name: str = "gpt-4o-mini", save_csv: bool = True):
    """폴더 내 모든 txt 파일의 토큰 수를 세고 출력 및 CSV 저장"""
    results = []
    encoding = tiktoken.encoding_for_model(model_name)

    for root, _, files in os.walk(base_dir):  # ✅ 모든 하위 폴더 자동 탐색
        for file in files:
            if file.lower().endswith(".txt"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()
                    token_count = len(encoding.encode(text))
                    results.append((file_path, token_count))
                except Exception as e:
                    print(f"⚠️ {file_path} 처리 중 오류 발생: {e}")

    # 결과 출력
    print(f"\n총 {len(results)}개 파일 분석 완료 ✅\n")
    total_tokens = 0
    for path, count in results:
        print(f"{path} → {count} tokens")
        total_tokens += count

    print(f"\n📊 전체 토큰 합계: {total_tokens} tokens")

    # ✅ CSV로 저장
    if save_csv and results:
        csv_path = os.path.join(base_dir, "token_counts.csv")
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["File Path", "Token Count"])
            writer.writerows(results)
        print(f"\n📂 CSV 파일로 저장 완료: {csv_path}")

if __name__ == "__main__":
    base_path = r"데이터셋 제작\한국 고문서 자료관\한국 고문서 자료관 txt"
    count_tokens_in_directory(base_path)
