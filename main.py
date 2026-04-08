import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
from datetime import datetime

st.set_page_config(page_title="하예성 복지센터 명세서", layout="wide")
st.title("📄 하예성 복지센터 명세서 자동 생성기")

# 자격별 본인부담 요율 설정
RATE_MAP = {
    '일반': 0.15,
    '감경(40%)': 0.09,
    '감경(60%)': 0.06,
    '의료': 0.06,
    '기초': 0.0
}

col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("1. 수급자구분변경이력 (xlsx)", type=['xlsx'])
with col2:
    file2 = st.file_uploader("2. 일정계획 (xlsx)", type=['xlsx'])

if file1 and file2:
    if st.button("🚀 명세서 일괄 생성 및 압축하기"):
        try:
            df1 = pd.read_excel(file1)
            df2 = pd.read_excel(file2)
            
            # --- 날짜 자동 계산 ---
            df2['일자'] = pd.to_datetime(df2['일자'])
            min_date = df2['일자'].min()
            max_date = df2['일자'].max()
            
            # 1. 급여제공기간용 (0000-00-00 ~ 0000-00-00)
            date_range = f"{min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"
            
            # 2. 하단 발행일용 (0000년 00월 00일 - 해당 월의 말일)
            publish_date = max_date.strftime('%Y년 %m월 %d일')
            
            # 수가 계산
            df2['수가'] = pd.to_numeric(df2['수가'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            df2_sum = df2.groupby('수급자명')['수가'].sum().reset_index()
            
            final_df = pd.merge(df1, df2_sum, on='수급자명', how='inner')
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for _, row in final_df.iterrows():
                    total_pay = int(row['수가']) 
                    user_rate = RATE_MAP.get(row['자격'], 0.15) 
                    own_pay = int(total_pay * user_rate) 
                    pub_pay = total_pay - own_pay 
                    
                    try:
                        img = Image.open("template.png")
                        if img.mode != 'RGB': img = img.convert('RGB')
                    except:
                        st.error("이미지 오류! template.png를 다시 확인해주세요.")
                        st.stop()

                    draw = ImageDraw.Draw(img)
                    
                    # 폰트 설정 (맑은고딕)
                    try:
                        font_main = ImageFont.truetype("malgun.ttf", 25)
                        font_small = ImageFont.truetype("malgun.ttf", 18)
                    except:
                        font_main = font_small = ImageFont.load_default()
                    
                    # --- [좌표 입력 섹션] 위치가 안 맞으면 아래 숫자들을 고치세요 ---
                    
                    # 상단 정보
                    draw.text((150, 240), str(row['수급자명']), fill="black", font=font_main)
                    draw.text((150, 280), str(row['인정관리번호']), fill="black", font=font_small)
                    
                    # 중간 급여제공기간
                    draw.text((350, 240), date_range, fill="black", font=font_small)
                    
                    # 금액표 (우측 정렬 느낌으로 좌표 조정 필요)
                    draw.text((450, 420), f"{
