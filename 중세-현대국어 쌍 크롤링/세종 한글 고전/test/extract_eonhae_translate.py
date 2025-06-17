import xml.etree.ElementTree as ET
import re
import os

def clean_text(text):
    """텍스트에서 불필요한 공백과 줄바꿈을 정리"""
    if not text:
        return ""
    
    # 여러 공백을 하나로 통합
    text = re.sub(r'\s+', ' ', text)
    # 앞뒤 공백 제거
    text = text.strip()
    return text

def extract_eonhae_translate_with_regex(xml_content):
    """정규표현식을 사용하여 언해 태그 안의 옮김 뒤 문자들 추출"""
    
    # 언해 태그 전체 추출
    언해_pattern = r'<언해>(.*?)</언해>'
    언해_matches = re.findall(언해_pattern, xml_content, re.DOTALL)
    
    # 옮김 뒤 문자들 추출
    옮김_texts = []
    for match in 언해_matches:
        # 〔옮김〕 뒤의 텍스트를 찾는 패턴
        옮김_pattern = r'〔옮김〕(.*?)(?=</언해>|$)'
        옮김_match = re.search(옮김_pattern, match, re.DOTALL)
        
        if 옮김_match:
            text = 옮김_match.group(1)
            # 협주와 원본위치 태그 제거
            text = re.sub(r'<협주>.*?</협주>', '', text, flags=re.DOTALL)
            text = re.sub(r'<원본위치[^>]*>.*?</원본위치>', '', text, flags=re.DOTALL)
            # 다른 마크업 제거 (〔한문〕 등)
            text = re.sub(r'〔[^〕]*〕', '', text)
            # HTML 태그 제거
            text = re.sub(r'<[^>]+>', '', text)
            # 텍스트 정리
            text = clean_text(text)
            if text:
                옮김_texts.append(text)
    
    return 옮김_texts

def extract_eonhae_translate_from_xml(xml_file_path):
    """XML 파일에서 언해 태그 안의 옮김 뒤 문자들 추출"""
    
    try:
        # 파일 읽기
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # 정규표현식으로 텍스트 추출
        옮김_texts = extract_eonhae_translate_with_regex(xml_content)
        
        return 옮김_texts
        
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {xml_file_path}")
        return []
    except Exception as e:
        print(f"파일 처리 오류: {e}")
        return []

def save_to_txt(texts, filename):
    """텍스트 리스트를 파일로 저장"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for i, text in enumerate(texts, 1):
                f.write(f"{i:03d}. {text}\n\n")
        print(f"저장 완료: {filename} ({len(texts)}개 항목)")
    except Exception as e:
        print(f"파일 저장 오류 ({filename}): {e}")

def main():
    """메인 함수"""
    # XML 파일 경로
    xml_file = "역주월인석보-세종어제훈민정음.xml"
    
    # 파일 존재 확인
    if not os.path.exists(xml_file):
        print(f"파일이 존재하지 않습니다: {xml_file}")
        return
    
    print("XML 파일에서 언해 태그 안의 '옮김' 뒤 문자들을 추출 중...")
    
    # 텍스트 추출
    옮김_texts = extract_eonhae_translate_from_xml(xml_file)
    
    if not 옮김_texts:
        print("추출할 텍스트가 없습니다.")
        return
    
    # 결과 출력
    print(f"추출 완료: {len(옮김_texts)}개의 옮김 텍스트")
    
    # 파일로 저장
    save_to_txt(옮김_texts, "언해_옮김_추출.txt")
    
    print("\n처리 완료!")
    
    # 샘플 출력
    print(f"\n[옮김 텍스트 샘플]")
    for i, text in enumerate(옮김_texts[:5], 1):  # 처음 5개만 보여주기
        print(f"{i}. {text[:50]}...")
    
    if len(옮김_texts) > 5:
        print(f"... 외 {len(옮김_texts) - 5}개 더")

if __name__ == "__main__":
    main() 