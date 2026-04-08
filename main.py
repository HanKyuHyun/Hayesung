import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile

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
            
            # --- 날짜 자동 계산 로직 ---
            # '일자' 컬럼을 날짜 형식으로 변환
            df2['일자'] = pd.to_datetime(df2['일자'])
            start_date = df2['일자'].min().strftime('%Y-%m-%d') # 제일 빠른 날
            end_date = df2['일자'].max().strftime('%Y-%m-%d')   # 제일 늦은 날
            date_range = f"{start_date} ~ {end_date}"
            
            # 수가 계산 (콤마 제거 및 숫자 변환)
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
                    
                    # 이미지 열기 (오류 방지를 위해 최대한 단순하게 열기)
                    try:
                        img = Image.open("template.png")
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                    except Exception as img_err:
                        st.error("이미지 파일을 읽을 수 없습니다. template.png 파일을 삭제 후 다시 올려주세요.")
                        st.stop()

                    draw = ImageDraw.Draw(img)
                    
                    try:
                        font = ImageFont.truetype("malgun.ttf", 25)
                        font_small = ImageFont.truetype("malgun.ttf", 20)
                    except:
                        font = ImageFont.load_default()
                        font_small = ImageFont.load_default()
                    
                    # --- 좌표 입력 (사장님 양식 위치에 맞춰 조정 필요) ---
                    # 1. 성명 및 정보
                    draw.text((150, 240), str(row['수급자명']), fill="black", font=font)
                    draw.text((150, 280), str(row['인정관리번호']), fill="black", font=font_small)
                    
                    # 2. 💡 자동 계산된 날짜 기입 (급여제공기간 칸)
                    draw.text((350, 240), date_range, fill="black", font=font_small)
                    
                    # 3. 금액 기입
                    draw.text((450, 420), f"{own_pay:,}", fill="black", font=font)
                    draw.text((450, 450), f"{pub_pay:,}", fill="black", font=font)
                    draw.text((450, 480), f"{total_pay:,}", fill="black", font=font)
                    
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    zip_file.writestr(f"{row['수급자명']}_명세서.png", img_byte_arr.getvalue())
            
            st.success(f"기간: {date_range} / 총 {len(final_df)}명 완료!")
            st.download_button("📥 압축파일 다운로드", data=zip_buffer.getvalue(), file_name=f"하예성_명세서_{start_date[:7]}.zip")
            
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
