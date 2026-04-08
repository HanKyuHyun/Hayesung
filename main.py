import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import math

st.set_page_config(page_title="하예성 복지센터", layout="wide")
st.title("📄 하예성 명세서 (칸 중심 정밀 보정)")

RATE_MAP = {'일반': 0.15, '감경(40%)': 0.09, '감경(60%)': 0.06, '의료': 0.06, '기초': 0.0}

def ceil_10(value):
    return math.ceil(value / 10) * 10

def draw_invoice(row, date_range, publish_date):
    total_amt = int(row['수가'])
    user_status = str(row['자격']).strip()
    rate = RATE_MAP.get(user_status, 0.15)
    own_amt = ceil_10(total_amt * rate) 
    pub_amt = total_amt - own_amt        
    
    # 1984 x 2806 원본 템플릿 로드
    img = Image.open("template.png").convert('RGB')
    draw = ImageDraw.Draw(img)
    
    try:
        # 칸 크기에 비해 글자가 너무 크지 않게 조절
        f_name = ImageFont.truetype("malgun.ttf", 52) 
        f_main = ImageFont.truetype("malgun.ttf", 45)
        f_date = ImageFont.truetype("malgun.ttf", 38)
    except:
        f_name = f_main = f_date = ImageFont.load_default()

    # --- [이미지 분석 기반 정밀 좌표 - 칸 중앙 타겟팅] ---
    
    # 1. 인적사항 (성명/인정번호 왼쪽 정렬, 제공기간은 오른쪽 칸)
    # 성명 (Y축 720 라인으로 대폭 하향)
    draw.text((250, 725), str(row['수급자명']), fill="black", font=f_name)
    # 인정번호 (성명 바로 아래칸 중앙)
    draw.text((250, 830), str(row['인정관리번호']), fill="black", font=f_main)
    # 제공기간 (인정번호와 같은 높이, 오른쪽 칸 시작점)
    draw.text((680, 725), date_range, fill="black", font=f_date)
    
    # 2. 왼쪽 '급여' 항목 금액 (X축을 750->850으로 밀어서 칸 중앙 배치)
    draw.text((850, 1055), f"{own_amt:,}", fill="black", font=f_main) # 본인부담
    draw.text((850, 1175), f"{pub_amt:,}", fill="black", font=f_main) # 공단부담
    draw.text((850, 1295), f"{total_amt:,}", fill="black", font=f_main) # 급여계
    
    # 3. 오른쪽 '금액산정내역' (X축을 1200->1350으로 밀어서 중앙 배치)
    draw.text((1350, 1095), f"{total_amt:,}", fill="black", font=f_main) # 총액
    draw.text((1350, 1335), f"{own_amt:,}", fill="black", font=f_main)   # 본인총액
    
    # 4. 수납금액 합계 (하단 큰 숫자 칸)
    draw.text((1480, 1750), f"{own_amt:,}", fill="black", font=f_name)
    
    # 5. 하단 날짜 (발행일)
    draw.text((1350, 2700), publish_date, fill="black", font=f_main)
    
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
    date_range = f"{min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"
    publish_date = max_date.strftime('%Y    %m    %d')
    
    df2['수가'] = pd.to_numeric(df2['수가'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    df2_sum = df2.groupby('수급자명')['수가'].sum().reset_index()
    final_df = pd.merge(df1, df2_sum, on='수급자명', how='inner')

    st.subheader("🔍 실시간 미리보기 (선택하여 확인)")
    selected_name = st.selectbox("수급자 선택", final_df['수급자명'].tolist())
    
    if selected_name:
        row = final_df[final_df['수급자명'] == selected_name].iloc[0]
        preview_img = draw_invoice(row, date_range, publish_date)
        # 이미지를 크게 보여줌
        st.image(preview_img, caption="이게 현재 좌표 결과입니다. 칸 중앙에 오는지 확인해주세요.", use_container_width=True)

    if st.button("📥 이대로 전체 압축파일 생성"):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for _, row in final_df.iterrows():
                img = draw_invoice(row, date_range, publish_date)
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                zip_file.writestr(f"{row['수급자명']}_명세서.png", img_byte_arr.getvalue())
        st.download_button("📥 압축파일 받기", data=zip_buffer.getvalue(), file_name="하예성_명세서_정밀보정.zip")
