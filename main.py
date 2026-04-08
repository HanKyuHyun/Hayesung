import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
from datetime import datetime

st.set_page_config(page_title="하예성 복지센터", layout="wide")
st.title("📄 하예성 복지센터 명세서 최종 최적화")

RATE_MAP = {'일반': 0.15, '감경(40%)': 0.09, '감경(60%)': 0.06, '의료': 0.06, '기초': 0.0}

col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("1. 수급자구분변경이력 (xlsx)", type=['xlsx'])
with col2:
    file2 = st.file_uploader("2. 일정계획 (xlsx)", type=['xlsx'])

if file1 and file2:
    if st.button("🚀 최종 명세서 발행하기"):
        try:
            df1 = pd.read_excel(file1)
            df2 = pd.read_excel(file2)
            
            df2['일자'] = pd.to_datetime(df2['일자'])
            min_date = df2['일자'].min()
            max_date = df2['일자'].max()
            
            target_month = min_date.strftime('%Y년 %m월분')
            date_range = f"{min_date.strftime('%Y-%m-%d')}~{max_date.strftime('%Y-%m-%d')}"
            publish_date = max_date.strftime('%Y   %m   %d') # 날짜 사이 간격 띄움
            
            df2['수가'] = pd.to_numeric(df2['수가'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            df2_sum = df2.groupby('수급자명')['수가'].sum().reset_index()
            final_df = pd.merge(df1, df2_sum, on='수급자명', how='inner')
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for _, row in final_df.iterrows():
                    total_pay = int(row['수가']) 
                    own_pay = int(total_pay * RATE_MAP.get(row['자격'], 0.15)) 
                    pub_pay = total_pay - own_pay 
                    
                    img = Image.open("template.png").convert('RGB')
                    draw = ImageDraw.Draw(img)
                    
                    # --- 폰트 크기 최적화 (너무 크지 않게 조정) ---
                    font_path = "malgun.ttf"
                    try:
                        font_title = ImageFont.truetype(font_path, 150) # 상단 제목 옆 월 표시용
                        font_main = ImageFont.truetype(font_path, 130)  # 성명, 금액 등
                        font_small = ImageFont.truetype(font_path, 100) # 인정번호, 기간
                    except:
                        font_title = font_main = font_small = ImageFont.load_default()

                    # --- [사장님 양식 4960x7016 최종 좌표 미세조정] ---
                    
                    # 1. 상단 '중간' 체크표시 (이미지에 있는 체크박스 위치)
                    draw.text((3850, 1350), "v", fill="black", font=font_main)
                    
                    # 2. 인적사항 (칸의 중앙에 오도록 조정)
                    draw.text((700, 2450), str(row['수급자명']), fill="black", font=font_main)
                    draw.text((700, 2850), str(row['인정관리번호']), fill="black", font=font_small)
                    draw.text((1500, 2850), date_range, fill="black", font=font_small)
                    
                    # 3. 금액 섹션 (표의 금액 칸)
                    draw.text((1600, 3150), f"{own_pay:,}", fill="black", font=font_main)   # 본인부담
                    draw.text((1600, 3450), f"{pub_pay:,}", fill="black", font=font_main)   # 공단부담
                    draw.text((1600, 3750), f"{total_pay:,}", fill="black", font=font_main) # 급여계
                    
                    # 4. 우측 금액산정내역 (총액 및 합계)
                    draw.text((2500, 3250), f"{total_pay:,}", fill="black", font=font_main) # 총액(9)
                    draw.text((2500, 3850), f"{own_pay:,}", fill="black", font=font_main)   # 본인부담총액(10)
                    draw.text((3200, 5200), f"{own_pay:,}", fill="black", font=font_main)   # 합계
                    
                    # 5. 하단 발행일 및 센터 정보 (하단 여백)
                    draw.text((2300, 7550), publish_date, fill="black", font=font_main)
                    
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    zip_file.writestr(f"{row['수급자명']}_{min_date.strftime('%m월')}.png", img_byte_arr.getvalue())
            
            st.success(f"✅ {target_month} 명세서 발행 완료!")
            st.download_button("📥 전체 다운로드", data=zip_buffer.getvalue(), file_name=f"하예성_명세서_{min_date.strftime('%Y%m')}.zip")
            
        except Exception as e:
            st.error(f"오류: {e}")
