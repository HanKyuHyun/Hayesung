import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import math

# ... (상단 생략: RATE_MAP, ceil_10 동일)

def draw_invoice(row, date_range, publish_date):
    # ... (금액 계산 로직 동일)
    
    img = Image.open("template.png").convert('RGB')
    draw = ImageDraw.Draw(img)
    
    try:
        f_name = ImageFont.truetype("malgun.ttf", 48) 
        f_main = ImageFont.truetype("malgun.ttf", 42)
        f_date = ImageFont.truetype("malgun.ttf", 36)
    except:
        f_name = f_main = f_date = ImageFont.load_default()

    # --- [좌표 전면 재수정: 가로 한 줄 정렬] ---
    
    # Y_LINE: 성명, 인정번호, 제공기간이 모두 위치할 '같은 높이'
    Y_LINE = 730 

    # 1. 인적사항 (전부 같은 Y축, X축만 다르게 하여 가로 배치)
    # 성명 (가장 왼쪽)
    draw.text((250, Y_LINE), str(row['수급자명']), fill="black", font=f_name)
    # 인정번호 (성명 오른쪽으로 띄워서 배치)
    draw.text((450, Y_LINE + 5), str(row['인정관리번호']), fill="black", font=f_main)
    # 제공기간 (인정번호보다 더 오른쪽 칸에 배치)
    draw.text((850, Y_LINE + 10), date_range, fill="black", font=f_date)
    
    # 2. 왼쪽 금액 항목 (칸 중앙으로 하향 및 우측 이동)
    draw.text((880, 1055), f"{own_amt:,}", fill="black", font=f_main) # 본인부담
    draw.text((880, 1175), f"{pub_amt:,}", fill="black", font=f_main) # 공단부담
    draw.text((880, 1295), f"{total_amt:,}", fill="black", font=f_main) # 급여계
    
    # 3. 오른쪽 금액산정내역 (중앙 배치)
    draw.text((1380, 1095), f"{total_amt:,}", fill="black", font=f_main) # 총액
    draw.text((1380, 1335), f"{own_amt:,}", fill="black", font=f_main)   # 본인총액
    
    # 4. 수납금액 합계
    draw.text((1500, 1750), f"{own_amt:,}", fill="black", font=f_name)
    
    # 5. 하단 발행일
    draw.text((1350, 2700), publish_date, fill="black", font=f_main)
    
    return img

# ... (하단 미리보기 및 다운로드 로직 동일)
