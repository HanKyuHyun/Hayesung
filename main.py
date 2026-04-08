import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import math

# ---------------------------------------------------------
# 1. 설정 및 계산 함수들
# ---------------------------------------------------------
st.set_page_config(page_title="하예성 복지센터", layout="wide")
st.title("📄 하예성 명세서 (최종 완성본 - 가나다순 정렬)")

# 수가에 따른 본인부담률 설정
RATE_MAP = {'일반': 0.15, '감경(40%)': 0.09, '감경(60%)': 0.06, '의료': 0.06, '기초': 0.0}

def ceil_10(value):
    """1원 단위에서 올림하여 10원 단위로 만듦"""
    return math.ceil(value / 10) * 10

def format_amt(amt):
    """0원일 경우 '-'로 표시하고, 그 외에는 천단위 콤마 추가"""
    if amt == 0:
        return "-"
    return f"{amt:,}"

# ---------------------------------------------------------
# 2. 명세서 그리기 함수 (사장님 황금 좌표 반영)
# ---------------------------------------------------------
def draw_invoice(row, date_range, publish_date_str, seq_num):
    # 계산 로직
    total_amt = int(row['수가'])
    user_status = str(row['자격']).strip()
    rate = RATE_MAP.get(user_status, 0.15)
    own_amt = ceil_10(total_amt * rate) 
    pub_amt = total_amt - own_amt        
    
    # 템플릿 이미지 불러오기 (파일 이름이 template.png여야 합니다)
    img = Image.open("template.png").convert('RGB')
    draw = ImageDraw.Draw(img)
    
    # 폰트 설정 (축소된 28사이즈)
    try:
        f_name = ImageFont.truetype("malgun.ttf", 28) 
        f_main = ImageFont.truetype("malgun.ttf", 28)
        f_date = ImageFont.truetype("malgun.ttf", 24)
    except:
        f_name = f_main = f_date = ImageFont.load_default()

    # [0. 영수증 번호] 사장님 요청 좌표
    receipt_no = f"2026-03-{seq_num:02d}" 
    draw.text((1350, 780), receipt_no, fill="black", font=f_main)

    # [1. 인적사항] 사장님 좌표
    Y_LINE = 780 
    draw.text((220, Y_LINE), str(row['수급자명']), fill="black", font=f_name)
    draw.text((380, Y_LINE + 5), str(row['인정관리
