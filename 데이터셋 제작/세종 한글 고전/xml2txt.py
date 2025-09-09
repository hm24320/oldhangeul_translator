import os
import re
import sys
from lxml import etree
## from OldHangeul import OldTexts ##

# 스크립트가 어디서 실행되든, 스크립트 파일 기준 상대 경로 사용
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(SCRIPT_DIR, "세종 한글 고전 xml")       # 원본 XML 폴더
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "세종 한글 고전 txt")    # 결과 TXT 폴더

# 입력 폴더 존재 확인 (없으면 안내 후 종료)
if not os.path.isdir(BASE_DIR):
    # 콘솔 인코딩 이슈 대비 안전 출력
    enc = (getattr(sys.stdout, "encoding", None) or "utf-8")
    msg1 = f"입력 폴더를 찾을 수 없습니다: {BASE_DIR}"
    msg2 = "실제 폴더 경로를 확인하거나 스크립트를 해당 폴더가 있는 위치에서 실행하세요."
    try:
        print(msg1)
        print(msg2)
    except UnicodeEncodeError:
        print(msg1.encode(enc, "replace").decode(enc, "replace"))
        print(msg2.encode(enc, "replace").decode(enc, "replace"))
    exit(0)

# 안전 출력 함수 (Windows cp949 콘솔 등에서의 깨짐 방지)
def safe_print(message: str) -> None:
    enc = (getattr(sys.stdout, "encoding", None) or "utf-8")
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode(enc, "replace").decode(enc, "replace"))

def extract_years(date_elements):
    """출판일 태그 여러 개에서 연도만 추출 (2000년 이상은 무시).
       '1399년(정종 원년)', '1797(정조 21년)' 같은 것도 인식"""
    years = []
    for elem in date_elements:
        if elem is None:
            continue
        text = "".join(elem.itertext())  # 태그 내부 전체 텍스트 합치기
        # '1399년', '1399년(', '1797(정조...' 모두 잡음
        for m in re.finditer(r"(\d{3,4})(?=년|\()", text):
            y = int(m.group(1))
            if y < 2000:  # 2000년 이후는 무시 - 실제 인터넷 게시일과 구별
                years.append(y)
    return years

def get_period_from_xml(root):
    """XML에서 올바른 연도를 추출하여 시기 구분"""
    출판일_elems = root.findall(".//출판일")
    years = extract_years(출판일_elems)
    if not years:
        return "중세국어"  # 혹시 없으면 기본값
    year = min(years)  # 가장 오래된 연도를 선택
    return "중세국어" if year <= 1592 else "근대국어"

def get_full_text(element):
    """태그 안의 모든 텍스트 추출 (단, <원본위치>는 태그ごと 제거)"""
    for pos in element.findall(".//원본위치"):
        parent = pos.getparent()
        if pos.tail:  # 원본위치 뒤에 붙은 실제 텍스트 보존
            prev = pos.getprevious()
            if prev is not None:
                prev.tail = (prev.tail or "") + pos.tail
            else:
                parent.text = (parent.text or "") + pos.tail
        parent.remove(pos)  # 태그 삭제

    return etree.tostring(element, method="text", encoding="utf-8").decode("utf-8").strip()

def process_xml(xml_path, rel_path):
    # 원본 읽기
    with open(xml_path, encoding="utf-8") as f:
        xml_text = f.read()

    # 잘못된 </저자정보> 중복 닫힘 태그 교정
    xml_text = re.sub(r"</저자정보>\s*<(?=(한글|한자|출판일))", "<저자정보><", xml_text)
    xml_text = re.sub(r"</저자정보>\s*~~\s*</저자정보>", "</저자정보>", xml_text)

    # xml 파싱 (교정된 것만 허용)
    parser = etree.XMLParser(recover=False)
    root = etree.fromstring(xml_text.encode("utf-8"), parser)

    # 출판연도 -> 시기 분류
    period = get_period_from_xml(root)

    본문 = root.find("본문")
    if 본문 is None:
        return

    lines_언해 = []
    lines_번역문 = []

    for 기사 in 본문.findall("기사"):
        원문들 = 기사.findall(".//원문") + 기사.findall(".//언해")
        번역문들 = 기사.findall(".//번역문")

        for 원문 in 원문들:
            text = get_full_text(원문)
            if text:
                lines_언해.append(text)

        for 번역문 in 번역문들:
            text = get_full_text(번역문)
            if text:
                lines_번역문.append(text)

    # 저장 경로 유지
    rel_path_txt = rel_path.replace(".xml", ".txt")
    txt_path_언해 = os.path.join(OUTPUT_DIR, period, "언해", rel_path_txt)
    txt_path_번역문 = os.path.join(OUTPUT_DIR, period, "번역문", rel_path_txt)

    if lines_언해:
        os.makedirs(os.path.dirname(txt_path_언해), exist_ok=True)
        with open(txt_path_언해, "w", encoding="utf-8") as f:
            f.write("\n\n".join(lines_언해))

    if lines_번역문:
        os.makedirs(os.path.dirname(txt_path_번역문), exist_ok=True)
        with open(txt_path_번역문, "w", encoding="utf-8") as f:
            f.write("\n\n".join(lines_번역문))

    safe_print(f"{rel_path} -> {period} 변환 완료")

# 전체 xml 순회 + 진행상황 표시
total_files = []
for root_dir, _, files in os.walk(BASE_DIR):
    for file in files:
        if file.endswith(".xml"):
            total_files.append(os.path.join(root_dir, file))

safe_print(f"총 {len(total_files)}개 XML 파일 처리 시작...")

for idx, xml_path in enumerate(total_files, 1):
    rel_path = os.path.relpath(xml_path, BASE_DIR)
    try:
        process_xml(xml_path, rel_path)
    except Exception as e:
        safe_print(f"오류: {xml_path} -> {e}")
    if idx % 10 == 0 or idx == len(total_files):
        safe_print(f"[진행상황] {idx}/{len(total_files)} 완료")