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
            
            # 표시용 날짜 포맷
            year_month_label = min_date.strftime('%Y년 %m월분') # 예: 2026년 03월분
            date_range = f"{min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"
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
                        st.error("이미지 오류! template.png 파일을 확인해주세요.")
                        st.stop()

                    draw = ImageDraw.Draw(img)
                    
                    # 폰트 설정
                    try:
                        font_title = ImageFont.truetype("malgun.ttf", 350) # 제목용 (매우 크게)
                        font_huge = ImageFont.truetype("malgun.ttf", 250)
                        font_large = ImageFont.truetype("malgun.ttf", 180)
                    except:
                        font_title = font_huge = font_large = ImageFont.load_default()
                    
                    # --- [초고해상도 맞춤 좌표] ---
                    
                    # 0. 상단 제목 (0000년 00월분 장기요양급여 제공명세서)
                    # 위치가 너무 위면 500을 더 키우세요.
                    draw.text((1200, 500), f"{year_month_label} 장기요양급여 제공명세서", fill="black", font=font_title)
                    
                    # 1. 상단 정보
                    draw.text((1500, 2450), str(row['수급자명']), fill="black", font=font_huge)
                    draw.text((1500, 2750), str(row['인정관리번호']), fill="black", font=font_large)
                    draw.text((3800, 2450), date_range, fill="black", font=font_large)
                    
                    # 2. 금액표
                    draw.text((3000, 3150), f"{own_pay:,}", fill="black", font=font_huge)
                    draw.text((3000, 3400), f"{pub_pay:,}", fill="black", font=font_huge)
                    draw.text((3000, 3650), f"{total_pay:,}", fill="black", font=font_huge)
                    
                    # 우측 총액
                    draw.text((5800, 3150), f"{total_pay:,}", fill="black", font=font_huge)
                    draw.text((5800, 3500), f"{own_pay:,}", fill="black", font=font_huge)
                    
                    # 3. 하단 발행일 (말일)
                    draw.text((5800, 7550), publish_date, fill="black", font=font_huge)
                    
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    zip_file.writestr(f"{row['수급자명']}_명세서.png", img_byte_arr.getvalue())
            
            st.success(f"완료! {year_month_label} 명세서 {len(final_df)}건 생성됨")
            st.download_button("📥 전체 명세서 다운로드", data=zip_buffer.getvalue(), file_name=f"하예성_명세서_{min_date.strftime('%Y%m')}.zip")
            
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
