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
            
            # 💡 수정된 부분: '이름' 대신 '수급자명'을 기준으로 합산합니다.
            # 엑셀에 금액 숫자에 콤마(,)가 있어도 계산 가능하도록 처리합니다.
            df2['수가'] = pd.to_numeric(df2['수가'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            df2_sum = df2.groupby('수급자명')['수가'].sum().reset_index()
            
            # 데이터 병합 (둘 다 '수급자명' 기준)
            final_df = pd.merge(df1, df2_sum, on='수급자명', how='inner')
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for _, row in final_df.iterrows():
                    total_pay = int(row['수가']) 
                    user_rate = RATE_MAP.get(row['자격'], 0.15) 
                    own_pay = int(total_pay * user_rate) 
                    pub_pay = total_pay - own_pay 
                    
                    img = Image.open("template.png").convert("RGB")
                    draw = ImageDraw.Draw(img)
                    
                    try:
                        font = ImageFont.truetype("malgun.ttf", 25)
                        font_small = ImageFont.truetype("malgun.ttf", 20)
                    except:
                        font = ImageFont.load_default()
                        font_small = ImageFont.load_default()
                    
                    # --- 좌표 입력 ---
                    draw.text((150, 240), str(row['수급자명']), fill="black", font=font)
                    draw.text((300, 240), str(row['인정관리번호']), fill="black", font=font_small)
                    draw.text((450, 420), f"{own_pay:,}", fill="black", font=font)
                    draw.text((450, 450), f"{pub_pay:,}", fill="black", font=font)
                    draw.text((450, 480), f"{total_pay:,}", fill="black", font=font)
                    
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    zip_file.writestr(f"{row['수급자명']}_명세서.png", img_byte_arr.getvalue())
            
            st.success(f"총 {len(final_df)}명의 명세서 생성이 완료되었습니다!")
            st.download_button("📥 압축파일 다운로드", data=zip_buffer.getvalue(), file_name="하예성_명세서_전체.zip")
            
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
