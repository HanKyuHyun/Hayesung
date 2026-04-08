import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import math

st.set_page_config(page_title="하예성 복지센터", layout="wide")
st.title("📄 하예성 명세서 (인적사항 정밀 조정)")

RATE_MAP = {'일반': 0.15, '감경(40%)': 0.09, '감경(60%)': 0.06, '의료': 0.06, '기초': 0.0}

def ceil_10(value):
    return math.ceil(value / 10) * 10

def draw_invoice(row, date_range, publish_date_str):
    total_amt = int(row['수가'])
    user_status = str(row['자격']).strip()
    rate = RATE_MAP.get(user_status, 0.15)
    own_amt = ceil_10(total_amt * rate) 
    pub_amt = total_amt - own_amt        
    
    img = Image.open("template.png").convert('RGB')
    draw = ImageDraw.Draw(img)
    
    try:
        f_name = ImageFont.truetype("malgun.ttf", 48) 
        f_main = ImageFont.truetype("malgun.ttf", 42)
        f_date = ImageFont.truetype("malgun.ttf", 36)
    except:
        f_name = f_main = f_date = ImageFont.load_default()

    # --- [좌표 재수정: 전체적으로 왼쪽 & 아래로] ---
    
    # Y_LINE: 성명 라인을 이전보다 아래로(725 -> 760) 내림
    Y_LINE = 760 

    # 1. 인적사항 (전체적으로 왼쪽 X축 값을 줄임)
    # 성명 (220 -> 180으로 왼쪽 이동)
    draw.text((180, Y_LINE), str(row['수급자명']), fill="black", font=f_name)
    # 인정번호 (450 -> 380으로 왼쪽 이동)
    draw.text((380, Y_LINE + 5), str(row['인정관리번호']), fill="black", font=f_main)
    # 제공기간 (850 -> 720으로 왼쪽 이동)
    draw.text((720, Y_LINE + 10), date_range, fill="black", font=f_date)
    
    # 2. 왼쪽 '급여' 항목 (이전보다 살짝 아래로 조정)
    draw.text((830, 1080), f"{own_amt:,}", fill="black", font=f_main) 
    draw.text((830, 1200), f"{pub_amt:,}", fill="black", font=f_main) 
    draw.text((830, 1320), f"{total_amt:,}", fill="black", font=f_main) 
    
    # 3. 오른쪽 '금액산정내역' (중앙 정렬 유지)
    draw.text((1350, 1120), f"{total_amt:,}", fill="black", font=f_main) 
    draw.text((1350, 1360), f"{own_amt:,}", fill="black", font=f_main)   
    
    # 4. 수납금액 합계 부분은 사장님 요청으로 삭제하였습니다.
    
    # 5. 하단 날짜 (년 월 일 표기)
    draw.text((1250, 2700), publish_date_str, fill="black", font=f_main)
    
    return img

# ... (이하 엑셀 업로드 및 미리보기 로직은 동일)
