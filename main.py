import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import math

st.set_page_config(page_title="하예성 복지센터", layout="wide")
st.title("📄 하예성 명세서 (최종 완성본)")

RATE_MAP = {'일반': 0.15, '감경(40%)': 0.09, '감경(60%)': 0.06, '의료': 0.06, '기초': 0.0}

# --- 1. 필수 계산 및 포맷 함수 ---
def ceil_10(value):
    """1원 단위에서 올림하여 10원 단위로 만듦"""
    return math.ceil(value / 10) * 10

def format_amt(amt):
    """0원일 경우 '-'로 표시, 그 외 천단위 콤마"""
    if amt == 0:
        return "-"
    return f"{amt:,}"

# --- 2. 명세서 그리기 함수 (seq_num 매개변수 추가!) ---
def draw_invoice(row, date_range, publish_date_str, seq_num):
    total_amt = int(row['수가'])
    user_status = str(row['자격']).strip()
    rate = RATE_MAP.get(user_status, 0.15)
    own_amt = ceil_10(total_amt * rate) 
    pub_amt = total_amt - own_amt        
    
    img = Image.open("template.png").convert('RGB')
    draw = ImageDraw.Draw(img)
    
    try:
        f_name = ImageFont.truetype("malgun.ttf", 28) 
        f_main = ImageFont.truetype("malgun.ttf", 28)
        f_date = ImageFont.truetype("malgun.ttf", 24)
    except:
        f_name = f_main = f_date = ImageFont.load_default()

    # [0. 영수증 번호 추가]
    # 사장님 요청 좌표: (1350, 780)
    receipt_no = f"2026-03-{seq_num:02d}" 
    draw.text((1250, 780), receipt_no, fill="black", font=f_main)

    # [1. 인적사항: 사장님 고정 좌표]
    Y_LINE = 780 
    draw.text((220, Y_LINE), str(row['수급자명']), fill="black", font=f_name)
    draw.text((380, Y_LINE + 5), str(row['인정관리번호']), fill="black", font=f_main)
    draw.text((635, Y_LINE + 10), date_range, fill="black", font=f_date)
    
    # [2. 급여항목: ₩ 630 고정 & 숫자 우측정렬]
    L_X, R_X = 630, 950  
    draw.text((L_X, 888), "₩", fill="black", font=f_main)
    draw.text((R_X, 888), format_amt(own_amt), fill="black", font=f_main, anchor="ra")
    draw.text((L_X, 960), "₩", fill="black", font=f_main)
    draw.text((R_X, 960), format_amt(pub_amt), fill="black", font=f_main, anchor="ra")
    draw.text((L_X, 1030), "₩", fill="black", font=f_main)
    draw.text((R_X, 1030), format_amt(total_amt), fill="black", font=f_main, anchor="ra")
    
    # [3. 금액산정내역: 사장님 고정 좌표]
    R_L_X, R_R_X = 1280, 1670 
    draw.text((R_L_X, 915), "₩", fill="black", font=f_main)
    draw.text((R_R_X, 915), format_amt(total_amt), fill="black", font=f_main, anchor="ra")
    draw.text((R_L_X, 1010), "₩", fill="black", font=f_main)
    draw.text((R_R_X, 1010), format_amt(own_amt), fill="black", font=f_main, anchor="ra")
    
    # 4. 하단 발행일
    draw.text((1350, 2050), publish_date_str, fill="black", font=f_main)
    
    return img

# --- 3. 파일 업로드 및 데이터 처리 ---
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

    # [중요] 순번 계산을 위해 names 리스트를 여기서 생성합니다.
    names = final_df['수급자명'].tolist()

    st.divider()
    selected_name = st.selectbox("어르신 성함을 선택하세요", names)
    
    if selected_name:
        idx = names.index(selected_name) + 1 
        row = final_df[final_df['수급자명'] == selected_name].iloc[0]
        # 함수에 idx(순번)를 함께 전달합니다.
        preview_img = draw_invoice(row, date_range, publish_date_str, idx)
        st.image(preview_img, caption=f"영수증 번호: 2026-03-{idx:02d}가 적용되었습니다.", use_container_width=True)
    
    if st.button("🎁 최종 보정본으로 전체 압축 생성"):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            # 전체 압축 시에도 i(순번)를 전달하도록 수정했습니다.
            for i, (_, row) in enumerate(final_df.iterrows(), 1):
                img = draw_invoice(row, date_range, publish_date_str, i)
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                zip_file.writestr(f"{i:02d}_{row['수급자명']}_명세서.png", img_byte_arr.getvalue())
        st.download_button("📥 압축파일 다운로드", data=zip_buffer.getvalue(), file_name="하예성_명세서_최종본.zip")
