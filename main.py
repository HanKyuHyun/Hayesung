import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import math

st.set_page_config(page_title="하예성 복지센터", layout="wide")
st.title("📄 하예성 명세서 (폰트 축소 및 급여칸 보정)")

RATE_MAP = {'일반': 0.15, '감경(40%)': 0.09, '감경(60%)': 0.06, '의료': 0.06, '기초': 0.0}

def ceil_10(value):
    """1원 단위에서 올림하여 10원 단위로 만듦 (예: 123원 -> 130원)"""
    return math.ceil(value / 10) * 10

# --- 1. 이 함수가 반드시 먼저 나와야 합니다! ---
def format_amt(amt):
    """0원일 경우 '-'로 표시하고, 그 외에는 천단위 콤마 추가"""
    if amt == 0:
        return "-"
    return f"{amt:,}"

def draw_invoice(row, date_range, publish_date_str):
    total_amt = int(row['수가'])
    user_status = str(row['자격']).strip()
    rate = RATE_MAP.get(user_status, 0.15)
    own_amt = ceil_10(total_amt * rate) 
    pub_amt = total_amt - own_amt        
    
    img = Image.open("template.png").convert('RGB')
    draw = ImageDraw.Draw(img)
    
    try:
        # 사장님 요청: 기존 크기(48, 42, 36)의 약 2/3인 30~32 수준으로 축소
        f_name = ImageFont.truetype("malgun.ttf", 28) 
        f_main = ImageFont.truetype("malgun.ttf", 28)
        f_date = ImageFont.truetype("malgun.ttf", 24)
    except:
        f_name = f_main = f_date = ImageFont.load_default()

        
 # --- [1. 인적사항: 사장님 좌표 유지] ---
    Y_LINE = 780 
    draw.text((220, Y_LINE), str(row['수급자명']), fill="black", font=f_name)
    draw.text((380, Y_LINE + 5), str(row['인정관리번호']), fill="black", font=f_main)
    draw.text((635, Y_LINE + 10), date_range, fill="black", font=f_date)
    
    # --- [2. 급여항목: ₩ 기호 50px 우측 이동 및 0원 처리] ---
    # L_X: 580 -> 630 (50픽셀 우측 이동)
    # R_X: 950 (사장님 고정 좌표)
    L_X = 630  
    R_X = 950  
    
    # 본인부담금 (Y=888)
    draw.text((L_X, 888), "₩", fill="black", font=f_main)
    draw.text((R_X, 888), format_amt(own_amt), fill="black", font=f_main, anchor="ra")
    
    # 공단부담금 (Y=960)
    draw.text((L_X, 960), "₩", fill="black", font=f_main)
    draw.text((R_X, 960), format_amt(pub_amt), fill="black", font=f_main, anchor="ra")
    
    # 급여 계 (Y=1030)
    draw.text((L_X, 1030), "₩", fill="black", font=f_main)
    draw.text((R_X, 1030), format_amt(total_amt), fill="black", font=f_main, anchor="ra")
    
    # --- [3. 금액산정내역: 사장님 요청으로 수정 없음] ---
    R_L_X = 1280 
    R_R_X = 1670 
    
    # 총액 (Y=915)
    draw.text((R_L_X, 915), "₩", fill="black", font=f_main)
    draw.text((R_R_X, 915), format_amt(total_amt), fill="black", font=f_main, anchor="ra")
    
    # 본인부담총액 (Y=1010)
    draw.text((R_L_X, 1010), "₩", fill="black", font=f_main)
    draw.text((R_R_X, 1010), format_amt(own_amt), fill="black", font=f_main, anchor="ra")
    
    # 4. 하단 발행일
    draw.text((1350, 2050), publish_date_str, fill="black", font=f_main)
    
    return img

# --- 파일 업로드 및 데이터 처리 로직 ---
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
    date_range = f"{min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"
    publish_date_str = max_date.strftime('%Y년 %m월 %d일')
    
    df2['수가'] = pd.to_numeric(df2['수가'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    df2_sum = df2.groupby('수급자명')['수가'].sum().reset_index()
    final_df = pd.merge(df1, df2_sum, on='수급자명', how='inner')

    st.divider()
    selected_name = st.selectbox("어르신 성함을 선택하세요", final_df['수급자명'].tolist())
    
    if selected_name:
        row = final_df[final_df['수급자명'] == selected_name].iloc[0]
        preview_img = draw_invoice(row, date_range, publish_date_str)
        st.image(preview_img, caption="폰트가 작아지고 급여칸이 위/왼쪽으로 이동했습니다.", use_container_width=True)
    
    if st.button("🎁 최종 보정본으로 전체 압축 생성"):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for _, row in final_df.iterrows():
                img = draw_invoice(row, date_range, publish_date_str)
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                zip_file.writestr(f"{row['수급자명']}_명세서.png", img_byte_arr.getvalue())
        st.download_button("📥 압축파일 다운로드", data=zip_buffer.getvalue(), file_name="하예성_명세서_보정본.zip")
