import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import math

st.set_page_config(page_title="하예성 복지센터", layout="wide")
st.title("📄 하예성 명세서 (폰트 축소 및 급여칸 보정)")

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
        # 사장님 요청: 기존 크기(48, 42, 36)의 약 2/3인 30~32 수준으로 축소
        f_name = ImageFont.truetype("malgun.ttf", 32) 
        f_main = ImageFont.truetype("malgun.ttf", 28)
        f_date = ImageFont.truetype("malgun.ttf", 24)
    except:
        f_name = f_main = f_date = ImageFont.load_default()

    # --- [좌표 수정: 급여 항목 왼쪽 30, 위 100 이동] ---
    
    # 1. 인적사항 (Y축은 760 유지, 폰트가 작아져서 시각적으로 더 여유로워짐)
    Y_LINE = 760 
    draw.text((180, Y_LINE), str(row['수급자명']), fill="black", font=f_name)
    draw.text((380, Y_LINE + 5), str(row['인정관리번호']), fill="black", font=f_main)
    draw.text((720, Y_LINE + 10), date_range, fill="black", font=f_date)
    
    # 2. 왼쪽 '급여' 항목 (X는 830->800, Y는 1080->980으로 이동)
    # 사장님 요청: 왼쪽으로 30 (830-30=800), 위로 100 (1080-100=980)
    draw.text((800, 980), f"{own_amt:,}", fill="black", font=f_main) # 본인부담
    draw.text((800, 1100), f"{pub_
