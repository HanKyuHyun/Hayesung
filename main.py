import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import math

st.set_page_config(page_title="하예성 복지센터", layout="wide")
st.title("📄 하예성 복지센터 명세서 (금액 절상 및 좌표 교정)")

# 1. 자격별 요율 설정
RATE_MAP = {'일반': 0.15, '감경(40%)': 0.09, '감경(60%)': 0.06, '의료': 0.06, '기초': 0.0}

def ceil_10(value):
    """원단위 무조건 올림 (예: 1231원 -> 1240원)"""
    return math.ceil(value / 10) * 10

col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("1. 수급자구분변경이력 (xlsx)", type=['xlsx'])
with col2:
    file2 = st.file_uploader("2. 일정계획 (xlsx)", type=['xlsx'])

if file1 and file2:
    if st.button("🚀 명세서 발행하기"):
        try:
            df1 = pd.read_excel(file1)
            df2 = pd.read_excel(file2)
            
            df2['일자'] = pd.to_datetime(df2['일자'])
            min_date = df2['일자'].min()
            max_date = df2['일자'].max()
            date_range = f"{min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"
            publish_date = max_date.strftime('%Y    %m    %d')
            
            df2['수가'] = pd.to_numeric(df2['수가'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            df2_sum = df2.groupby('수급자명')['수가'].sum().reset_index()
            final_df = pd.merge(df1, df2_sum, on='수급자명', how='inner')
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for _, row in final_df.iterrows():
                    # --- 금액 계산 (원단위 절상) ---
                    total_amt = int(row['수가'])
                    user_status = str(row['자격']).strip()
                    rate = RATE_MAP.get(user_status, 0.15)
                    
                    own_amt = ceil_10(total_amt * rate) # 본인부담금 올림
                    pub_amt = total_amt - own_amt        # 공단부담금
                    
                    # 이미지 로드 (1984 x 2806 기준)
                    img = Image.open("template.png").convert('RGB')
                    draw = ImageDraw.Draw(img)
                    
                    try:
                        f_name = ImageFont.truetype("malgun.ttf", 65)
                        f_main = ImageFont.truetype("malgun.ttf", 55)
                        f_date = ImageFont.truetype("malgun.ttf", 45)
                    except:
                        f_name = f_main = f_date = ImageFont.load_default()

                    # --- [1984 x 2806 정밀 좌표] ---
                    # 1. 인적사항
                    draw.text((280, 1005), str(row['수급자명']), fill="black", font=f_name)
                    draw.text((280, 1155), str(row['인정관리번호']), fill="black", font=f_main)
                    draw.
