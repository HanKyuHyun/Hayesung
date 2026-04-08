import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import math

st.set_page_config(page_title="하예성 복지센터", layout="wide")
st.title("📄 하예성 복지센터 명세서 (최종 정밀 교정)")

# 1. 요율표 (계산용으로만 사용, 출력 안 함)
RATE_MAP = {'일반': 0.15, '감경(40%)': 0.09, '감경(60%)': 0.06, '의료': 0.06, '기초': 0.0}

def ceil_10(value):
    """원단위 무조건 올림"""
    return math.ceil(value / 10) * 10

col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("1. 수급자구분변경이력 (xlsx)", type=['xlsx'])
with col2:
    file2 = st.file_uploader("2. 일정계획 (xlsx)", type=['xlsx'])

if file1 and file2:
    if st.button("🚀 최종 명세서 발행"):
        try:
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
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for _, row in final_df.iterrows():
                    # 금액 계산 (절상)
                    total_amt = int(row['수가'])
                    user_status = str(row['자격']).strip()
                    rate = RATE_MAP.get(user_status, 0.15)
                    own_amt = ceil_10(total_amt * rate) 
                    pub_amt = total_amt - own_amt        
                    
                    # 이미지 로드
                    img = Image.open("template.png").convert('RGB')
                    draw = ImageDraw.Draw(img)
                    
                    try:
                        # 폰트 크기 하향 조정 (칸 넘침 방지)
                        f_name = ImageFont.truetype("malgun.ttf", 45) # 성명/합계
                        f_main = ImageFont.truetype("malgun.ttf", 40) # 일반 텍스트/숫자
                        f_date = ImageFont.truetype("malgun.ttf", 35) # 기간
                    except:
                        f_name = f_main = f_date = ImageFont.load_default()

                    # --- [정밀 좌표 재설정] ---
                    
                    # 1. 인적사항
                    draw.text((220, 260), str(row['수급자명']), fill="black", font=f_name)
                    draw.text((220, 310), str(row['인정관리번호']), fill="black", font=f_main)
                    draw.text((430, 310), date_range, fill="black", font=f_date)
                    
                    # 2. 왼쪽 급여 항목 (본인부담, 공단부담, 급여계)
                    draw.text((450, 420), f"{own_amt:,}", fill="black", font=f_main) 
                    draw.text((450, 470), f"{pub_amt:,}", fill="black", font=f_main) 
                    draw.text((450, 520), f"{total_amt:,}", fill="black", font=f_main) 
                    
                    # 3. 오른쪽 금액산정내역 (총액, 본인총액)
                    draw.text((920, 435), f"{total_amt:,}", fill="black", font=f_main)
                    draw.text((920, 535), f"{own_amt:,}", fill="black", font=f_main)
                    
                    # 4. 수납금액 합계 (하단 큰 칸)
                    draw.text((1050, 1120), f"{own_amt:,}", fill="black", font=f_name)
                    
                    # 5. 최하단 발행 날짜
                    draw.text((950, 2450), publish_date, fill="black", font=f_main)
                    
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    zip_file.writestr(f"{row['수급자명']}_명세서.png", img_byte_arr.getvalue())
            
            st.success(f"✅ {len(final_df)}건 발행 완료! 폰트 및 요율 정리됨.")
            st.download_button("📥 압축파일 다운로드", data=zip_buffer.getvalue(), file_name="하예성_명세서_최종.zip")
            
        except Exception as e:
            st.error(f"오류: {e}")
