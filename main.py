import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import math

st.set_page_config(page_title="하예성 복지센터", layout="wide")
st.title("📄 하예성 명세서 (최종 완성본)")

RATE_MAP = {'일반': 0.15, '감경(40%)': 0.09, '감경(60%)': 0.06, '의료': 0.06, '기초': 0.0}

# --- 1. 필수 계산 및 포맷 함수 ---
def ceil_10(value):
    """1원 단위에서 올림하여 10원 단위로 만듦"""
    return math.ceil(value / 10) * 10

def format_amt(amt):
    """0원일 경우 '-'로 표시, 그 외 천단위 콤마"""
    if amt == 0:
        return "-"
    return f"{amt:,}"

# --- 2. 명세서 그리기 함수 (seq_num 매개변수 추가!) ---
def draw_invoice(row, date_range, publish_date_str, seq_num):
    total_amt = int(row['수가'])
    user_status = str(row['자격']).strip()
    rate = RATE_MAP.get(user_status, 0.15)
    own_amt = ceil_10(total_amt * rate) 
    pub_amt = total_amt - own_amt        
    
    img = Image.open("template.png").convert('RGB')
    draw = ImageDraw.Draw(img)
    
    try:
        f_name = ImageFont.truetype("malgun.ttf", 28) 
        f_main = ImageFont.truetype("malgun.ttf", 28)
        f_date = ImageFont.truetype("malgun.ttf", 24)
    except:
        f_name = f_main = f_date = ImageFont.load_default()

    # [0. 영수증 번호 추가]
    # 사장님 요청 좌표: (1350, 780)
    receipt_no = f"2026-03-{seq_num:02d}" 
    draw.text((1350, 780), receipt_no, fill="black", font=f_main)

    # [1. 인적사항: 사장님 고정 좌표]
    Y_LINE = 780 
    draw.text((220, Y_LINE), str(row['수급자명']), fill="black", font=f_name)
    draw.text((380, Y_LINE + 5), str(row['인정관리번호']), fill="black", font=f_main)
    draw.text((635, Y_LINE + 10), date_range, fill="black", font=f_date)
    
    # [2. 급여항목: ₩ 630 고정 & 숫자 우측정렬]
    L_X, R_X = 630, 950  
    draw.text((L_X, 888), "₩", fill="black", font=f_main)
    draw.text((R_X, 888), format_amt(own_amt), fill="black", font=f_main, anchor="ra")
    draw.text((L_X, 960), "₩", fill="black", font=f_main)
    draw.text((R_X, 960), format_amt(pub_amt), fill="black", font=f_main, anchor="ra")
    draw.text((L_X, 1030), "₩", fill="black", font=f_main)
    draw.text((R_X, 1030), format_amt(total_amt), fill="black", font=f_main, anchor="ra")
    
    # [3. 금액산정내역: 사장님 고정 좌표]
    R_L_X, R_R_X = 1280, 1670 
    draw.text((R_L_X, 915), "₩", fill="black", font=f_main)
    draw.text((R_R_X, 915), format_amt(total_amt), fill="black", font=f_main, anchor="ra")
    draw.text((R_L_X, 1010), "₩", fill="black", font=f_main)
    draw.text((R_R_X, 1010), format_amt(own_amt), fill="black", font=f_main, anchor="ra")
    
    # 4. 하단 발행일
    draw.text((1350, 2050), publish_date_str, fill="black", font=f_main)
    
    return img

#
