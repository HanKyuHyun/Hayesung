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
    return math.ceil(value / 10) * 10

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

    # --- [좌표 수정: 급여 항목 왼쪽 30, 위 100 이동] ---
    
   # 1. 인적사항: 더 왼쪽으로, 더 아래로 (Y축 760 -> 785)
    Y_LINE = 785 
    draw.text((170, Y_LINE), str(row['수급자명']), fill="black", font=f_name) # X: 180->150
    draw.text((370, Y_LINE + 5), str(row['인정관리번호']), fill="black", font=f_main) # X: 380->350
    draw.text((550, Y_LINE + 10), date_range, fill="black", font=f_date) # X: 720->700
    
    # 2. 왼쪽 '급여' 항목: 요청대로 위로 100 올리고, 왼쪽으로 더 많이(800->750) 이동
    draw.text((750, 880), f"{own_amt:,}", fill="black", font=f_main) 
    draw.text((750, 930), f"{pub_amt:,}", fill="black", font=f_main) 
    draw.text((750, 980), f"{total_amt:,}", fill="black", font=f_main) 
    
    # 3. 오른쪽 '금액산정내역': 오른쪽 선 침범 방지를 위해 왼쪽으로 많이 당김 (1350->1250)
    draw.text((1250, 950), f"{total_amt:,}", fill="black", font=f_main) 
    draw.text((1250, 1050), f"{own_amt:,}", fill="black", font=f_main)
  
    # 4. 하단 발행일
    draw.text((1250, 1950), publish_date_str, fill="black", font=f_main)
    
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
