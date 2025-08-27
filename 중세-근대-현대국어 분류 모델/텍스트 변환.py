import os
from pathlib import Path
from OldHangeul import hNFD

def convert_pua_to_jamo(input_file, output_file=None):
    """한양 PUA를 첫가끝 코드로 변환"""
    
    # output_file이 None이면 입력 파일을 덮어쓰기
    if output_file is None:
        output_file = input_file
    
    try:
        # 입력 파일 읽기
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        converted_lines = []
        
        for line in lines:
            if line.strip():  # 빈 줄이 아닌 경우
                # 번호 부분과 텍스트 부분 분리
                if '. ' in line:
                    parts = line.split('. ', 1)
                    if len(parts) == 2:
                        number_part = parts[0] + '. '
                        text_part = parts[1]
                        
                        # 텍스트 부분을 hNFD로 변환
                        converted_text = hNFD(text_part.strip())
                        converted_line = number_part + converted_text + '\n'
                    else:
                        # 분리가 안 되는 경우 전체를 변환
                        converted_line = hNFD(line.strip()) + '\n'
                else:
                    # 번호가 없는 경우 전체를 변환
                    converted_line = hNFD(line.strip()) + '\n'
            else:
                # 빈 줄은 그대로 유지
                converted_line = line
            
            converted_lines.append(converted_line)
        
        # 변환된 내용을 파일로 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(converted_lines)
        
        return True, None
        
    except FileNotFoundError:
        error_msg = f"파일을 찾을 수 없습니다: {input_file}"
        return False, error_msg
    except Exception as e:
        error_msg = f"변환 중 오류 발생: {e}"
        return False, error_msg

def convert_all_txt_files(directories):
    """
    지정된 디렉토리들의 모든 txt 파일을 변환하는 함수
    """
    total_files = 0
    converted_files = 0
    failed_files = []
    
    for directory in directories:
        if not os.path.exists(directory):
            print(f"경고: {directory} 디렉토리를 찾을 수 없습니다.")
            continue
        
        # 디렉토리 내 모든 txt 파일 찾기
        txt_files = list(Path(directory).glob('*.txt'))
        print(f"\n{directory} 폴더에서 {len(txt_files)}개의 txt 파일을 발견했습니다.")
        
        for txt_file in txt_files:
            total_files += 1
            success, error = convert_pua_to_jamo(txt_file)
            
            if success:
                converted_files += 1
                if converted_files % 100 == 0:  # 100개마다 진행상황 출력
                    print(f"진행상황: {converted_files}/{total_files} 파일 변환 완료")
            else:
                failed_files.append((str(txt_file), error))
                print(f"변환 실패: {txt_file.name} - {error}")
    
    return total_files, converted_files, failed_files

def main():
    """메인 함수"""
    # Dataset 폴더 내의 근대국어, 중세국어 디렉토리 경로
    dataset_directories = [
        "Dataset/근대국어",
        "Dataset/중세국어"
    ]
    
    print("Dataset 폴더 내 txt 파일들의 한양 PUA → 첫가끝 코드 변환 시작...")
    
    # 변환 실행
    total_files, converted_files, failed_files = convert_all_txt_files(dataset_directories)
    
    # 결과 출력
    print(f"\n=== 변환 결과 ===")
    print(f"총 파일 수: {total_files}")
    print(f"변환 성공: {converted_files}")
    print(f"변환 실패: {len(failed_files)}")
    
    if failed_files:
        print(f"\n=== 변환 실패 파일 목록 ===")
        for file_path, error in failed_files:
            print(f"- {file_path}: {error}")
    
    print("\n처리 완료!")

if __name__ == "__main__":
    main() 