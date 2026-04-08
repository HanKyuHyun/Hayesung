import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import math

st.set_page_config(page_title="하예성 복지센터", layout="wide")
st.title("📄 하예성 명세서 (가로 정렬 및 날짜 수정)")

RATE_MAP = {'일반': 0.15, '감경(40%)': 0.09, '감경(60%)': 0.06, '의료': 0.06, '기초': 0.0}

def ceil_10(value):
    return math.ceil(value / 10) * 10

def draw_invoice(row, date_range, publish_date_str):
    total_amt = int(row['수가'])
    user_status = str(row['자격']).strip()
    rate = RATE_MAP.get(user_status, 0.15)
    own_amt = ceil_10(total_amt * rate) 
    pub_amt = total_amt - own_amt        
    
    # 1984 x 2806 원본 템플릿 로드
    img = Image.open("template.png").convert('RGB')
    draw = ImageDraw.Draw(img)
    
    try:
        # 고해상도에 맞춰 폰트 크기 키움
        f_name = ImageFont.truetype("malgun.ttf", 50) 
        f_main = ImageFont.truetype("malgun.ttf", 45)
        f_date = ImageFont.truetype("malgun.ttf", 38)
    except:
        f_name = f_main = f_date = ImageFont.load_default()

    # --- [좌표 대폭 수정: 원본 해상도 1984x2806 기준] ---
    
    # 1. 인적사항 (성명, 인정번호, 제공기간 Y축 725로 통일)
    Y_LINE = 725
    # 성명 (가장 왼쪽 칸)
    draw.text((220, Y_LINE), str(row['수급자명']), fill="black", font=f_name)
    # 인정번호 (성명 옆 빈 공간)
    draw.text((450, Y_LINE + 5), str(row['인정관리번호']), fill="black", font=f_main)
    # 제공기간 (중앙 급여제공기간 칸)
    draw.text((850, Y_LINE + 10), date_range, fill="black", font=f_date)
    
    # 2. 왼쪽 '급여' 항목 (X축을 800대, Y축을 1000~1300대로 조정)
    draw.text((830, 1050), f"{own_amt:,}", fill="black", font=f_main) 
    draw.text((830, 1170), f"{pub_amt:,}", fill="black", font=f_main) 
    draw.text((830, 1290), f"{total_amt:,}", fill="black", font=f_main) 
    
    # 3. 오른쪽 '금액산정내역' (X축 1300대)
    draw.text((1350, 1090), f"{total_amt:,}", fill="black", font=f_main) 
    draw.text((1350, 1330), f"{own_amt:,}", fill="black", font=f_main)   
    
    # 4. 수납금액 합계 (하단 큰 숫자 칸)
    draw.text((1450, 1740), f"{own_amt:,}", fill="black", font=f_name)
    
    # 5. 하단 날짜 (요청하신 년 월 일 표기)
    draw.text((1250, 2690), publish_date_str, fill="black", font=f_main)
    
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
    
    # 가로형 기간 표시
    date_range = f"{min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"
    # 하단 날짜 표기: 0000년 00월 00일
    publish_date_str = max_date.strftime('%Y년 %m월 %d일')
    
    df2['수가'] = pd.to_numeric(df2['수가'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    df2_sum = df2.groupby('수급자명')['수가'].sum().reset_index()
    final_df = pd.merge(df1, df2_sum, on='수급자명', how='inner')

    st.subheader("🔍 실시간 미리보기")
    selected_name = st.selectbox("수급자 선택", final_df['수급자명'].tolist())
    
    if selected_name:
        row = final_df[final_df['수급자명'] == selected_name].iloc[0]
        preview_img = draw_invoice(row, date_range, publish_date_str)
        st.image(preview_img, caption="가로 정렬 및 날짜 형식을 확인하세요.", use_container_width=True)

    if st.button("📥 전체 명세서 압축 생성"):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for _, row in final_df.iterrows():
                img = draw_invoice(row, date_range, publish_date_str)
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                zip_file.writestr(f"{row['수급자명']}_명세서.png", img_byte_arr.getvalue())
        st.download_button("📥 압축파일 받기", data=zip_buffer.getvalue(), file_name="하예성_명세서_최종보정.zip")
