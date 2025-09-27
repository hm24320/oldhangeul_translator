import tiktoken
import json

def count_tokens_in_jsonl(file_path):
    # Load the tiktoken encoding for GPT-4 (cl100k_base)
    encoding = tiktoken.encoding_for_model("gpt-4o-mini")
    
    total_tokens = 0
    line_count = 0
    
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line:  # Skip empty lines
                try:
                    # Parse the JSON line
                    data = json.loads(line)
                    
                    # Convert the entire JSON object to string for token counting
                    json_str = json.dumps(data, ensure_ascii=False)
                    
                    # Count tokens
                    tokens = encoding.encode(json_str)
                    token_count = len(tokens)
                    
                    total_tokens += token_count
                    line_count += 1
                    
                    # Print progress every 1000 lines
                    if line_count % 1000 == 0:
                        print(f"Processed {line_count} lines, current total tokens: {total_tokens:,}")
                        
                except json.JSONDecodeError as e:
                    print(f"Error parsing line {line_count + 1}: {e}")
                    continue
    
    return total_tokens, line_count

if __name__ == "__main__":
    file_path = "데이터셋 제작/jsonl 제작/merged_sample_10percent.jsonl"
    
    print(f"Counting tokens in {file_path}...")
    print("This may take a while for large files...")
    
    total_tokens, line_count = count_tokens_in_jsonl(file_path)
    
    print(f"\n=== Results ===")
    print(f"Total lines processed: {line_count:,}")
    print(f"Total tokens: {total_tokens:,}")
    print(f"Average tokens per line: {total_tokens / line_count:.2f}" if line_count > 0 else "No lines processed")
