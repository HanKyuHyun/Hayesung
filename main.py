import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile

st.set_page_config(page_title="하예성 복지센터 명세서", layout="wide")
st.title("📄 하예성 복지센터 명세서 자동 생성기")

# 1. 자격별 본인부담 요율 설정 (수정 완료)
# 일반(15%), 감경40%(9%), 감경60% & 의료(6%), 기초(0%)
RATE_MAP = {
    '일반': 0.15,
    '감경(40%)': 0.09,
    '감경(60%)': 0.06,
    '의료': 0.06,  # 의료 자격 6% 적용
    '기초': 0.0
}

st.info("💡 파일 1(이력)과 파일 2(일정)를 순서대로 올려주세요.")

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
            
            # 이름별 수가 합계 계산 (파일 2)
            df2_sum = df2.groupby('이름')['수가'].sum().reset_index()
            
            # 데이터 병합 (성명 기준)
            final_df = pd.merge(df1, df2_sum, left_on='수급자명', right_on='이름', how='inner')
            
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for _, row in final_df.iterrows():
                    # 금액 계산
                    total_pay = int(row['수가']) 
                    user_rate = RATE_MAP.get(row['자격'], 0.15) 
                    own_pay = int(total_pay * user_rate) 
                    pub_pay = total_pay - own_pay 
                    
                    # 이미지 작업 (template.png 사용)
                    img = Image.open("template.png").convert("RGB")
                    draw = ImageDraw.Draw(img)
                    
                    # 폰트 설정 (GitHub에 malgun.ttf 파일 권장)
                    try:
                        font = ImageFont.truetype("malgun.ttf", 25)
                        font_small = ImageFont.truetype("malgun.ttf", 20)
                    except:
                        font = ImageFont.load_default()
                        font_small = ImageFont.load_default()
                    
                    # --- 좌표 입력 (수치는 예시이며, 결과물 확인 후 수정 가능) ---
                    # 1. 성명 및 정보
                    draw.text((150, 240), str(row['수급자명']), fill="black", font=font)
                    draw.text((300, 240), str(row['인정관리번호']), fill="black", font=font_small)
                    
                    # 2. 금액 (천단위 콤마 적용)
                    draw.text((450, 420), f"{own_pay:,}", fill="black", font=font)  # 본인부담금
                    draw.text((450, 450), f"{pub_pay:,}", fill="black", font=font)  # 공단부담금
                    draw.text((450, 480), f"{total_pay:,}", fill="black", font=font) # 급여계(총액)
                    
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    zip_file.writestr(f"{row['수급자명']}_명세서.png", img_byte_arr.getvalue())
            
            st.success(f"총 {len(final_df)}명의 명세서 생성이 완료되었습니다!")
            st.download_button("📥 압축파일 다운로드", data=zip_buffer.getvalue(), file_name="하예성_명세서_전체.zip")
            
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}. 엑셀 항목 이름(수급자명, 이름, 수가 등)을 확인해 주세요.")
