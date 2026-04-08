import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
from datetime import datetime

st.set_page_config(page_title="하예성 복지센터", layout="wide")
st.title("📄 하예성 복지센터 명세서 자동 생성")

RATE_MAP = {'일반': 0.15, '감경(40%)': 0.09, '감경(60%)': 0.06, '의료': 0.06, '기초': 0.0}

col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("1. 수급자구분변경이력", type=['xlsx'])
with col2:
    file2 = st.file_uploader("2. 일정계획", type=['xlsx'])

if file1 and file2:
    if st.button("🚀 명세서 생성 (위치 보정판)"):
        try:
            df1 = pd.read_excel(file1)
            df2 = pd.read_excel(file2)
            
            df2['일자'] = pd.to_datetime(df2['일자'])
            min_date = df2['일자'].min()
            max_date = df2['일자'].max()
            
            target_month = min_date.strftime('%Y년 %m월분')
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
                        font_huge = ImageFont.truetype("malgun.ttf", 220)
                        font_mid = ImageFont.truetype("malgun.ttf", 150)
                    except:
                        font_huge = font_mid = ImageFont.load_default()

                    # --- [사장님 양식 4960x7016 맞춤 좌표] ---
                    # 1. 제목 (중앙 상단)
                    draw.text((1500, 1000), f"{target_month} 장기요양급여비용 명세서", fill="blue", font=font_huge)
                    
                    # 2. 인적사항 (성명, 인정번호, 기간)
                    draw.text((800, 2750), str(row['수급자명']), fill="blue", font=font_mid)
                    draw.text((1200, 2750), str(row['인정관리번호']), fill="blue", font=font_mid)
                    draw.text((2300, 2750), date_range, fill="blue", font=font_mid)
                    
                    # 3. 금액 섹션 (표 안의 칸들)
                    draw.text((1500, 3650), f"{own_pay:,}", fill="blue", font=font_mid)   # 본인부담금
                    draw.text((1500, 3950), f"{pub_pay:,}", fill="blue", font=font_mid)   # 공단부담금
                    draw.text((1500, 4250), f"{total_pay:,}", fill="blue", font=font_mid) # 급여계
                    
                    # 4. 우측 총액 계산내역
                    draw.text((3600, 3650), f"{total_pay:,}", fill="blue", font=font_mid) # 총액
                    draw.text((3600, 3950), f"{own_pay:,}", fill="blue", font=font_mid)   # 본인부담총액
                    
                    # 5. 하단 발행일
                    draw.text((2800, 7800), publish_date, fill="blue", font=font_mid)
                    
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    zip_file.writestr(f"{row['수급자명']}_{min_date.strftime('%m월')}_명세서.png", img_byte_arr.getvalue())
            
            st.success(f"✅ {target_month} 명세서 생성이 완료되었습니다!")
            st.download_button("📥 압축파일 다운로드", data=zip_buffer.getvalue(), file_name=f"하예성_명세서_{min_date.strftime('%Y%m')}.zip")
            
        except Exception as e:
            st.error(f"오류 발생: {e}")
