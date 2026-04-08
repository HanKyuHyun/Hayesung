import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
from datetime import datetime

st.set_page_config(page_title="하예성 복지센터", layout="wide")
st.title("📄 하예성 복지센터 명세서 (이미지 축소 및 요율 보정판)")

# 1. 요율표 (엑셀 '자격' 컬럼의 텍스트와 완벽히 일치해야 함)
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
    if st.button("🚀 명세서 일괄 생성 및 압축"):
        try:
            df1 = pd.read_excel(file1)
            df2 = pd.read_excel(file2)
            
            # 날짜 및 수가 데이터 정리
            df2['일자'] = pd.to_datetime(df2['일자'])
            min_date = df2['일자'].min()
            max_date = df2['일자'].max()
            
            target_month = min_date.strftime('%Y년 %m월분')
            date_range = f"{min_date.strftime('%Y-%m-%d')}~{max_date.strftime('%Y-%m-%d')}"
            publish_date = max_date.strftime('%Y    %m    %d')
            
            # 쉼표 제거 후 숫자 변환
            df2['수가'] = pd.to_numeric(df2['수가'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            df2_sum = df2.groupby('수급자명')['수가'].sum().reset_index()
            
            # 데이터 병합 (수급자명 기준)
            final_df = pd.merge(df1, df2_sum, on='수급자명', how='inner')
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for _, row in final_df.iterrows():
                    # --- [요율 계산 로직 강화] ---
                    total_amt = int(row['수가'])
                    # 엑셀의 자격 텍스트에서 공백을 제거하고 매칭 시도
                    user_status = str(row['자격']).strip()
                    rate = RATE_MAP.get(user_status, 0.15) # 매칭 안되면 기본 15%
                    
                    own_amt = int(total_amt * rate)
                    pub_amt = total_amt - own_amt
                    
                    # 이미지 로드 (1984 x 2806)
                    img = Image.open("template.png").convert('RGB')
                    draw = ImageDraw.Draw(img)
                    
                    try:
                        # 줄어든 이미지 크기에 맞춘 폰트 사이즈
                        f_main = ImageFont.truetype("malgun.ttf", 45)
                        f_bold = ImageFont.truetype("malgun.ttf", 55)
                        f_small = ImageFont.truetype("malgun.ttf", 35)
                    except:
                        f_main = f_bold = f_small = ImageFont.load_default()

                    # --- [1984x2806 맞춤 정밀 좌표] ---
                    # 1. 인적사항
                    draw.text((320, 1000), str(row['수급자명']), fill="black", font=f_bold)
                    draw.text((320, 1150), str(row['인정관리번호']), fill="black", font=f_main)
                    draw.text((650, 1150), date_range, fill="black", font=f_small)
                    
                    # 2. 왼쪽 금액 (본인/공단/합계)
                    draw.text((700, 1300), f"{own_amt:,}", fill="black", font=f_main)
                    draw.text((700, 1420), f"{pub_amt:,}", fill="black", font=f_main)
                    draw.text((700, 1540), f"{total_amt:,}", fill="black", font=f_bold)
                    
                    # 3. 오른쪽 산정내역
                    draw.text((1100, 1350), f"{total_amt:,}", fill="black", font=f_main)
                    draw.text((1100, 1580), f"{own_amt:,}", fill="black", font=f_main)
                    
                    # 4. 수납금 합계 및 하단 날짜
                    draw.text((1350, 2120), f"{own_amt:,}", fill="black", font=f_bold)
                    draw.text((1100, 3050), publish_date, fill="black", font=f_main)
                    
                    # 중간 체크표시
                    draw.text((1630, 560), "v", fill="black", font=f_bold)
                    
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    zip_file.writestr(f"{row['수급자명']}_{min_date.strftime('%m월')}.png", img_byte_arr.getvalue())
            
            st.success(f"✅ {len(final_df)}명의 명세서가 {target_month} 기준으로 생성되었습니다!")
            st.download_button("📥 압축파일 다운로드", data=zip_buffer.getvalue(), file_name=f"하예성_명세서_{min_date.strftime('%Y%m')}.zip")
            
        except Exception as e:
            st.error(f"오류 발생: {e}")
