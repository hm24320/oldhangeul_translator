import json
import random

# 입력 파일 읽기
input_file = '통합_데이터셋.jsonl'
train_file = 'train.jsonl'
validation_file = 'validation.jsonl'

# 데이터 읽기
data = []
with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:  # 빈 줄 제외
            data.append(json.loads(line))

# 랜덤 셔플 (데이터 분포를 고르게 하기 위함)
random.seed(42)  # 재현성을 위해 시드 설정
random.shuffle(data)

# 8:2로 분할
total = len(data)
train_size = int(total * 0.8)

train_data = data[:train_size]
validation_data = data[train_size:]

# Train 데이터 저장
with open(train_file, 'w', encoding='utf-8') as f:
    for item in train_data:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

# Validation 데이터 저장
with open(validation_file, 'w', encoding='utf-8') as f:
    for item in validation_data:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

print(f"총 {total}개의 데이터를 분할했습니다.")
print(f"Train 데이터: {len(train_data)}개 ({len(train_data)/total*100:.1f}%)")
print(f"Validation 데이터: {len(validation_data)}개 ({len(validation_data)/total*100:.1f}%)")
print(f"train.jsonl과 validation.jsonl 파일이 생성되었습니다.")
