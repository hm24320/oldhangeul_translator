import os
import re
import time
import unicodedata
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs, quote_plus
from OldHangeul import hNFD  # [OldHangeul 적용]
from playwright.sync_api import sync_playwright

# 설정
BASE = "https://archive.aks.ac.kr"
LIST_URL = f"{BASE}/letter/list.do?itemId=letter&gubun=lettername&pageIndex=1&pageUnit=1000"


session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/S.0 (Windows NT 10.0; Win64; x64)",
    "Referer": LIST_URL,
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
})

# 폴더 구조
base_folder = "한국 고문서 자료관 txt"
folders = {
    "중세국어": {"고문서": os.path.join(base_folder, "중세국어", "고문서"),
               "번역본": os.path.join(base_folder, "중세국어", "번역본")},
    "근대국어": {"고문서": os.path.join(base_folder, "근대국어", "고문서"),
               "번역본": os.path.join(base_folder, "근대국어", "번역본")},
}
for g in folders.values():
    for p in g.values():
        os.makedirs(p, exist_ok=True)

# 구간 연도에서 가장 오래된 연도 추출
def extract_year_from_range(date_text):
    """구간 연도에서 가장 오래된 연도 추출"""
    if not date_text:
        return None
    
    # "1653년〜1659년" 형태에서 첫 번째 연도 추출
    match = re.search(r'(\d{4})년', date_text)
    if match:
        return int(match.group(1))
    return None

# 제목 정규화
def normalize_title(title: str) -> str:
    if not title:
        return "무제"
    s = unicodedata.normalize("NFKC", title)
    s = re.sub(r'[\u200B-\u200F\uFEFF]', '', s)
    s = re.sub(r'[\x00-\x1F\x7F]', '', s)
    s = ' '.join(s.split())
    s = re.sub(r'[\\/*?:"<>|]', '', s)
    return s[:150] if len(s) > 150 else s

# 중복 방지
title_counter = {}
def get_unique_title_once(norm_title: str) -> str:
    if norm_title not in title_counter:
        title_counter[norm_title] = 1
        return norm_title
    else:
        title_counter[norm_title] += 1
        return f"{norm_title}({title_counter[norm_title]})"

# 목록 수집
resp = session.get(LIST_URL, timeout=15)
resp.encoding = resp.apparent_encoding or "utf-8"
soup = BeautifulSoup(resp.text, "html.parser")
ul = soup.find("ul", class_="wrap__list")
items = []
if ul:
    for li in ul.find_all("li"):
        title_el = li.select_one("div.list__title > a")
        if not title_el:
            continue
        title_text = title_el.get_text(strip=True)
        href = title_el.get("href", "")
        if href.startswith("#"):
            href = href[1:]
        if not href.startswith("/"):
            href = "/" + href
        
        # URL 구조 수정: /view.do 대신 /letter/view.do 사용
        if "/view.do" in href:
            href = href.replace("/view.do", "/letter/view.do")
        
        link = urljoin(BASE, href)
        items.append((title_text, link))

print("수집된 항목:", len(items))


# Playwright를 사용한 연도 추출 함수
def extract_year_with_playwright(url):
    """Playwright를 사용하여 연도 정보 추출"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle")
            
            # 다양한 셀렉터로 연대 정보 찾기
            selectors_to_try = [
                "table.htable",
                "table[class*='htable']",
                "table",
                ".htable",
                "[class*='table']"
            ]
            
            for selector in selectors_to_try:
                htable = page.query_selector(selector)
                if htable:
                    rows = htable.query_selector_all("tbody tr")
                    if not rows:
                        rows = htable.query_selector_all("tr")
                    
                    for row in rows:
                        th = row.query_selector("th")
                        if th:
                            th_text = th.inner_text().strip()
                            
                            # 다양한 연대 키워드 시도
                            keywords = ["연대", "년도", "연도", "시기", "시대"]
                            for keyword in keywords:
                                if keyword in th_text:
                                    td = row.query_selector("td")
                                    if td:
                                        date_text = td.inner_text().strip()
                                        year = extract_year_from_range(date_text)
                                        if year:
                                            return year
                                    break
            
            # 대체 방법: 페이지 전체에서 연도 패턴 찾기
            page_content = page.content()
            
            year_patterns = [
                r'(\d{4})년',
                r'(\d{4})~(\d{4})',
                r'(\d{4})-(\d{4})',
                r'(\d{4})\.(\d{4})',
                r'(\d{4})\s*년',
                r'(\d{4})\s*~',
                r'(\d{4})\s*-'
            ]
            
            for pattern in year_patterns:
                matches = re.findall(pattern, page_content)
                if matches:
                    for match in matches:
                        if isinstance(match, tuple):
                            year = int(match[0])
                        else:
                            year = int(match)
                        if 1000 <= year <= 2000:  # 합리적인 연도 범위
                            return year
            
            # 제목에서 연도 추출 시도
            title_element = page.query_selector("title")
            if title_element:
                title_text = title_element.inner_text()
                title_year = extract_year_from_range(title_text)
                if title_year:
                    return title_year
            
            # h1, h2 태그에서 연도 추출 시도
            for tag in ["h1", "h2", "h3"]:
                elements = page.query_selector_all(tag)
                for element in elements:
                    text = element.inner_text().strip()
                    if text and any(keyword in text for keyword in ["년", "연대", "시기"]):
                        year = extract_year_from_range(text)
                        if year:
                            return year
                            
        except Exception as e:
            print(f"Playwright 연도 추출 오류: {e}")
        finally:
            browser.close()
    
    return None

# 상세 페이지에서 텍스트 추출
def extract_text_from_detail(url):
    # Playwright로 연도 추출
    year = extract_year_with_playwright(url)
    
    # 기존 requests 방식으로 텍스트 추출
    r = session.get(url, timeout=20)
    r.encoding = r.apparent_encoding or "utf-8"
    s = BeautifulSoup(r.text, "html.parser")

    result = {"원문": "", "번역": ""}

    candidates = [
        ("원문", ["div.org_text", "div.org-text", "div#org_text", "div[class*='org']"]),
        ("번역", ["div.trans_text", "div.trans-text", "div#trans_text", "div[class*='trans']"]),
    ]

    def clean_element(element):
        if not element:
            return
        for el_to_remove in element.select("div.comment_box, dl.jusok-dl, span.kakju_num"):
            el_to_remove.decompose()

    for key, sels in candidates:
        for sel in sels:
            el = s.select_one(sel)
            if el and el.get_text(strip=True):
                clean_element(el)
                result[key] = el.get_text(separator="\n", strip=True)
                break

    if (not result["원문"] or not result["번역"]):
        iframe = s.find("iframe")
        if iframe and iframe.get("src"):
            iframe_src = iframe["src"]
            iframe_url = urljoin(url, iframe_src)
            try:
                r2 = session.get(iframe_url, timeout=15)
                r2.encoding = r2.apparent_encoding or "utf-8"
                s2 = BeautifulSoup(r2.text, "html.parser")
                for key, sels in candidates:
                    if result[key]:
                        continue
                    for sel in sels:
                        el = s2.select_one(sel)
                        if el and el.get_text(strip=True):
                            clean_element(el)
                            result[key] = el.get_text(separator="\n", strip=True)
                            break
            except Exception:
                pass

    if (not result["원문"] or not result["번역"]):
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        data_id = qs.get("dataId", [None])[0]
        if data_id:
            for ep in ["/letter/view.do", "/letter/viewAjax.do", "/letter/contents.do"]:
                try:
                    r3 = session.get(urljoin(BASE, ep), params={"dataId": data_id},
                                     headers={"X-Requested-With": "XMLHttpRequest"}, timeout=10)
                    if r3.status_code == 200 and r3.text.strip():
                        s3 = BeautifulSoup(r3.text, "html.parser")
                        for key, sels in candidates:
                            if result[key]:
                                continue
                            for sel in sels:
                                el = s3.select_one(sel)
                                if el and el.get_text(strip=True):
                                    clean_element(el)
                                    result[key] = el.get_text(separator="\n", strip=True)
                                    break
                        if result["원문"] and result["번역"]:
                            break
                except Exception:
                    continue

    # 주석문 제거
    if "주석문" in result["원문"]:
        result["원문"] = result["원문"].split("주석문", 1)[0].strip()
    if "주석문" in result["번역"]:
        result["번역"] = result["번역"].split("주석문", 1)[0].strip()

    return result["원문"], result["번역"], year

# 메인 루프
for idx, (title, link) in enumerate(items, 1):
    try:
        norm = normalize_title(title)
        unique_base = get_unique_title_once(norm)

        original, translation, year = extract_text_from_detail(link)

        if not original and not translation:
            print(f"[{idx}/{len(items)}] '{title}' 내용 없음 — 수동 확인 필요: {link}")
            continue

        if year and year < 1592:  # 임진왜란 이전
            group = "중세국어"
            print(f"[{idx}/{len(items)}] '{title}' ({year}년) -> '{group}'로 저장")
        else:
            group = "근대국어"
            year_str = f"{year}년" if year else "연도미상"
            print(f"[{idx}/{len(items)}] '{title}' ({year_str}) -> '{group}'로 저장")

        # [OldHangeul 적용] 텍스트 정규화
        if original:
            original_converted = hNFD(original)
            path = os.path.join(folders[group]["고문서"], f"{unique_base}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(original_converted)

        if translation:
            translation_converted = hNFD(translation)
            path = os.path.join(folders[group]["번역본"], f"{unique_base}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(translation_converted)

        time.sleep(0.3)

    except Exception as e:
        print(f"[{idx}/{len(items)}] '{title}' 처리 중 오류 발생: {e}, 링크: {link}")

print("모든 작업이 완료되었습니다.")