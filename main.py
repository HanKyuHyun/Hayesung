import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
from datetime import datetime

st.set_page_config(page_title="하예성 복지센터", layout="wide")
st.title("📄 하예성 복지센터 명세서 (최종 테스트)")

RATE_MAP = {'일반': 0.15, '감경(40%)': 0.09, '감경(60%)': 0.06, '의료': 0.06, '기초': 0.0}

col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("1. 수급자구분변경이력", type=['xlsx'])
with col2:
    file2 = st.file_uploader("2. 일정계획", type=['xlsx'])

if file1 and file2:
    if st.button("🚀 명세서 생성 시작"):
        try:
            df1 = pd.read_excel(file1)
            df2 = pd.read_excel(file2)
            
            # 날짜 계산
            df2['일자'] = pd.to_datetime(df2['일자'])
            min_date = df2['일자'].min()
            max_date = df2['일자'].max()
            
            # 명세서에 들어갈 월 정보 (예: 2026년 03월분)
            target_month = min_date.strftime('%Y년 %m월분')
            file_month = min_date.strftime('%Y_%m월') # 파일명용
            date_range = f"{min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"
            publish_date = max_date.strftime('%Y년 %m월 %d일')
            
            df2['수가'] = pd.to_numeric(df2['수가'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            df2_sum = df2.groupby('수급자명')['수가'].sum().reset_index()
            final_df = pd.merge(df1, df2_sum, on='수급자명', how='inner')
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for _, row in final_df.iterrows():
                    total_pay = int(row['수가'])
                    own_pay = int(total_pay * RATE_MAP.get(row['자격'], 0.15))
                    pub_pay = total_pay - own_pay
                    
                    img = Image.open("template.png").convert("RGB")
                    draw = ImageDraw.Draw(img)
                    
                    try:
                        # 글자가 안 보일 수 없게 크기를 350으로 대폭 키움
                        font = ImageFont.truetype("malgun.ttf", 350)
                    except:
                        font = ImageFont.load_default()

                    # --- [긴급 좌표 수정] ---
                    # 이번엔 글자가 안 보일 수 없도록 화면 중앙 근처에 빨간색으로 씁니다.
                    # 확인 후 위치가 맞으면 숫자를 조절하고 색상을 black으로 바꾸면 됩니다.
                    
                    # 제목 (상단 중앙)
                    draw.text((1000, 800), f"{target_month} 급여명세서", fill="red", font=font)
                    
                    # 성함 및 정보 (중앙 왼쪽)
                    draw.text((800, 2500), f"성함: {row['수급자명']}", fill="red", font=font)
                    draw.text((800, 3000), f"번호: {row['인정관리번호']}", fill="red", font=font)
                    
                    # 금액 (중앙 오른쪽)
                    draw.text((2500, 3500), f"본인부담: {own_pay:,}", fill="red", font=font)
                    draw.text((2500, 4000), f"총액: {total_pay:,}", fill="red", font=font)
                    
                    # 발행일 (하단)
                    draw.text((2500, 6000), publish_date, fill="red", font=font)
                    
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    zip_file.writestr(f"{row['수급자명']}_{file_month}_명세서.png", img_byte_arr.getvalue())
            
            st.success(f"✅ {target_month} 생성이 완료되었습니다!")
            # 다운로드 파일명에 월을 넣었습니다.
            st.download_button("📥 압축파일 다운로드", data=zip_buffer.getvalue(), file_name=f"하예성_명세서_{file_month}.zip")
            
        except Exception as e:
            st.error(f"오류 발생: {e}")
