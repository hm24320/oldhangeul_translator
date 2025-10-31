import os
import sys


def remove_empty_lines_from_file(file_path: str) -> bool:
    """
    파일에서 빈 줄을 제거합니다.
    
    Args:
        file_path: 처리할 파일 경로
        
    Returns:
        파일이 수정되었는지 여부 (True: 수정됨, False: 수정 안 됨)
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        
        # 빈 줄이 있는지 확인
        non_empty_lines = [line for line in lines if line.strip()]
        
        # 빈 줄이 없으면 수정할 필요 없음
        if len(non_empty_lines) == len(lines):
            return False
        
        # 빈 줄을 제거한 내용으로 파일 저장
        with open(file_path, "w", encoding="utf-8", errors="ignore") as f:
            f.writelines(non_empty_lines)
        
        return True
    except Exception as e:
        print(f"[ERROR] 파일 처리 실패 {file_path}: {e}")
        return False


def process_folder(folder_path: str) -> None:
    """
    폴더 내의 모든 .txt 파일에서 빈 줄을 제거합니다.
    
    Args:
        folder_path: 처리할 폴더 경로
    """
    if not os.path.isdir(folder_path):
        print(f"[ERROR] 폴더를 찾을 수 없습니다: {folder_path}")
        return
    
    txt_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".txt")]
    
    if not txt_files:
        print(f"[INFO] {folder_path} 폴더에 .txt 파일이 없습니다.")
        return
    
    modified_count = 0
    total_count = len(txt_files)
    
    print(f"[INFO] {folder_path} 폴더 처리 중... ({total_count}개 파일)")
    
    for filename in txt_files:
        file_path = os.path.join(folder_path, filename)
        if remove_empty_lines_from_file(file_path):
            modified_count += 1
            print(f"  [수정] {filename}")
    
    print(f"[INFO] 완료: {modified_count}/{total_count}개 파일이 수정되었습니다.")


def main() -> None:
    """메인 함수"""
    # 프로젝트 루트 경로 계산 (현재 파일의 위치 기준)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    utils_dir = os.path.dirname(current_dir)
    project_root = os.path.dirname(utils_dir)
    
    # 기본 경로 설정
    base_dir = os.path.join(project_root, "데이터셋 제작2", "학술제 뉴 데이터셋")
    translation_dir = os.path.join(base_dir, "번역")
    original_dir = os.path.join(base_dir, "원문")
    
    # CLI 인자로 경로를 받을 수 있도록 (선택사항)
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
        translation_dir = os.path.join(base_dir, "번역")
        original_dir = os.path.join(base_dir, "원문")
    
    print("=" * 60)
    print("빈 줄 제거 스크립트")
    print("=" * 60)
    
    # 번역 폴더 처리
    print("\n[번역 폴더 처리]")
    process_folder(translation_dir)
    
    # 원문 폴더 처리
    print("\n[원문 폴더 처리]")
    process_folder(original_dir)
    
    print("\n" + "=" * 60)
    print("[완료] 모든 작업이 완료되었습니다.")
    print("=" * 60)


if __name__ == "__main__":
    main()

