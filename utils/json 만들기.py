import os
import json

def create_jsonl_file_by_filename(source_lang, target_lang, source_dir, target_dir, outfile):
    """
    지정된 소스 및 대상 디렉토리에서 동일한 파일명의 텍스트 파일을 찾아 JSONL 파일에 추가합니다.

    Args:
        source_lang (str): 소스 언어 (예: "근대국어").
        target_lang (str): 대상 언어 (예: "현대국어").
        source_dir (str): 소스 파일이 있는 디렉토리 경로.
        target_dir (str): 대상 파일이 있는 디렉토리 경로.
        outfile: 열려있는 파일 객체.
    
    Returns:
        int: 매칭된 파일 수.
    """
    # 소스 디렉토리에서 모든 .txt 파일의 파일명을 수집합니다.
    source_files = {}
    for root, _, files in os.walk(source_dir):
        for filename in files:
            if filename.endswith(".txt"):
                filepath = os.path.join(root, filename)
                # 파일명을 키로 사용 (중복 시 첫 번째 경로 사용)
                if filename not in source_files:
                    source_files[filename] = filepath
    
    # 대상 디렉토리에서 모든 .txt 파일을 찾아 소스와 매칭합니다.
    matched_count = 0
    for root, _, files in os.walk(target_dir):
        for filename in files:
            if filename.endswith(".txt"):
                target_filepath = os.path.join(root, filename)
                
                # 동일한 파일명이 소스 디렉토리에 있는지 확인
                if filename in source_files:
                    source_filepath = source_files[filename]
                    
                    try:
                        with open(source_filepath, 'r', encoding='utf-8') as f:
                            source_content = f.read().strip()
                        with open(target_filepath, 'r', encoding='utf-8') as f:
                            target_content = f.read().strip()
                        
                        # 빈 내용은 건너뜁니다.
                        if not source_content or not target_content:
                            continue
                        
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
                        matched_count += 1
                    except Exception as e:
                        print(f"파일 처리 중 오류 발생: {source_filepath}, {target_filepath} - {e}")
    
    return matched_count

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

# 현재 스크립트의 디렉토리 경로
script_dir = os.path.dirname(os.path.abspath(__file__))
dataset2_dir = os.path.join(script_dir, "..", "데이터셋 제작2")

# 하나의 JSONL 파일에 모든 데이터를 기록
output_filename = "통합_데이터셋.jsonl"
total_matched = 0

with open(output_filename, 'w', encoding='utf-8') as outfile:
    # 1. 고문서_완성형과 번역본_완성형 매칭
    gomyunsoe_source_dir = os.path.join(dataset2_dir, "고문서_완성형")
    beonyeokbon_target_dir = os.path.join(dataset2_dir, "번역본_완성형")
    count1 = create_jsonl_file_by_filename("중세국어", "현대국어", gomyunsoe_source_dir, beonyeokbon_target_dir, outfile)
    total_matched += count1
    print(f"고문서_완성형 매칭 완료: {count1}개 파일")
    
    # 2. 학술제 뉴 데이터셋/원문_완성형과 학술제 뉴 데이터셋/번역_완성형 매칭
    hakseolje_source_dir = os.path.join(dataset2_dir, "학술제 뉴 데이터셋", "원문_완성형")
    hakseolje_target_dir = os.path.join(dataset2_dir, "학술제 뉴 데이터셋", "번역_완성형")
    count2 = create_jsonl_file_by_filename("중세국어", "현대국어", hakseolje_source_dir, hakseolje_target_dir, outfile)
    total_matched += count2
    print(f"학술제 뉴 데이터셋 매칭 완료: {count2}개 파일")

print(f"\n{output_filename} 생성 완료! 총 매칭된 파일 수: {total_matched}")