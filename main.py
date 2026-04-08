import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
from datetime import datetime

st.set_page_config(page_title="하예성 복지센터", layout="wide")
st.title("📄 하예성 복지센터 명세서 최종 보정 (계산 & 위치)")

# 자격별 요율 (사장님 엑셀 '자격' 컬럼 기준)
RATE_MAP = {'일반': 0.15, '감경(40%)': 0.09, '감경(60%)': 0.06, '의료': 0.06, '기초': 0.0}

col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("1. 수급자구분변경이력 (xlsx)", type=['xlsx'])
with col2:
    file2 = st.file_uploader("2. 일정계획 (xlsx)", type=['xlsx'])

if file1 and file2:
    if st.button("🚀 명세서 일괄 발행 (정밀 교정)"):
        try:
            df1 = pd.read_excel(file1)
            df2 = pd.read_excel(file2)
            
            # 날짜 처리
            df2['일자'] = pd.to_datetime(df2['일자'])
            min_date = df2['일자'].min()
            max_date = df2['일자'].max()
            year_month = min_date.strftime('%Y년 %m월분')
            date_range_str = f"{min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"
            # 발행일은 해당 월의 마지막 날로 설정
            pub_date_str = max_date.strftime('%Y    %m    %d') 
            
            # 수가 계산 (쉼표 제거 후 숫자 변환)
            df2['수가'] = pd.to_numeric(df2['수가'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            df2_sum = df2.groupby('수급자명')['수가'].sum().reset_index()
            
            # 데이터 병합
            final_df = pd.merge(df1, df2_sum, on='수급자명', how='inner')
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for _, row in final_df.iterrows():
                    total_amt = int(row['수가']) # 급여계
                    rate = RATE_MAP.get(row['자격'], 0.15)
                    own_amt = int(total_amt * rate) # 본인부담금
                    pub_amt = total_amt - own_amt   # 공단부담금
                    
                    img = Image.open("template.png").convert('RGB')
                    draw = ImageDraw.Draw(img)
                    
                    try:
                        f_name = ImageFont.truetype("malgun.ttf", 160)  # 성명용
                        f_mid = ImageFont.truetype("malgun.ttf", 130)   # 금액/번호용
                        f_date = ImageFont.truetype("malgun.ttf", 110)  # 기간용
                    except:
                        f_name = f_mid = f_date = ImageFont.load_default()

                    # --- [4960x7016 초정밀 좌표 수정] ---
                    # 1. 상단 인적사항
                    draw.text((750, 2480), str(row['수급자명']), fill="black", font=f_name)
                    draw.text((750, 2800), str(row['인정관리번호']), fill="black", font=f_mid)
                    draw.text((1550, 2800), date_range_str, fill="black", font=f_date)
                    
                    # 2. 왼쪽 급여 항목 (본인/공단/계)
                    draw.text((1700, 3180), f"{own_amt:,}", fill="black", font=f_mid)
                    draw.text((1700, 3450), f"{pub_amt:,}", fill="black", font=f_mid)
                    draw.text((1700, 3720), f"{total_amt:,}", fill="black", font=f_mid)
                    
                    # 3. 오른쪽 금액산정내역 (총액/본인부담총액)
                    draw.text((2600, 3280), f"{total_amt:,}", fill="black", font=f_mid)
                    draw.text((2600, 3850), f"{own_amt:,}", fill="black", font=f_mid)
                    
                    # 4. 수납금액 합계 (중앙 우측)
                    draw.text((3250, 5200), f"{own_amt:,}", fill="black", font=f_mid)
                    
                    # 5. 하단 발행일 및 '중간' 체크
                    draw.text((3880, 1370), "v", fill="black", font=f_name) # 중간(V) 체크
                    draw.text((2600, 7550), pub_date_str, fill="black", font=f_mid) # 하단 날짜
                    
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    zip_file.writestr(f"{row['수급자명']}_{min_date.strftime('%m월')}.png", img_byte_arr.getvalue())
            
            st.success(f"✅ {len(final_df)}건 발행 완료! 이제 다운로드하세요.")
            st.download_button("📥 압축파일 다운로드", data=zip_buffer.getvalue(), file_name=f"하예성_결과_{min_date.strftime('%Y%m')}.zip")
            
        except Exception as e:
            st.error(f"오류: {e}")
