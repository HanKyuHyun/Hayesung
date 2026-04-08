import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
from datetime import datetime

st.set_page_config(page_title="하예성 복지센터 명세서", layout="wide")
st.title("📄 하예성 복지센터 명세서 자동 생성기")

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
    if st.button("🚀 명세서 일괄 생성 및 압축하기"):
        try:
            df1 = pd.read_excel(file1)
            df2 = pd.read_excel(file2)
            
            # --- 날짜 자동 계산 ---
            df2['일자'] = pd.to_datetime(df2['일자'])
            min_date = df2['일자'].min()
            max_date = df2['일자'].max()
            date_range = f"{min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"
            publish_date = max_date.strftime('%Y년 %m월 %d일')
            
            # 수가 계산
            df2['수가'] = pd.to_numeric(df2['수가'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            df2_sum = df2.groupby('수급자명')['수가'].sum().reset_index()
            
            final_df = pd.merge(df1, df2_sum, on='수급자명', how='inner')
            
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
                    
                    # 💡 거대 이미지에 맞춘 대형 폰트 설정 (기본 크기 10배 이상)
                    try:
                        font_huge = ImageFont.truetype("malgun.ttf", 250) # 성명 등 메인 정보
                        font_large = ImageFont.truetype("malgun.ttf", 180) # 인정번호 등 서브 정보
                    except:
                        # 맑은고딕 없으면 기본폰트 사용 (기본폰트는 작아서 안보일수 있습니다)
                        font_huge = font_large = ImageFont.load_default()
                        st.warning("malgun.ttf 폰트 파일이 없어 기본 폰트를 사용합니다. 글자가 매우 작게 보일 수 있습니다.")
                    
                    # --- [초고해상도 맞춤 좌표 섹션] ---
                    # 사장님 양식의 정확한 위치는 모르지만, 이 거대 이미지 크기에 맞춘 대략적인 좌표입니다.
                    # 결과물을 보시고 숫자를 조절해주세요.
                    
                    # 1. 상단 정보
                    # (성명, 인정번호, 기간)
                    draw.text((1500, 2450), str(row['수급자명']), fill="black", font=font_huge)
                    draw.text((1500, 2750), str(row['인정관리번호']), fill="black", font=font_large)
                    draw.text((3800, 2450), date_range, fill="black", font=font_large)
                    
                    # 2. 금액표 (중앙 및 우측 상단 칸 등)
                    # 본인부담, 공단부담, 급여계
                    draw.text((3000, 3150), f"{own_pay:,}", fill="black", font=font_huge)
                    draw.text((3000, 3400), f"{pub_pay:,}", fill="black", font=font_huge)
                    draw.text((3000, 3650), f"{total_pay:,}", fill="black", font=font_huge)
                    
                    # 우측 총액 부분
                    draw.text((5800, 3150), f"{total_pay:,}", fill="black", font=font_huge)
                    draw.text((5800, 3500), f"{own_pay:,}", fill="black", font=font_huge)
                    
                    # 3. 하단 발행일 (말일)
                    # 대표자 위쪽 적절한 위치 (Y좌표 755 -> 7550으로 변경)
                    draw.text((5800, 7550), publish_date, fill="black", font=font_huge)
                    
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    zip_file.writestr(f"{row['수급자명']}_명세서.png", img_byte_arr.getvalue())
            
            st.success(f"성공! {publish_date} 발행분 ({len(final_df)}명)")
            st.download_button("📥 전체 명세서 다운로드", data=zip_buffer.getvalue(), file_name=f"하예성_명세서_{min_date.strftime('%Y%m')}.zip")
            
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
