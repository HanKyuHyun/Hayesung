import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import math

st.set_page_config(page_title="하예성 복지센터", layout="wide")
st.title("📄 하예성 명세서 (최종 좌표 보정 및 완성본)")

# 요율표
RATE_MAP = {'일반': 0.15, '감경(40%)': 0.09, '감경(60%)': 0.06, '의료': 0.06, '기초': 0.0}

def ceil_10(value):
    """원단위 무조건 올림"""
    return math.ceil(value / 10) * 10

def draw_invoice(row, date_range, publish_date_str):
    total_amt = int(row['수가'])
    user_status = str(row['자격']).strip()
    rate = RATE_MAP.get(user_status, 0.15)
    own_amt = ceil_10(total_amt * rate) 
    pub_amt = total_amt - own_amt        
    
    # 원본 템플릿 로드 (1984 x 2806 기준)
    img = Image.open("template.png").convert('RGB')
    draw = ImageDraw.Draw(img)
    
    try:
        f_name = ImageFont.truetype("malgun.ttf", 48) 
        f_main = ImageFont.truetype("malgun.ttf", 42)
        f_date = ImageFont.truetype("malgun.ttf", 36)
    except:
        f_name = f_main = f_date = ImageFont.load_default()

    # --- [사장님 피드백 반영: 왼쪽 & 아래로 조정] ---
    Y_LINE = 760 # 이전보다 아래로 내림

    # 1. 인적사항 (가로로 나란히, 더 왼쪽으로 당김)
    draw.text((180, Y_LINE), str(row['수급자명']), fill="black", font=f_name)
    draw.text((380, Y_LINE + 5), str(row['인정관리번호']), fill="black", font=f_main)
    draw.text((720, Y_LINE + 10), date_range, fill="black", font=f_date)
    
    # 2. 왼쪽 '급여' 항목 (칸 중앙에 맞춰 하향)
    draw.text((830, 1080), f"{own_amt:,}", fill="black", font=f_main) 
    draw.text((830, 1200), f"{pub_amt:,}", fill="black", font=f_main) 
    draw.text((830, 1320), f"{total_amt:,}", fill="black", font=f_main) 
    
    # 3. 오른쪽 '금액산정내역'
    draw.text((1350, 1120), f"{total_amt:,}", fill="black", font=f_main) 
    draw.text((1350, 1360), f"{own_amt:,}", fill="black", font=f_main)   
    
    # 4. 하단 발행일 (년 월 일 표기)
    draw.text((1250, 2700), publish_date_str, fill="black", font=f_main)
    
    return img

# --- 파일 업로드 로직 ---
col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("1. 수급자구분변경이력 (xlsx)", type=['xlsx'])
with col2:
    file2 = st.file_uploader("2. 일정계획 (xlsx)", type=['xlsx'])

if file1 and file2:
    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)
    
    # 날짜 및 기간 처리
    df2['일자'] = pd.to_datetime(df2['일자'])
    min_date = df2['일자'].min()
    max_date = df2['일자'].max()
    date_range = f"{min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"
    publish_date_str = max_date.strftime('%Y년 %m월 %d일')
    
    # 수가 합계 계산
    df2['수가'] = pd.to_numeric(df2['수가'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    df2_sum = df2.groupby('수급자명')['수가'].sum().reset_index()
    final_df = pd.merge(df1, df2_sum, on='수급자명', how='inner')

    # --- 미리보기 섹션 ---
    st.divider()
    st.subheader("🔍 실시간 위치 확인")
    selected_name = st.selectbox("어르신 성함을 선택하세요", final_df['수급자명'].tolist())
    
    if selected_name:
        row = final_df[final_df['수급자명'] == selected_name].iloc[0]
        preview_img = draw_invoice(row, date_range, publish_date_str)
        st.image(preview_img, caption=f"[{selected_name}]님 미리보기", use_container_width=True)
    
    # --- 전체 압축파일 생성 및 다운로드 ---
    st.divider()
    if st.button("🎁 위 위치대로 전체 명세서 압축 생성"):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for _, row in final_df.iterrows():
                img = draw_invoice(row, date_range, publish_date_str)
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                zip_file.writestr(f"{row['수급자명']}_명세서.png", img_byte_arr.getvalue())
        
        st.download_button("📥 압축파일 다운로드", data=zip_buffer.getvalue(), file_name="하예성_명세서_전체.zip")
