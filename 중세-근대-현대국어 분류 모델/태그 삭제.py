import os
import re
from pathlib import Path

def clean_add_tags_from_file(file_path):
    """
    텍스트 파일에서 <add>〃</add> 태그를 삭제하는 함수
    """
    try:
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 원본 내용 저장 (변경사항 확인용)
        original_content = content
        
        # <add>〃</add> 패턴 삭제
        # 정규표현식을 사용하여 <add>로 시작하고 </add>로 끝나는 모든 태그 삭제
        cleaned_content = re.sub(r'<add>[^<]*</add>', '', content)
        
        # 변경사항이 있는 경우에만 파일 업데이트
        if original_content != cleaned_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            return True, f"정리됨: {file_path}"
        else:
            return False, f"변경사항 없음: {file_path}"
            
    except Exception as e:
        return False, f"오류 발생 {file_path}: {e}"

def clean_all_txt_files():
    """
    Dataset 폴더의 모든 txt 파일을 정리하는 함수
    """
    dataset_path = Path("Dataset")
    
    if not dataset_path.exists():
        print("Dataset 폴더가 존재하지 않습니다.")
        return
    
    # 모든 txt 파일 찾기
    txt_files = list(dataset_path.rglob("*.txt"))
    
    if not txt_files:
        print("Dataset 폴더에 txt 파일이 없습니다.")
        return
    
    print(f"총 {len(txt_files)}개의 txt 파일을 검사합니다...")
    
    cleaned_count = 0
    error_count = 0
    
    for txt_file in txt_files:
        success, message = clean_add_tags_from_file(txt_file)
        
        if success:
            cleaned_count += 1
            if cleaned_count <= 10:  # 처음 10개만 출력
                print(message)
            elif cleaned_count == 11:
                print("... (더 많은 파일들이 정리되고 있습니다)")
        else:
            if "오류" in message:
                error_count += 1
                print(message)
    
    print(f"\n=== 정리 완료 ===")
    print(f"총 파일 수: {len(txt_files)}")
    print(f"정리된 파일 수: {cleaned_count}")
    print(f"오류 발생 파일 수: {error_count}")
    print(f"변경사항 없는 파일 수: {len(txt_files) - cleaned_count - error_count}")

if __name__ == "__main__":
    clean_all_txt_files() 