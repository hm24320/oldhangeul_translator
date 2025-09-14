import os
import glob

def remove_last_angle_bracket_from_txt_files(root_dir):
    """
    지정된 디렉토리와 하위 디렉토리의 모든 txt 파일에서
    파일 마지막에 있는 '＜' 문자를 삭제합니다.
    """
    # 모든 txt 파일 찾기
    txt_files = glob.glob(os.path.join(root_dir, "**", "*.txt"), recursive=True)
    
    processed_count = 0
    modified_count = 0
    
    print(f"총 {len(txt_files)}개의 txt 파일을 찾았습니다.")
    
    for file_path in txt_files:
        try:
            # 파일 읽기
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # 파일이 비어있지 않고 마지막 문자가 '＜'인 경우
            if content and content[-1] == '＜':
                # 마지막 '＜' 문자 제거
                modified_content = content[:-1]
                
                # 파일에 다시 쓰기
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(modified_content)
                
                print(f"수정됨: {file_path}")
                modified_count += 1
            else:
                print(f"변경 없음: {file_path}")
            
            processed_count += 1
            
        except Exception as e:
            print(f"오류 발생 - {file_path}: {str(e)}")
    
    print(f"\n처리 완료!")
    print(f"총 처리된 파일: {processed_count}개")
    print(f"수정된 파일: {modified_count}개")

if __name__ == "__main__":
    # 한국 고문서 자료관 txt 폴더 경로
    target_directory = "데이터셋 제작/한국 고문서 자료관/한국 고문서 자료관 txt"
    
    if os.path.exists(target_directory):
        remove_last_angle_bracket_from_txt_files(target_directory)
    else:
        print(f"디렉토리를 찾을 수 없습니다: {target_directory}")
