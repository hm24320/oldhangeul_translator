import requests
from bs4 import BeautifulSoup
import os
import re
import time
import urllib.parse
from pathlib import Path
from playwright.sync_api import sync_playwright
import shutil

class SejongClassicCrawler:
    def __init__(self, base_url="http://db.sejongkorea.org", download_dir="세종 한글 고전"):
        self.base_url = base_url
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        
        # 다운로드 추적 파일 경로 설정 (코드와 같은 디렉토리)
        self.downloaded_classics_file = Path(__file__).parent / "downloaded_classic.txt"
        
        # 요청 헤더 설정 (BeautifulSoup용)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Playwright 초기화
        self.playwright = None
        self.browser = None
        self.page = None
        self.temp_download_dir = Path("temp_downloads")
        self.temp_download_dir.mkdir(exist_ok=True)
    
    def get_soup(self, url, retries=3):
        """URL에서 BeautifulSoup 객체를 반환합니다."""
        # URL 유효성 검사
        if not url or not url.startswith('http'):
            print(f"Invalid URL format: {url}")
            return None
        
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                response.encoding = 'utf-8'
                return BeautifulSoup(response.text, 'html.parser')
            except requests.exceptions.MissingSchema as e:
                print(f"URL format error for {url}: {e}")
                return None
            except requests.exceptions.RequestException as e:
                print(f"Request error for {url} (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # 지수적 백오프
                else:
                    return None
            except Exception as e:
                print(f"Unexpected error fetching {url} (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # 지수적 백오프
                else:
                    return None
    
    def start_browser(self):
        """Playwright 브라우저를 빠르게 시작합니다."""
        if self.playwright is None:
            self.playwright = sync_playwright().start()
            
            # 최적화된 브라우저 옵션
            browser_options = {
                'headless': True,
                'args': [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-images',  # 이미지 로딩 비활성화
                    '--disable-plugins',
                    '--disable-extensions'
                ]
            }
            
            self.browser = self.playwright.chromium.launch(**browser_options)
            
            # 빠른 컨텍스트 생성
            context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                accept_downloads=True,
                ignore_https_errors=True  # SSL 오류 무시
            )
            
            self.page = context.new_page()
            
            # 타임아웃 단축
            self.page.set_default_timeout(30000)
            
            # 다이얼로그 자동 처리 (간소화)
            self.page.on("dialog", lambda dialog: dialog.accept())
    
    def close_browser(self):
        """Playwright 브라우저를 종료합니다."""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            print(f"브라우저 종료 중 오류 발생: {e}")
        
        # 임시 다운로드 폴더 정리
        if self.temp_download_dir.exists():
            shutil.rmtree(self.temp_download_dir, ignore_errors=True)
    
    def sanitize_filename(self, filename):
        """파일명에서 특수문자를 제거합니다."""
        return re.sub(r'[<>:"/\\|?*]', '_', filename).strip()
    
    def load_downloaded_classics(self):
        """이미 다운로드된 고전 목록을 파일에서 읽어옵니다."""
        try:
            if self.downloaded_classics_file.exists():
                with open(self.downloaded_classics_file, 'r', encoding='utf-8') as f:
                    downloaded = set()
                    for line in f:
                        title = line.strip()
                        if title:  # 빈 줄 제외
                            downloaded.add(title)
                    return downloaded
            else:
                # 파일이 없으면 빈 집합 반환하고 파일 생성
                self.downloaded_classics_file.touch()
                return set()
        except Exception as e:
            print(f"다운로드 기록 파일 읽기 오류: {e}")
            return set()
    
    def save_downloaded_classic(self, title):
        """다운로드 완료된 고전의 제목을 파일에 저장합니다."""
        try:
            # 중복 방지를 위해 기존 목록 확인
            downloaded = self.load_downloaded_classics()
            if title not in downloaded:
                with open(self.downloaded_classics_file, 'a', encoding='utf-8') as f:
                    f.write(f"{title}\n")
                print(f"  📝 다운로드 완료 기록: {title}")
            return True
        except Exception as e:
            print(f"다운로드 기록 저장 오류: {e}")
            return False
    
    def get_main_links(self):
        """메인 페이지에서 모든 고전 링크를 추출합니다."""
        main_url = f"{self.base_url}/front/chron.do?type=db&currentPage=1&recordsPerPage=100&cate=table"
        print(f"메인 페이지에서 링크 추출 중: {main_url}")
        
        # 이미 다운로드된 고전 목록 로드
        downloaded_classics = self.load_downloaded_classics()
        if downloaded_classics:
            print(f"이미 다운로드된 고전 {len(downloaded_classics)}개를 제외합니다.")
            for classic in list(downloaded_classics)[:5]:  # 처음 5개만 표시
                print(f"  - {classic}")
            if len(downloaded_classics) > 5:
                print(f"  ... 외 {len(downloaded_classics) - 5}개")
        
        soup = self.get_soup(main_url)
        if not soup:
            print("메인 페이지를 가져올 수 없습니다.")
            return []
        
        links = []
        skipped_count = 0
        
        # 테이블에서 고전 링크들 추출
        # 테이블의 tbody 안에서 두 번째 열(내용 열)에 있는 링크들을 찾기
        table = soup.find('table')
        if table:
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:  # 최소 2개 열이 있어야 함
                        # 두 번째 열(내용 열)에서 링크 찾기
                        content_cell = cells[1]
                        link = content_cell.find('a', href=True)
                        
                        if link:
                            href = link.get('href')
                            title = link.get_text(strip=True)
                            
                            # booklist.do 또는 contentlist.do 링크만 처리
                            if href and ('booklist.do' in href or 'contentlist.do' in href):
                                # 이미 다운로드된 고전인지 확인
                                if title in downloaded_classics:
                                    print(f"  건너뜀: {title} (이미 다운로드됨)")
                                    skipped_count += 1
                                    continue
                                
                                # URL 변환 개선
                                if href.startswith('/'):
                                    href = self.base_url + href
                                elif not href.startswith('http'):
                                    href = self.base_url + '/front/' + href
                                
                                link_type = self.determine_link_type(href)
                                links.append({
                                    'title': title,
                                    'url': href,
                                    'type': link_type
                                })
                                print(f"  발견: {title} ({link_type})")
        
        print(f"총 {len(links)}개의 새로운 고전 링크를 찾았습니다. ({skipped_count}개 제외)")
        return links
    
    def determine_link_type(self, url):
        """빠르게 링크 타입을 결정합니다."""
        try:
            # 빠른 접속으로 리다이렉트 후 최종 URL 확인
            response = self.session.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            
            final_url = response.url
            
            # 최종 URL로 타입 판별
            if 'contentlist.do' in final_url:
                return 'contentlist'
            elif 'booklist.do' in final_url:
                return 'booklist'
            else:
                # 페이지 내용으로 빠른 판별
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                
                if soup.find('ul', class_='dep_01'):
                    return 'contentlist'
                elif soup.find('table', class_='bookListTable'):
                    return 'booklist'
                else:
                    return 'unknown'
                    
        except Exception as e:
            # 오류 시 기본 판별
            if 'contentlist.do' in url:
                return 'contentlist'
            elif 'booklist.do' in url:
                return 'booklist'
            else:
                return 'unknown'
    
    def get_detail_links_from_contentlist(self, url):
        """contentlist 페이지에서 detail 링크들을 추출합니다."""
        soup = self.get_soup(url)
        if not soup:
            return []
        
        detail_links = []
        
        # <ul class="dep_01"> 안의 가장 자식 <ul> 태그들을 찾기
        dep_01_lists = soup.find_all('ul', class_='dep_01')
        
        for dep_01 in dep_01_lists:
            # 가장 깊은 레벨의 ul 태그들 찾기
            nested_uls = dep_01.find_all('ul')
            
            for ul in nested_uls:
                # 더 이상 중첩된 ul이 없는 경우만 처리
                if not ul.find('ul'):
                    li_elements = ul.find_all('li')
                    for li in li_elements:
                        link = li.find('a', href=True)
                        if link and 'detail.do' in link['href']:
                            detail_url = link['href']
                            # URL 변환 개선
                            if detail_url.startswith('/'):
                                detail_url = self.base_url + detail_url
                            elif not detail_url.startswith('http'):
                                detail_url = self.base_url + '/front/' + detail_url
                            
                            detail_links.append({
                                'title': link.get_text(strip=True),
                                'url': detail_url
                            })
        
        return detail_links
    
    def get_detail_links_from_booklist(self, url):
        """booklist 페이지에서 contentlist 링크들을 먼저 찾고, 그 다음 detail 링크들을 추출합니다."""
        soup = self.get_soup(url)
        if not soup:
            return []
        
        detail_links = []
        contentlist_found = False
        
        # <table class="bookListTable"> 안의 <tbody> 에서 링크들 찾기
        table = soup.find('table', class_='bookListTable')
        if table:
            tbody = table.find('tbody')
            if tbody:
                links = tbody.find_all('a', href=True)
                
                for link in links:
                    href = link['href']
                    # URL 변환 개선
                    if href.startswith('/'):
                        href = self.base_url + href
                    elif not href.startswith('http'):
                        href = self.base_url + '/front/' + href
                    
                    # contentlist 링크인 경우 재귀적으로 detail 링크들 추출
                    if 'contentlist.do' in href:
                        contentlist_found = True
                        print(f"  권별 페이지에서 상세 링크 추출 중: {link.get_text(strip=True)}")
                        sub_details = self.get_detail_links_from_contentlist(href)
                        detail_links.extend(sub_details)
                
                # contentlist 링크가 없는 경우, 직접 detail 링크 찾기
                if not contentlist_found:
                    print("  contentlist 링크가 없음. 직접 detail 링크 검색 중...")
                    for link in links:
                        href = link['href']
                        # URL 변환 개선
                        if href.startswith('/'):
                            href = self.base_url + href
                        elif not href.startswith('http'):
                            href = self.base_url + '/front/' + href
                        
                        # detail 링크인 경우 직접 추가
                        if 'detail.do' in href:
                            detail_links.append({
                                'title': link.get_text(strip=True),
                                'url': href
                            })
        
        return detail_links
    
    def download_xml_from_detail(self, detail_url, save_dir, filename_prefix=""):
        """detail 페이지에서 XML 파일을 빠르게 다운로드합니다."""
        function_start = time.time()
        try:
            # 브라우저가 시작되지 않았으면 시작
            if self.page is None:
                self.start_browser()
            
            # 저장 디렉토리 생성
            save_dir = Path(save_dir)
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 페이지 로딩 (대기 시간 단축)
            page_load_start = time.time()
            self.page.goto(detail_url, wait_until='domcontentloaded', timeout=30000)
            page_load_time = time.time() - page_load_start
            print(f"    ⏱️ 페이지 로딩: {page_load_time:.2f}초")
            
            sleep_start = time.time()
            time.sleep(1)  # 최소 대기
            sleep_time = time.time() - sleep_start
            print(f"    ⏱️ 페이지 안정화 대기: {sleep_time:.2f}초")
            
            # 다운로드 버튼 찾기 (핵심 셀렉터만 사용)
            button_search_start = time.time()
            download_selectors = [
                'a.btn_down',
                'a[class*="btn_down"]',
                'a[href*="down"]',
                '.btn_down'
            ]
            
            download_element = None
            for selector in download_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible():
                        download_element = element
                        break
                except:
                    continue
            button_search_time = time.time() - button_search_start
            print(f"    ⏱️ 다운로드 버튼 찾기: {button_search_time:.2f}초")
            
            if not download_element:
                function_time = time.time() - function_start
                print(f"    ❌ 다운로드 버튼 없음: {detail_url}")
                print(f"    ⏱️ 전체 처리 시간: {function_time:.2f}초")
                return False
            
            # 다운로드 실행
            try:
                download_start = time.time()
                with self.page.expect_download(timeout=30000) as download_info:
                    download_element.click()
                    dialog_wait_start = time.time()
                    time.sleep(1)  # 다이얼로그 대기 시간 단축
                    dialog_wait_time = time.time() - dialog_wait_start
                    print(f"    ⏱️ 다이얼로그 대기: {dialog_wait_time:.2f}초")
                
                download = download_info.value
                download_time = time.time() - download_start
                print(f"    ⏱️ 파일 다운로드: {download_time:.2f}초")
                
            except Exception as e:
                # 대안: 직접 링크 접근
                try:
                    alternative_start = time.time()
                    href = download_element.get_attribute('href')
                    if href:
                        if href.startswith('/'):
                            href = self.base_url + href
                        
                        new_page = self.page.context.new_page()
                        with new_page.expect_download(timeout=30000) as download_info:
                            new_page.goto(href)
                        download = download_info.value
                        new_page.close()
                    else:
                        function_time = time.time() - function_start
                        print(f"    ⏱️ 전체 처리 시간: {function_time:.2f}초")
                        return False
                    alternative_time = time.time() - alternative_start
                    print(f"    ⏱️ 대안 다운로드 방법: {alternative_time:.2f}초")
                except:
                    function_time = time.time() - function_start
                    print(f"    ⏱️ 전체 처리 시간: {function_time:.2f}초")
                    return False
            
            # 파일명 설정
            filename_start = time.time()
            try:
                filename = self.sanitize_filename(download.suggested_filename)
            except:
                # 백업 파일명
                url_parts = urllib.parse.urlparse(detail_url)
                query_params = urllib.parse.parse_qs(url_parts.query)
                record_id = query_params.get('recordId', ['unknown'])[0]
                filename = f"{filename_prefix}_{record_id}.xml" if filename_prefix else f"{record_id}.xml"
                filename = self.sanitize_filename(filename)
            filename_time = time.time() - filename_start
            print(f"    ⏱️ 파일명 설정: {filename_time:.2f}초")
            
            # 파일 저장
            save_start = time.time()
            final_path = save_dir / filename
            download.save_as(final_path)
            save_time = time.time() - save_start
            print(f"    ⏱️ 파일 저장: {save_time:.2f}초")
            
            save_wait_start = time.time()
            time.sleep(0.5)  # 저장 대기 시간 단축
            save_wait_time = time.time() - save_wait_start
            print(f"    ⏱️ 저장 완료 대기: {save_wait_time:.2f}초")
            
            # 저장 성공 확인
            if final_path.exists() and final_path.stat().st_size > 0:
                file_size = final_path.stat().st_size
                function_time = time.time() - function_start
                print(f"    ✅ 저장 완료: {filename} ({file_size} bytes)")
                print(f"    ⏱️ 전체 다운로드 시간: {function_time:.2f}초")
                return True
            else:
                # 대안: 직접 복사
                try:
                    alternative_save_start = time.time()
                    download_path = Path(download.path())
                    if download_path.exists():
                        shutil.copy2(download_path, final_path)
                        if final_path.exists() and final_path.stat().st_size > 0:
                            alternative_save_time = time.time() - alternative_save_start
                            print(f"    ⏱️ 대안 저장 방법: {alternative_save_time:.2f}초")
                            function_time = time.time() - function_start
                            print(f"    ✅ 저장 완료: {filename}")
                            print(f"    ⏱️ 전체 다운로드 시간: {function_time:.2f}초")
                            return True
                except:
                    pass
                
                function_time = time.time() - function_start
                print(f"    ❌ 저장 실패: {filename}")
                print(f"    ⏱️ 전체 처리 시간: {function_time:.2f}초")
                return False
            
        except Exception as e:
            function_time = time.time() - function_start
            print(f"    ❌ 다운로드 실패: {e}")
            print(f"    ⏱️ 전체 처리 시간: {function_time:.2f}초")
            return False
    
    def crawl_classic(self, classic_info):
        """개별 고전을 크롤링합니다."""
        title = classic_info['title']
        url = classic_info['url']
        link_type = classic_info['type']
        
        print(f"\n고전 크롤링 시작: {title}")
        print(f"URL: {url}")
        print(f"타입: {link_type}")
        
        # 폴더 생성
        safe_title = self.sanitize_filename(title)
        classic_dir = self.download_dir / safe_title
        classic_dir.mkdir(exist_ok=True)
        
        # 링크 타입에 따라 detail 링크들 추출
        detail_links = []
        
        if link_type == 'contentlist':
            detail_links = self.get_detail_links_from_contentlist(url)
        elif link_type == 'booklist':
            detail_links = self.get_detail_links_from_booklist(url)
        
        print(f"  {len(detail_links)}개의 상세 페이지를 찾았습니다.")
        
        if len(detail_links) == 0:
            print(f"  경고: '{title}' 고전에서 상세 페이지를 찾을 수 없습니다.")
            print(f"  페이지 구조를 확인하세요: {url}")
        
        # XML 파일들 다운로드
        success_count = 0
        for i, detail in enumerate(detail_links, 1):
            print(f"  [{i}/{len(detail_links)}] {detail['title']} 다운로드 중...")
            
            # URL 유효성 검사
            if not detail.get('url') or not detail['url'].startswith('http'):
                print(f"    잘못된 URL 형식: {detail.get('url', 'None')}")
                continue
            
            if self.download_xml_from_detail(detail['url'], classic_dir, safe_title):
                success_count += 1
            
            # 서버 부하 방지를 위한 최소 딜레이
            time.sleep(0.5)
        
        print(f"고전 '{title}' 크롤링 완료: {success_count}/{len(detail_links)} 파일 다운로드")
        
        # 다운로드 완료 기록 (모든 파일이 성공적으로 다운로드된 경우 또는 detail 링크가 없는 경우)
        if len(detail_links) == 0:
            print(f"  ⚠️ '{title}' 고전에 다운로드할 파일이 없습니다.")
            # detail 링크가 없는 경우도 완료로 기록 (재시도 방지)
            self.save_downloaded_classic(title)
        elif success_count == len(detail_links):
            print(f"  ✅ '{title}' 고전의 모든 파일이 성공적으로 다운로드되었습니다!")
            self.save_downloaded_classic(title)
        elif success_count > 0:
            print(f"  ⚠️ '{title}' 고전의 일부 파일만 다운로드되었습니다. ({success_count}/{len(detail_links)})")
            print(f"     다음 실행 시 다시 시도됩니다.")
        else:
            print(f"  ❌ '{title}' 고전의 파일을 다운로드할 수 없었습니다.")
            print(f"     다음 실행 시 다시 시도됩니다.")
        
        return success_count
    
    def crawl_all(self):
        """모든 고전을 크롤링합니다."""
        print("세종한글고전 사이트 크롤링을 시작합니다...")
        
        try:
            # Playwright 브라우저 시작
            print("브라우저를 시작합니다...")
            self.start_browser()
            
            # 메인 페이지에서 모든 고전 링크 추출
            classic_links = self.get_main_links()
            
            if not classic_links:
                print("고전 링크를 찾을 수 없습니다.")
                return
            
            total_files = 0
            
            # 각 고전별로 크롤링 수행
            for i, classic in enumerate(classic_links, 1):
                print(f"\n=== [{i}/{len(classic_links)}] ===")
                
                try:
                    files_downloaded = self.crawl_classic(classic)
                    total_files += files_downloaded
                    
                    # 각 고전 사이의 최소 딜레이
                    time.sleep(1)
                    
                except KeyboardInterrupt:
                    print("\n사용자에 의해 중단되었습니다.")
                    break
                except Exception as e:
                    print(f"고전 '{classic['title']}' 크롤링 중 오류 발생: {e}")
                    continue
            
            print(f"\n=== 크롤링 완료 ===")
            print(f"총 {len(classic_links)}개 고전에서 {total_files}개 파일을 다운로드했습니다.")
            print(f"저장 위치: {self.download_dir.absolute()}")
            
            # 실제 저장된 파일들 확인
            print(f"\n=== 저장된 파일 확인 ===")
            if self.download_dir.exists():
                all_files = list(self.download_dir.rglob("*.xml"))
                print(f"실제 저장된 XML 파일 수: {len(all_files)}")
                
                if len(all_files) > 0:
                    print(f"저장된 파일들:")
                    for file in all_files[:10]:  # 처음 10개만 표시
                        file_size = file.stat().st_size
                        relative_path = file.relative_to(self.download_dir)
                        print(f"  - {relative_path} ({file_size} bytes)")
                    
                    if len(all_files) > 10:
                        print(f"  ... 외 {len(all_files) - 10}개 파일")
                        
                    # 폴더별 파일 수 통계
                    folder_stats = {}
                    for file in all_files:
                        folder = file.parent.name
                        folder_stats[folder] = folder_stats.get(folder, 0) + 1
                    
                    print(f"\n폴더별 파일 수:")
                    for folder, count in folder_stats.items():
                        print(f"  - {folder}: {count}개 파일")
                else:
                    print("❌ 저장된 XML 파일이 없습니다!")
                    print("문제 해결을 위한 제안:")
                    print("1. 인터넷 연결 상태 확인")
                    print("2. 사이트 접근 권한 확인")
                    print("3. Playwright 브라우저 설치 확인: playwright install chromium")
            else:
                print(f"❌ 저장 디렉토리가 존재하지 않습니다: {self.download_dir.absolute()}")
            
        except KeyboardInterrupt:
            print("\n사용자에 의해 중단되었습니다.")
        except Exception as e:
            print(f"크롤링 중 전체 오류 발생: {e}")
        
        finally:
            # 브라우저 정리
            print("브라우저를 종료합니다...")
            self.close_browser()

def main():
    """메인 함수"""
    print("=== 세종한글고전 크롤러 ===")
    print("주의: 처음 실행 시 다음 명령어로 Playwright 브라우저를 설치해주세요:")
    print("  pip install playwright")
    print("  playwright install chromium")
    print("=" * 50)
    
    try:
        # 크롤러 인스턴스 생성
        crawler = SejongClassicCrawler()
        
        # 크롤링 시작
        crawler.crawl_all()
        
    except ImportError as e:
        print(f"라이브러리 가져오기 오류: {e}")
        print("\n필요한 라이브러리를 설치해주세요:")
        print("  pip install -r requirements.txt")
        print("  playwright install chromium")
    except Exception as e:
        print(f"크롤러 실행 중 오류 발생: {e}")
        print("\nPlaywright가 제대로 설치되었는지 확인해주세요:")
        print("  pip install playwright")
        print("  playwright install chromium")

if __name__ == "__main__":
    main() 