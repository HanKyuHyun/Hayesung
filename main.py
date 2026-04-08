import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import math

st.set_page_config(page_title="하예성 복지센터", layout="wide")
st.title("📄 하예성 명세서 (실시간 미리보기 및 보정)")

RATE_MAP = {'일반': 0.15, '감경(40%)': 0.09, '감경(60%)': 0.06, '의료': 0.06, '기초': 0.0}

def ceil_10(value):
    return math.ceil(value / 10) * 10

def draw_invoice(row, date_range, publish_date):
    """이미지를 생성하여 반환하는 함수"""
    total_amt = int(row['수가'])
    user_status = str(row['자격']).strip()
    rate = RATE_MAP.get(user_status, 0.15)
    own_amt = ceil_10(total_amt * rate) 
    pub_amt = total_amt - own_amt        
    
    img = Image.open("template.png").convert('RGB')
    draw = ImageDraw.Draw(img)
    
    try:
        f_name = ImageFont.truetype("malgun.ttf", 42)
        f_main = ImageFont.truetype("malgun.ttf", 38)
        f_date = ImageFont.truetype("malgun.ttf", 34)
    except:
        f_name = f_main = f_date = ImageFont.load_default()

    # --- [사장님 요청 정밀 좌표 수정] ---
    
    # 1. 성명 및 인정번호 (같은 Y축, X축 더 왼쪽으로)
    # 성명 칸 시작점에 맞춤
    draw.text((210, 310), str(row['수급자명']), fill="black", font=f_name) 
    # 인정번호도 성명과 나란히 배치 (Y축 310 동일)
    draw.text((210, 370), str(row['인정관리번호']), fill="black", font=f_main)
    
    # 2. 제공기간 (X축 왼쪽으로 당기고 Y축 살짝 올림)
    draw.text((450, 310), date_range, fill="black", font=f_date)
    
    # 3. 금액 항목 (기존 위치 보강)
    draw.text((450, 420), f"{own_amt:,}", fill="black", font=f_main) # 본인부담
    draw.text((450, 470), f"{pub_amt:,}", fill="black", font=f_main) # 공단부담
    draw.text((450, 520), f"{total_amt:,}", fill="black", font=f_main) # 급여계
    
    # 4. 오른쪽 총액 및 본인총액
    draw.text((920, 435), f"{total_amt:,}", fill="black", font=f_main)
    draw.text((920, 535), f"{own_amt:,}", fill="black", font=f_main)
    
    # 5. 수납금액 합계
    draw.text((1050, 1120), f"{own_amt:,}", fill="black", font=f_name)
    
    # 6. 하단 날짜
    draw.text((950, 2450), publish_date, fill="black", font=f_main)
    
    return img

col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("1. 수급자구분변경이력 (xlsx)", type=['xlsx'])
with col2:
    file2 = st.file_uploader("2. 일정계획 (xlsx)", type=['xlsx'])

if file1 and file2:
    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)
    
    df2['일자'] = pd.to_datetime(df2['일자'])
    min_date = df2['일자'].min()
    max_date = df2['일자'].max()
    date_range = f"{min_date.strftime('%Y-%m-%d')}~{max_date.strftime('%Y-%m-%d')}"
    publish_date = max_date.strftime('%Y      %m      %d')
    
    df2['수가'] = pd.to_numeric(df2['수가'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    df2_sum = df2.groupby('수급자명')['수가'].sum().reset_index()
    final_df = pd.merge(df1, df2_sum, on='수급자명', how='inner')

    st.subheader("👀 실시간 미리보기")
    selected_person = st.selectbox("확인할 수급자를 선택하세요", final_df['수급자명'].tolist())
    
    if selected_person:
        row = final_df[final_df['수급자명'] == selected_person].iloc[0]
        preview_img = draw_invoice(row, date_range, publish_date)
        # 화면에 맞게 리사이즈해서 보여줌
        st.image(preview_img, caption=f"{selected_person}님 명세서 미리보기", use_container_width=True)

    if st.button("🎁 전체 명세서 압축 다운로드"):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for _, row in final_df.iterrows():
                img = draw_invoice(row, date_range, publish_date)
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                zip_file.writestr(f"{row['수급자명']}_명세서.png", img_byte_arr.getvalue())
        
        st.download_button("📥 압축파일 받기", data=zip_buffer.getvalue(), file_name="하예성_최종_명세서.zip")
