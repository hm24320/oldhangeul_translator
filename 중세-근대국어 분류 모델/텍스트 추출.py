import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

def extract_year_from_date(date_text):
    """
    date 태그에서 연도를 추출하는 함수
    예: '1600', '1600년' -> 1600, '16XX' -> 1600, '20세기초' -> None
    """
    if not date_text:
        return None
    
    # 숫자만 추출
    numbers = re.findall(r'\d+', date_text)
    
    if not numbers:
        return None
    
    # 첫 번째 숫자가 연도일 가능성이 높음
    year_str = numbers[0]
    
    # 4자리 연도인 경우
    if len(year_str) == 4:
        return int(year_str)
    
    # 2자리 연도인 경우 (16XX 형태)
    if len(year_str) == 2:
        year = int(year_str)
        if year >= 10:  # 10세기 이후
            return year * 100  # 16 -> 1600
    
    # 3자리나 기타 경우
    if len(year_str) == 3:
        return int(year_str) * 10  # 160 -> 1600
    
    return None

def extract_korean_sentences_by_lines(xml_file_path):
    """
    XML 파일에서 한국어 문장들을 줄바꿈 기준으로 추출하는 함수
    """
    try:
        # XML 파일을 텍스트로 읽어서 줄바꿈 정보 보존
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # XML 파싱
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        # date 태그에서 연도 추출
        date_element = root.find('.//date')
        year = None
        if date_element is not None and date_element.text:
            year = extract_year_from_date(date_element.text)
        
        # XML 파일을 줄별로 분석하여 한국어 문장 그룹 추출
        lines = xml_content.split('\n')
        sentence_groups = []
        current_group = []
        
        for line in lines:
            line = line.strip()
            # sent 태그에서 lang="kor"인 것만 추출
            if '<sent' in line and 'lang="kor"' in line:
                # 태그 내용 추출
                start_tag = line.find('>')
                end_tag = line.rfind('</')
                if start_tag != -1 and end_tag != -1 and start_tag < end_tag:
                    sentence_text = line[start_tag+1:end_tag].strip()
                    if sentence_text:
                        current_group.append(sentence_text)
            elif line == '' and current_group:
                # 빈 줄을 만나면 현재 그룹을 저장하고 새 그룹 시작
                sentence_groups.append(current_group)
                current_group = []
        
        # 마지막 그룹 추가
        if current_group:
            sentence_groups.append(current_group)
        
        return year, sentence_groups
    
    except Exception as e:
        print(f"오류 in {xml_file_path}: {e}")
        return None, []

def format_sentence_groups(sentence_groups):
    """
    문장 그룹들을 텍스트 형태로 변환하는 함수
    """
    if not sentence_groups:
        return []
    
    formatted_groups = []
    for group in sentence_groups:
        if group:  # 빈 그룹 제외
            formatted_groups.append('\n'.join(group))
    
    return formatted_groups

def save_text_files(text_groups, year, filename_base):
    """
    텍스트 그룹들을 개별 텍스트 파일로 저장하는 함수
    """
    if not text_groups:
        return
    
    # 연도에 따른 폴더 결정
    if year and 900 <= year <= 1591:
        folder_path = Path("Dataset/중세국어")
    elif year and 1592 <= year <= 1894:
        folder_path = Path("Dataset/근대국어")
    else:
        print(f"연도 {year}는 처리 범위를 벗어남: {filename_base}")
        return
    
    # 폴더 생성
    folder_path.mkdir(parents=True, exist_ok=True)
    
    # 각 텍스트 그룹을 개별 파일로 저장
    for i, text_group in enumerate(text_groups, 1):
        if text_group.strip():  # 빈 그룹 제외
            txt_filename = f"{filename_base}_part{i:03d}.txt"
            txt_path = folder_path / txt_filename
            
            try:
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(text_group)
                print(f"저장됨: {txt_path}")
            except Exception as e:
                print(f"파일 저장 오류 {txt_path}: {e}")

def process_all_xml_files():
    """
    모든 XML 파일을 처리하는 메인 함수
    """
    xml_folder = Path("NIKL_Korean History Corpus_v1.0")
    
    if not xml_folder.exists():
        print(f"폴더를 찾을 수 없습니다: {xml_folder}")
        return
    
    xml_files = list(xml_folder.glob("*.xml"))
    print(f"총 {len(xml_files)}개의 XML 파일을 처리합니다.")
    
    processed_count = 0
    medieval_count = 0
    modern_count = 0
    
    for xml_file in xml_files:
        print(f"\n처리 중: {xml_file.name}")
        
        year, sentence_groups = extract_korean_sentences_by_lines(xml_file)
        
        if not sentence_groups:
            print(f"한국어 문장이 없음: {xml_file.name}")
            continue
        
        if year is None:
            print(f"연도를 추출할 수 없음: {xml_file.name}")
            continue
        
        total_sentences = sum(len(group) for group in sentence_groups)
        print(f"추출된 연도: {year}, 한국어 문장 그룹 수: {len(sentence_groups)}, 총 문장 수: {total_sentences}")
        
        # 문장 그룹들을 텍스트 형태로 변환
        text_groups = format_sentence_groups(sentence_groups)
        
        if text_groups:
            filename_base = xml_file.stem
            save_text_files(text_groups, year, filename_base)
            processed_count += 1
            
            if 900 <= year <= 1591:
                medieval_count += 1
            elif 1592 <= year <= 1894:
                modern_count += 1
    
    print(f"\n=== 처리 완료 ===")
    print(f"총 처리된 파일: {processed_count}")
    print(f"중세국어 파일: {medieval_count}")
    print(f"근대국어 파일: {modern_count}")

if __name__ == "__main__":
    process_all_xml_files() 