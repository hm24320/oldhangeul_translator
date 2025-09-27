import random
import json

def extract_random_sample(input_file, output_file, sample_ratio=0.1):
    """
    JSONL 파일에서 랜덤으로 샘플을 추출하여 새로운 파일에 저장
    
    Args:
        input_file (str): 입력 JSONL 파일 경로
        output_file (str): 출력 JSONL 파일 경로
        sample_ratio (float): 추출할 비율 (기본값: 0.1 = 10%)
    """
    
    # 모든 라인을 읽어서 리스트에 저장
    with open(input_file, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
    
    total_lines = len(all_lines)
    sample_size = int(total_lines * sample_ratio)
    
    print(f"전체 라인 수: {total_lines}")
    print(f"추출할 샘플 수: {sample_size}")
    
    # 랜덤으로 샘플 선택
    random.seed(42)  # 재현 가능한 결과를 위해 시드 설정
    sampled_lines = random.sample(all_lines, sample_size)
    
    # 샘플을 새로운 파일에 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in sampled_lines:
            f.write(line)
    
    print(f"샘플이 '{output_file}'에 저장되었습니다.")
    
    # 샘플의 첫 몇 줄을 확인
    print("\n샘플의 첫 3줄:")
    for i, line in enumerate(sampled_lines[:3]):
        try:
            data = json.loads(line.strip())
            print(f"라인 {i+1}: {data.get('messages', [{}])[0].get('role', 'unknown')} - {data.get('messages', [{}])[0].get('content', '')[:50]}...")
        except:
            print(f"라인 {i+1}: {line.strip()[:50]}...")

if __name__ == "__main__":
    input_file = "데이터셋 제작/jsonl 제작/merged_filtered.jsonl"
    output_file = "데이터셋 제작/jsonl 제작/merged_sample.jsonl"
    
    extract_random_sample(input_file, output_file, sample_ratio=0.1)
