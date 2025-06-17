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

def extract_text_with_regex(xml_content):
    """정규표현식을 사용하여 언해와 번역문을 추출"""
    
    # 언해 텍스트 추출
    언해_pattern = r'<언해>(.*?)</언해>'
    언해_matches = re.findall(언해_pattern, xml_content, re.DOTALL)
    
    # 번역문 텍스트 추출
    번역문_pattern = r'<번역문>(.*?)</번역문>'
    번역문_matches = re.findall(번역문_pattern, xml_content, re.DOTALL)
    
    # 언해 텍스트 정리
    언해_texts = []
    for match in 언해_matches:
        # 협주와 원본위치 태그 제거
        text = re.sub(r'<협주>.*?</협주>', '', match, flags=re.DOTALL)
        text = re.sub(r'<원본위치[^>]*>.*?</원본위치>', '', text, flags=re.DOTALL)
        # 〔한문〕, 〔옮김〕 등의 마크업 제거
        text = re.sub(r'〔[^〕]*〕', '', text)
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        # 텍스트 정리
        text = clean_text(text)
        if text:
            언해_texts.append(text)
    
    # 번역문 텍스트 정리
    번역문_texts = []
    for match in 번역문_matches:
        # 협주와 원본위치 태그 제거
        text = re.sub(r'<협주>.*?</협주>', '', match, flags=re.DOTALL)
        text = re.sub(r'<원본위치[^>]*>.*?</원본위치>', '', text, flags=re.DOTALL)
        # 〔한문〕, 〔옮김〕 등의 마크업 제거
        text = re.sub(r'〔[^〕]*〕', '', text)
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        # 텍스트 정리
        text = clean_text(text)
        if text:
            번역문_texts.append(text)
    
    return 언해_texts, 번역문_texts

def extract_text_content(element):
    """XML 요소에서 순수 텍스트만 추출 (협주, 원본위치 등 제외)"""
    if element is None:
        return ""
    
    # 전체 텍스트 추출
    text_parts = []
    
    # 요소의 직접 텍스트
    if element.text:
        text_parts.append(element.text)
    
    # 자식 요소들 처리
    for child in element:
        # 협주와 원본위치는 제외
        if child.tag not in ['협주', '원본위치']:
            # 자식 요소의 텍스트 추가
            if child.text:
                text_parts.append(child.text)
        
        # 자식 요소 뒤의 tail 텍스트 추가
        if child.tail:
            text_parts.append(child.tail)
    
    # 텍스트 합치기
    full_text = ''.join(text_parts)
    
    # 〔한문〕, 〔옮김〕 등의 마크업 제거
    full_text = re.sub(r'〔[^〕]*〕', '', full_text)
    
    return clean_text(full_text)

def extract_texts_from_xml(xml_file_path):
    """XML 파일에서 언해와 번역문을 추출"""
    
    try:
        # 파일 읽기
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # 정규표현식으로 텍스트 추출 (XML 파싱이 실패할 경우 대비)
        언해_texts, 번역문_texts = extract_text_with_regex(xml_content)
        
        # XML 파싱도 시도해보기
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # 언해 텍스트 추출 (XML 파싱)
            xml_언해_texts = []
            for 언해 in root.findall('.//언해'):
                text = extract_text_content(언해)
                if text:
                    xml_언해_texts.append(text)
            
            # 번역문 텍스트 추출 (XML 파싱)
            xml_번역문_texts = []
            for 번역문 in root.findall('.//번역문'):
                text = extract_text_content(번역문)
                if text:
                    xml_번역문_texts.append(text)
            
            # XML 파싱 결과가 더 많으면 사용
            if len(xml_언해_texts) > len(언해_texts):
                언해_texts = xml_언해_texts
            if len(xml_번역문_texts) > len(번역문_texts):
                번역문_texts = xml_번역문_texts
                
        except ET.ParseError:
            print("XML 파싱 실패 - 정규표현식 결과 사용")
        
        return 언해_texts, 번역문_texts
        
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {xml_file_path}")
        return [], []
    except Exception as e:
        print(f"파일 처리 오류: {e}")
        return [], []

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
    
    print("XML 파일에서 텍스트를 추출 중...")
    
    # 텍스트 추출
    언해_texts, 번역문_texts = extract_texts_from_xml(xml_file)
    
    if not 언해_texts and not 번역문_texts:
        print("추출할 텍스트가 없습니다.")
        return
    
    # 결과 출력
    print(f"추출 완료:")
    print(f"- 언해: {len(언해_texts)}개")
    print(f"- 번역문: {len(번역문_texts)}개")
    
    # 파일로 저장
    if 언해_texts:
        save_to_txt(언해_texts, "중세국어_언해.txt")
    
    if 번역문_texts:
        save_to_txt(번역문_texts, "현대어_번역문.txt")
    
    print("\n처리 완료!")
    
    # 샘플 출력
    if 언해_texts:
        print(f"\n[언해 샘플]")
        print(f"첫 번째: {언해_texts[0][:100]}...")
    
    if 번역문_texts:
        print(f"\n[번역문 샘플]")
        print(f"첫 번째: {번역문_texts[0][:100]}...")

if __name__ == "__main__":
    main() 