import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
from datetime import datetime
import os

st.set_page_config(page_title="하예성 복지센터", layout="wide")
st.title("📄 하예성 복지센터 명세서 (한글 깨짐 & 크기 해결)")

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
    if st.button("🚀 명세서 일괄 생성 시작"):
        try:
            df1 = pd.read_excel(file1)
            df2 = pd.read_excel(file2)
            
            # --- 날짜 자동 계산 ---
            df2['일자'] = pd.to_datetime(df2['일자'])
            min_date = df2['일자'].min()
            max_date = df2['일자'].max()
            
            target_month = min_date.strftime('%Y년 %m월분')
            date_range = f"{min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"
            publish_date = max_date.strftime('%Y년 %m월 %d일')
            
            # 수가 계산
            df2['수가'] = pd.to_numeric(df2['수가'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            df2_sum = df2.groupby('수급자명')['수가'].sum().reset_index()
            
            final_df = pd.merge(df1, df2_sum, on='수급자명', how='inner')
            
            # 폰트 로드 (한글 깨짐 해결 및 크기 대폭 확대)
            font_path = "malgun.ttf" # 깃허브 창고에 이 파일이 꼭 있어야 합니다.
            
            try:
                # 거대 이미지($4960x7016$)에 맞춰 폰트 크기를 기존 200에서 1000 이상으로 키움
                font_title = ImageFont.truetype(font_path, 1200) # 제목용
                font_huge = ImageFont.truetype(font_path, 900)  # 성명 등 메인 정보
                font_large = ImageFont.truetype(font_path, 700) # 인정번호 등 서브 정보
            except Exception as e:
                # 폰트 파일이 없을 때 기본 폰트 사용 (기본 폰트는 한글이 깨지거나 작게 나옴)
                st.error(f"malgun.ttf 파일을 찾을 수 없습니다. 깃허브 창고에 파일을 올려주세요. 오류: {e}")
                font_title = font_huge = font_large = ImageFont.load_default()
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for _, row in final_df.iterrows():
                    total_pay = int(row['수가']) 
                    user_rate = RATE_MAP.get(row['자격'], 0.15) 
                    own_pay = int(total_pay * user_rate) 
                    pub_pay = total_pay - own_pay 
                    
                    try:
                        img = Image.open("template.png")
                        if img.mode != 'RGB': img = img.convert('RGB')
                    except:
                        st.error("이미지 오류! 깃허브에 template.png 파일이 있는지 확인해주세요.")
                        st.stop()

                    draw = ImageDraw.Draw(img)
                    
                    # --- [초고해상도 맞춤 좌표] ---
                    # 쥐꼬리만 한 글자가 보이게 좌표를 거대 이미지($4960x7016$)에 맞춰 전면 수정
                    # fill="blue"로 설정하여 흰 배경에 가장 잘 보이게 함
                    
                    # 0. 상단 제목 (0000년 00월분 장기요양급여 제공명세서)
                    # 좌표 (400, 300) -> (4000, 3000)으로 대폭 수정
                    draw.text((4000, 3000), f"{target_month} 급여제공명세서", fill="blue", font=font_title)
                    
                    # 1. 상단 정보
                    # (성명, 인정번호, 기간)
                    # 좌표 (150, 245) -> (1500, 2450) 등으로 대폭 수정
                    draw.text((1500, 2450), str(row['수급자명']), fill="blue", font=font_huge)
                    draw.text((1500, 2750), str(row['인정관리번호']), fill="blue", font=font_large)
                    draw.text((3800, 2450), date_range, fill="blue", font=font_large)
                    
                    # 2. 금액표
                    # 본인부담, 공단부담, 급여계
                    draw.text((3000, 3150), f"{own_pay:,}", fill="blue", font=font_huge)
                    draw.text((3000, 3400), f"{pub_pay:,}", fill="blue", font=font_huge)
                    draw.text((3000, 3650), f"{total_pay:,}", fill="blue", font=font_huge)
                    
                    # 우측 총액 부분
                    draw.text((5800, 3150), f"{total_pay:,}", fill="blue", font=font_huge)
                    draw.text((5800, 3500), f"{own_pay:,}", fill="blue", font=font_huge)
                    
                    # 3. 하단 발행일
                    # 좌표 (580, 755) -> (5800, 7550)으로 수정
                    draw.text((5800, 7550), publish_date, fill="blue", font=font_huge)
                    
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    zip_file.writestr(f"{row['수급자명']}_명세서.png", img_byte_arr.getvalue())
            
            st.success(f"완료! {len(final_df)}명의 명세서가 준비되었습니다.")
            st.download_button("📥 압축파일 다운로드", data=zip_buffer.getvalue(), file_name=f"명세서_{min_date.strftime('%Y%m')}.zip")
            
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
