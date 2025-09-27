import os
import json

def create_jsonl_file(source_lang, target_lang, source_dir, target_dir, output_filename):
    """
    지정된 소스 및 대상 디렉토리에서 파일을 읽어 JSONL 파일을 생성합니다.

    Args:
        source_lang (str): 소스 언어 (예: "근대국어").
        target_lang (str): 대상 언어 (예: "현대국어").
        source_dir (str): 소스 파일이 있는 디렉토리 경로.
        target_dir (str): 대상 파일이 있는 디렉토리 경로.
        output_filename (str): 생성될 JSONL 파일의 이름.
    """
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        # 대상 디렉토리의 모든 하위 디렉토리를 순회합니다.
        for root, _, files in os.walk(target_dir):
            for filename in files:
                if filename.endswith(".txt"):
                    target_filepath = os.path.join(root, filename)
                    
                    # 대상 디렉토리 경로에서 기본 경로를 제거하여 상대 경로를 만듭니다.
                    relative_path = os.path.relpath(target_filepath, target_dir)
                    source_filepath = os.path.join(source_dir, relative_path)

                    if os.path.exists(source_filepath):
                        try:
                            with open(source_filepath, 'r', encoding='utf-8') as f:
                                source_content = f.read().strip()
                            with open(target_filepath, 'r', encoding='utf-8') as f:
                                target_content = f.read().strip()
                            
                            # JSON 객체 생성
                            data = {
                                "messages": [
                                    {"role": "system", "content": f"사용자의 입력을 {source_lang}에서 {target_lang}로 번역해줘."},
                                    {"role": "user", "content": source_content},
                                    {"role": "assistant", "content": target_content}
                                ]
                            }
                            # JSONL 파일에 기록
                            outfile.write(json.dumps(data, ensure_ascii=False) + '\n')
                        except Exception as e:
                            print(f"파일 처리 중 오류 발생: {source_filepath}, {target_filepath} - {e}")

# 기본 경로 설정 (사용자 환경에 맞게 수정 필요)
base_path = r"C:\USERS\SAMSUNG\DESKTOP\한민고\1. 진행중\학술제\OLDHANGEUL_TRANSLATOR\데이터셋 제작\세종 한글 고전\세종 한글 고전 txt"

# 각 언어별 디렉토리 경로 설정
geundae_eonhae_dir = os.path.join(base_path, "근대국어", "언해")
geundae_beonyeok_dir = os.path.join(base_path, "근대국어", "번역문")
jungse_eonhae_dir = os.path.join(base_path, "중세국어", "언해")
jungse_beonyeok_dir = os.path.join(base_path, "중세국어", "번역문")

# 1. 근대국어 -> 현대국어
create_jsonl_file("근대국어", "현대국어", geundae_eonhae_dir, geundae_beonyeok_dir, "근대_현대.jsonl")
print("근대국어 -> 현대국어 JSONL 파일 생성 완료!")

# 2. 현대국어 -> 중세국어
create_jsonl_file("현대국어", "중세국어", jungse_beonyeok_dir, jungse_eonhae_dir, "현대_중세.jsonl")
print("현대국어 -> 중세국어 JSONL 파일 생성 완료!")

# 3. 중세국어 -> 현대국어
create_jsonl_file("중세국어", "현대국어", jungse_eonhae_dir, jungse_beonyeok_dir, "중세_현대.jsonl")
print("중세국어 -> 현대국어 JSONL 파일 생성 완료!")

# 4. 현대국어 -> 근대국어
create_jsonl_file("현대국어", "근대국어", geundae_beonyeok_dir, geundae_eonhae_dir, "현대_근대.jsonl")
print("현대국어 -> 근대국어 JSONL 파일 생성 완료!")