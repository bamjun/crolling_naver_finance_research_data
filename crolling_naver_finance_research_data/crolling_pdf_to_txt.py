import os
import time
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from PyPDF2 import PdfReader

# 현재 스크립트의 디렉토리 경로
current_dir = os.path.dirname(os.path.abspath(__file__))

# 크롬 웹드라이버 상대 경로 설정
chrome_driver_path = os.path.join(current_dir, 'chromedriver-win64', 'chromedriver.exe')
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service)

# 네이버 금융 리서치 웹사이트 URL
url = 'https://finance.naver.com/research/company_list.naver'

# 웹페이지 열기
driver.get(url)

# 페이지 로딩을 위해 잠시 대기
time.sleep(3)

# 데이터를 저장할 리스트 초기화
data = []

# 테이블 행 찾기
rows = driver.find_elements(By.CSS_SELECTOR, 'table.type_1 tbody tr')

# 각 행에서 데이터 추출
for row in rows:
    columns = row.find_elements(By.TAG_NAME, 'td')
    if len(columns) < 5:
        continue

    종목명 = columns[0].text.strip()
    제목 = columns[1].text.strip()
    증권사 = columns[2].text.strip()
    작성일 = columns[4].text.strip()
    
    # 첨부 파일 URL 추출 및 다운로드
    첨부_element = columns[3].find_element(By.TAG_NAME, 'a')
    첨부_url = 첨부_element.get_attribute('href')
    첨부_relative_path = os.path.join('downloads', os.path.basename(첨부_url))
    첨부_absolute_path = os.path.join(current_dir, 첨부_relative_path)
    
    # 첨부 파일 다운로드
    response = requests.get(첨부_url)
    os.makedirs(os.path.dirname(첨부_absolute_path), exist_ok=True)
    with open(첨부_absolute_path, 'wb') as file:
        file.write(response.content)

    # PDF 텍스트 추출 및 저장
    pdf_text_folder = os.path.join(current_dir, 'pdf_text')
    os.makedirs(pdf_text_folder, exist_ok=True)
    pdf_text_path = os.path.join(pdf_text_folder, os.path.basename(첨부_url).replace('.pdf', '.txt'))
    
    with open(첨부_absolute_path, 'rb') as pdf_file:
        reader = PdfReader(pdf_file)
        with open(pdf_text_path, 'w', encoding='utf-8') as text_file:
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_file.write(text)
    
    data.append([종목명, 제목, 증권사, 첨부_relative_path, 작성일, pdf_text_path])

# 웹드라이버 닫기
driver.quit()

# 데이터프레임 생성
df = pd.DataFrame(data, columns=['종목명', '제목', '증권사', '첨부 경로', '작성일', '텍스트 파일 경로'])

# 데이터프레임을 JSON 파일로 저장
df.to_json('naver_finance_research.json', orient='records', force_ascii=False, indent=4)

print("Data saved to naver_finance_research.json")
