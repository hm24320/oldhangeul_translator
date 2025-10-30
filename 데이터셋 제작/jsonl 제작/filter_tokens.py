import json
import tiktoken
import os

def count_tokens(text, model="gpt-4"):
    """텍스트의 토큰 수를 계산합니다."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def to_text(content):
    """message['content']가 문자열이 아닐 경우 안전하게 문자열로 변환"""
    if isinstance(content, str):
        return content
    try:
        return json.dumps(content, ensure_ascii=False)
    except Exception:
        return str(content)

def filter_jsonl_by_tokens(input_file, output_file, max_tokens=30000, model="gpt-4"):
    """
    JSONL 파일에서 assistant 또는 user 메시지의 토큰 수가 max_tokens를 넘는 줄을 제거합니다.
    
    Args:
        input_file (str): 입력 JSONL 파일 경로
        output_file (str): 출력 JSONL 파일 경로
        max_tokens (int): 최대 허용 토큰 수
        model (str): 토크나이저에 사용할 모델 이름
    """
    kept_count = 0
    total_count = 0
    removed_count = 0
    
    print(f"토큰 필터링 시작: {input_file}")
    print(f"최대 허용 토큰 수: {max_tokens}")
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        for line_num, line in enumerate(infile, 1):
            if line_num % 1000 == 0:
                print(f"처리 중... {line_num}줄")
            
            try:
                data = json.loads(line.strip())
                total_count += 1
                
                messages = data.get('messages', [])
                if not messages:
                    # messages가 없으면 그대로 유지
                    outfile.write(line)
                    kept_count += 1
                    continue
                
                remove_line = False
                # 각 메시지별로 검사 (user와 assistant 모두 검사)
                for message in messages:
                    role = message.get('role', '')
                    content = to_text(message.get('content', ''))
                    if not content:
                        continue
                    token_count = count_tokens(content, model=model)
                    
                    if token_count > max_tokens:
                        remove_line = True
                        removed_count += 1
                        if removed_count <= 10:  # 처음 10개만 상세 출력
                            print(f"제거됨 (줄 {line_num}) - role: {role}, tokens: {token_count}")
                        break  # 한 메시지 초과하면 바로 제거
                    
                if not remove_line:
                    outfile.write(line)
                    kept_count += 1
                
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 오류 (줄 {line_num}): {e}")
                continue
            except Exception as e:
                print(f"오류 (줄 {line_num}): {e}")
                continue
    
    print(f"\n필터링 완료!")
    print(f"총 처리된 줄: {total_count}")
    print(f"유지된 줄: {kept_count}")
    print(f"제거된 줄: {removed_count}")
    if total_count > 0:
        print(f"제거 비율: {removed_count/total_count*100:.2f}%")
    print(f"출력 파일: {output_file}")

if __name__ == "__main__":
    input_file = "merged.jsonl"
    output_file = "merged_filtered.jsonl"
    
    # 파일 존재 확인
    if not os.path.exists(input_file):
        print(f"입력 파일을 찾을 수 없습니다: {input_file}")
        exit(1)
    
    # 토큰 필터링 실행 (필요하면 model과 max_tokens 값 조절)
    filter_jsonl_by_tokens(input_file, output_file, max_tokens=10000, model="gpt-4")
