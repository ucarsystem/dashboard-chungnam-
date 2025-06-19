import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import plotly.express as px
import base64
import requests
import numpy as np
from PIL import Image, ImageOps
import matplotlib as mpl 
import matplotlib.pyplot as plt 
import matplotlib.font_manager as fm  
import matplotlib.ticker as ticker
from openpyxl import load_workbook
import calendar
import datetime
import plotly.graph_objects as go

# 한글 폰트 설정
font_path = "./malgun.ttf"  # 또는 절대 경로로 설정 (예: C:/install/FINAL_APP/dashboard/malgun.ttf)
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['axes.unicode_minus'] = False

# Load Data
excel_path = './file/충남고속.xlsx'
id_check_path = './file/충남고속ID.xlsx'
df_tang = pd.read_excel(excel_path, sheet_name='탕데이터')
df_driver = pd.read_excel(excel_path, sheet_name='운전자별')
df_course_driver = pd.read_excel(excel_path, sheet_name='코스+운전자별')
df_id_check = pd.read_excel(id_check_path)
#추후 사용
month_input = 6

st.set_page_config(page_title="충남고속 연비 대시보드", layout="centered")


#방문자 조회 코드
# GA4_ID = "G-DFK7QQH1EH"  # 여기에 본인의 측정 ID를 입력
# st.markdown(
#     f"""
#     <!-- Global site tag (gtag.js) - Google Analytics -->
#     <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
#     <script>
#       window.dataLayer = window.dataLayer || [];
#       function gtag(){{dataLayer.push(arguments);}}
#       gtag('js', new Date());
#       gtag('config', '{GA4_ID}');
#     </script>
#     """,
#     unsafe_allow_html=True
# )

#font-size: 14px !important;

st.markdown("""
<style>
/*전체 기본 폰트 색 및 배경*/
body, div, span, p, table, td, th, label, input, textarea {
  color: #222 !important;
  background-color: #FFFFFF !important;
}
  
  /*제목 강조 */
h1, h2, h3, h4, h5 {
  color: #222 !important;
  font-weight: bold !important;
}

/*입력창 placeholder 대비 강화*/
input::placeholder {
  color: #666 !important;
  opacity: 1 !important;
}

/* 기본 버튼 스타일 수정 */
button[kind="primary"], .stButton > button {
  background-color: #222 !important;
  color: white !important;
  border: none !important;
  padding: 0.6rem 1.2rem !important;
  font-weight: bold !important;
  border-radius: 6px !important;
  width: 100%;
}
button[kind="primary"]:hover, .stButton > button:hover {
  background-color: #444 !important;
}
  
/* Plotly 모바일 차트 스타일 */
.js-plotly-plot .plotly .main-svg {
  font-size: 14px !important;
  color: #333 !important;
}

.legend text, .xtick text, .ytick text {
  fill: #333 !important; /* 차트 글씨색을 더 진하게 */
}

.main-svg .xtick text, .main-svg .ytick text, .main-svg .legend text {
  fill: #333 !important;
  font-size: 12px !important;
}
            
@media screen and (max-width: 600px) {
  html, body {
    font-size: 15px !important;
  }

  input {
    font-size: 16px !important;
  }

  .stButton > button {
    width: 100% !important;
    font-size: 16px !important;
  }
}
</style>
""", unsafe_allow_html=True)
#출력시작

# Base64 인코딩 함수
def get_base64_image(img_path):
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
    
logo_base64 = get_base64_image("./logo.png")

st.markdown(f"""
    <div style='display: flex; align-items: center; gap: 10px;'>
        <img src="data:image/png;base64,{logo_base64}" style='height:32px; width:auto;'>
        <h1 style='margin:0; font-size:32px;'>충남고속_나만의 연비 대시보드</h1>
    </div>
    <hr style='border:1px solid #ccc; margin-top:10px;'>
""", unsafe_allow_html=True)

# col1, col2 = st.columns([1, 8])
# with col1:
#     st.image("./logo.png", width=80)  # 로고 파일 경로 및 크기 설정

# with col2:
#     st.markdown("<h1 style='margin-bottom:0;'>충남고속_나만의 연비 대시보드</h1>", unsafe_allow_html=True)

user_input = st.text_input("운전자번호를 입력하세요", "")
조회버튼 = st.button("조회하기")

if 조회버튼 and user_input:
    driver_id = int(user_input)

    if driver_id not in df_id_check['ECO관리번호'].values:
        st.warning("등록된 운전자가 아닙니다. 관리자에 등록 요청을 해주세요.")

    else:

        ### 1. 전체 지표 ###
        driver_name = df_id_check[df_id_check['ECO관리번호'] == driver_id].iloc[0]['성명']

        st.subheader(f"📌{driver_name}님의 전체 주행 지표")
        tang_filtered = df_tang[df_tang['운전자번호'] == driver_id].fillna('')
        driver_info = df_driver[df_driver['운전자ID'] == driver_id].fillna('')

        #등급에 따른 폰트색깔 함수
        def get_grade_color(this_grade):
            if this_grade in ["S", "A"]:
                return "green"
            elif this_grade in ["B", "C"]:
                return "orange"
            else:
                return "red"

        if not driver_info.empty:
            driver_info_df = driver_info.iloc[0]
            rep_car = driver_info_df['주차량']
            rep_course = int(driver_info_df['주코스'])
            rep_route = driver_info_df['주노선']

            st.markdown(f"""
            <div style='display: flex; align-items: center; gap:12px'>
                <img src='https://img.icons8.com/color/48/bus.png'; style='height:50px; width:auto;'>
                <div>
                    <div><strong>대표 차량:</strong> {rep_car}</div>
                    <div><strong>노선:</strong> {rep_route}</div>
                    <div><strong>주코스:</strong> {rep_course}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            #간격
            st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)  # 간격 조절 (20px → 원하면 더 키워도 됨)

            driver_info['공회전율(%)'] = round(((driver_info['공회전시간'] / driver_info['주행시간']) * 100),2)
            driver_info['급가속(회/100km)'] = round(((driver_info['급가속횟수'] * 100) / driver_info['주행거리(km)']),2)
            driver_info['급감속(회/100km)'] = round(((driver_info['급감속횟수'] * 100) / driver_info['주행거리(km)']),2)

            box_style = """
                background-color: #fff;
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            """

            if not driver_info.empty:
                driver_info_df =  driver_info.iloc[0]
                grade_color = get_grade_color(driver_info_df['등급'])

                st.markdown(f"""
                <div style='display: flex; justify-content: space-around; padding: 20px; border: 1px solid #ccc; border-radius: 8px;'>
                <div style='text-align:center;'>
                    <div style='font-weight: bold;'>6월 등급</div>
                    <div style='font-size: 40px; color: {grade_color}; font-weight: bold;'>{driver_info_df['등급']}</div>
                </div>
                <div style='text-align:center;'>
                    <div style='font-weight: bold;'>주행거리</div>
                    <div style='font-size: 40px;'>{driver_info_df['주행거리(km)']:,.0f} km</div>
                </div>
                <div style='text-align:center;'>
                    <div style='font-weight: bold;'>연비</div>
                    <div style='font-size: 40px;'>{driver_info_df['연비(km/m3)']:.2f}</div>
                </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

                # 비교 항목 시각화 함수
                def render_indicator(title, value, avg, unit="", reverse=False):
                    diff = value - avg
                    is_higher = diff > 0 if not reverse else diff < 0
                    label = "⚠️ 평균보다 높습니다." if is_higher else "✅ 평균보다 낮습니다."
                    color = "#f87171" if is_higher else "#10b981"  # red or green
                    bar_value = min(abs(diff) * 100, 100) if avg !=0 else 0

                    return f"""

                    <div style='flex: 1; min-width: 200px; padding: 20px; margin: 5px; border: 1px solid #ccc; border-radius: 8px; background-color: #fff; text-align: center;'>
                        <div style='font-size: 20px;font-weight: bold;'>{title}</div>
                        <div style='font-size: 40px;'>{value}{unit}</div>
                        <div style='margin-top: 6px; font-size: 14px; font-weight: bold;'>{label}</div>
                        <div style='width: 100%; background-color: #eee; height: 8px; border-radius: 4px; margin-top: 4px;'>
                            <div style='height: 8px; background: {color}; width: {bar_value}%; border-radius: 4px;'></div>
                        </div>
                    </div>
                    """
                
                idle_avg = round(driver_info_df['노선평균공회전']*100)
                excel_avg = round(driver_info_df['노선평균안전지수(급가속)'],2)
                break_avg = round(driver_info_df['노선평균안전지수(급감속)'],2)
                maxspeed_avg = round(driver_info_df['노선평균최고속도'],1)

                my_idle = driver_info_df['공회전율(%)']
                my_excel = round(driver_info_df['급가속(회/100km)'],2)
                my_break = round(driver_info_df['급감속(회/100km)'],2)
                my_speed = driver_info_df['최고속도(km)']

                idle_html = render_indicator("공회전율(%)", my_idle, idle_avg, "%")
                excel_html = render_indicator("안전지수(급가속)", my_excel, excel_avg,"회")
                break_html = render_indicator("안전지수(급감속)", my_break, break_avg,"회")
                speed_html = render_indicator("최고속도(km)", my_speed, maxspeed_avg, " km/h")

                #출력
                # indicator_block = f"""
                # <div style='display: flex; justify-content: space-around; padding: 20px; border: 1px solid #ccc; border-radius: 8px;'>
                #     {idle_html}
                #     {excel_html}
                #     {break_html}
                #     {speed_html}
                # </div>
                # """
                st.markdown(idle_html, unsafe_allow_html=True)
                st.markdown(excel_html, unsafe_allow_html=True)
                st.markdown(break_html, unsafe_allow_html=True)
                st.markdown(speed_html, unsafe_allow_html=True)

                # col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
                # with col1:
                #     st.markdown(f"<div style='font-size: 20px; font-weight: bold;'>{int(month_input)}월 등급</div><div style='font-size: 60px; font-weight: bold; color: {grade_color};'>{driver_info_df['등급']}</div>", unsafe_allow_html=True)
                # with col2:
                #     st.markdown(f"<div style='font-size:24px; font-weight:bold;'>주행거리</div><div>{driver_info_df['주행거리(km)']:,.0f} km</div>", unsafe_allow_html=True)
                # with col3:
                #     st.markdown(f"<div style='font-size:24px; font-weight:bold;'>연비</div><div>{driver_info_df['연비(km/m3)']:.2f}</div>", unsafe_allow_html=True)
                # with col4:
                #     st.markdown(f"<div style='font-size:24px; font-weight:bold;'>공회전율</div><div>{driver_info_df['공회전율(%)']:.1f}%</div>", unsafe_allow_html=True)
                # with col5:
                #     st.markdown(f"<div style='font-size:24px; font-weight:bold;'>안전지수(급가속)</div><div>{driver_info_df['급가속(회/100km)']:.2f}</div>", unsafe_allow_html=True)
                # with col6:
                #     st.markdown(f"<div style='font-size:24px; font-weight:bold;'>안전지수(급감속)</div>{driver_info_df['급감속(회/100km)']:.2f}</div>", unsafe_allow_html=True)
                # with col7:
                #     st.markdown(f"<div style='font-size:24px; font-weight:bold;'>최고속도</div><div>{driver_info_df['최고속도(km)']} km/h</div>", unsafe_allow_html=True)

        else:
            st.info("사원님의 주행 데이터가 없습니다.")

        #간격
        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)  # 간격 조절 (20px → 원하면 더 키워도 됨)

        ### 2. 주행 코스별 운행기록 ###
        st.subheader("🚌 코스별 나의 운행 데이터")

        #반환함수
        def format_course_table(df):
            df = df.copy()
            df['주행거리'] = df['주행거리'].apply(lambda x: f"{int(x):,} km")
            df['연비'] = df['연비'].apply(lambda x: f"<span style='color:#4FC3F7; font-weight:bold;'>{x:.2f}</span>")
            df['급가속(회)'] = df['급가속'].apply(lambda x: f"{x:.2f}")
            df['급감속(회)'] = df['급감속'].apply(lambda x: f"{x:.2f}")
            df['평균속도'] = df['평균속도'].apply(lambda x: f"{x:.0f}")
            df['공회전율(%)'] = df['공회전율(%)'].apply(lambda x: f"{x:.1f}%")
            df['저속구간(%)'] = df['저속구간(%)'].apply(lambda x: f"{x*100:.1f}%")
            df['경제구간(%)'] = df['경제구간(%)'].apply(lambda x: f"<span style='color:green; font-weight:bold;'>{x*100:.1f}%</span>")
            df['과속구간(%)'] = df['과속구간(%)'].apply(lambda x: f"{x*100:.1f}%")
            df['등수'] = df['등수'].apply(lambda x: f"<b>{x}등</b>")
            return df
        
        course_filtered = df_course_driver[df_course_driver['운전자번호'] == driver_id].fillna('')

        if not course_filtered.empty:
            course_filtered['저속구간(%)'] = course_filtered['구간1비율'] + course_filtered['구간2비율']
            course_filtered['경제구간(%)'] = course_filtered['구간3비율'] + course_filtered['구간4비율']
            course_filtered['과속구간(%)'] = course_filtered['구간5비율'] + course_filtered['구간6비율'] + course_filtered['구간7비율']
            course_filtered['공회전율(%)'] = (course_filtered['공회전시간(초)'] / course_filtered['주행시간(초)']) * 100

            course_filtered_display = format_course_table(course_filtered)

            course_filtered_display = course_filtered_display.sort_values(by='주행거리', ascending=True)
            course_filtered_final = course_filtered_display[['노선','코스', '주행거리', '연비', '등수', '공회전율(%)', '급가속(회)', '급감속(회)', '평균속도', '최고속도', '저속구간(%)', '경제구간(%)', '과속구간(%)']]

            #출력
            st.write("""
            <style>
            td span {
                font-size: 15px;
            }
            table td {
                white-space: nowrap !important;
                text-align: center;
                vertical-align: middle;
            }
            </style>
            """, unsafe_allow_html=True)

            st.write(course_filtered_final.to_html(escape=False, index=False), unsafe_allow_html=True)

        #간격
        st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

        ### 3. 개인 vs 코스평균 비교 (연비) ###
        st.subheader("📈나의 연비 vs 코스 평균 연비")
        #코스별 평균연비
        course_filtered_graph = course_filtered
        course_filtered_graph['평균연비'] = round(course_filtered_graph['코스별 평균 연비'],2)
        course_filtered_graph['내 연비'] = round(course_filtered_graph['연비'],2)

        course_filtered_graph['코스(노선)'] = course_filtered_graph['코스'].astype(str) + "(" + course_filtered_graph['노선'].astype(str) + ")"

        # 순서 정렬 (필요 시)
        course_filtered_graph = course_filtered_graph.sort_values(by='코스')

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=course_filtered_graph['코스(노선)'],
            y=course_filtered_graph['내 연비'],
            name = '내 연비',
            marker_color = "#7FB3D5"
        ))
        fig.add_trace(go.Scatter(
            x=course_filtered_graph['코스(노선)'],
            y=course_filtered_graph['코스별 평균 연비'],
            name='코스별 평균연비',
            mode='lines+markers',
            line=dict(color="#E73A3A", width=2, dash='dash'),
        ))
        ##FF9E63
        fig.update_layout(
            title='',
            barmode='group',
            xaxis=dict(
                title='코스(노선)',
                type='category',
                tickangle=-15,
                gridcolor='#F0F0F0'
            ),
            yaxis=dict(
                title='연비(km/ℓ)',
                gridcolor='#F0F0F0',
                range=[1, max(course_filtered_graph[['내 연비','코스별 평균 연비']].max()) + 0.5]
            ),
            font=dict(size=14, family='Arial, sans-serif'),
            legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=40, r=40, t=60, b=40)
        )

        st.plotly_chart(fig, use_container_width=True)


        # 색상 정의 (로고 컬러에 맞춰 주황계열 + 보조색)
        # colors = ['#4C78A8', '#9FB2C6']  # 주황 계열 (로고 색과 유사)

        # # 막대그래프
        # fig = px.bar(
        #     course_filtered_graph,
        #     x='코스',
        #     y=['내 연비', '평균연비'],
        #     barmode='group',
        #     labels={'value':'연비 (km/ℓ)', 'variable':'결과'},
        #     color_discrete_sequence=colors
        # )

        # # X축 눈금 표시
        # fig.update_xaxes(
        #     tickmode='linear',  # 모든 코스 번호 다 보여주기
        #     dtick=1,            # 1단위 간격으로
        #     title_text='코스',
        #     gridcolor='#F0F0F0',
        #     zeroline=False
        # )

        # # Y축 레이블
        # fig.update_yaxes(
        #     title_text='연비(km/ℓ)',
        #     showgrid=True,
        #     gridcolor='#F0F0F0',
        #     zeroline=False
        # )

        # # 레이아웃 스타일
        # fig.update_layout(
        #     title = '',
        #     title_x=0.5,
        #     font=dict(size=14, family='Arial, sans-serif'),
        #     legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        #     plot_bgcolor='white',
        #     paper_bgcolor='white',
        #     margin=dict(l=40, r=40, t=60, b=40),
        # )

        # # 출력
        # st.plotly_chart(fig, use_container_width=True)

        # fig = px.bar(course_filtered, x='코스', y=['연비', '평균연비'], barmode='group', labels={'value':'연비', 'variable':'코스'})
        # st.plotly_chart(fig)

        ### 4. 일별 주행기록 ###
        st.subheader("📊 일별 주행기록")

        daily_grouped = tang_filtered.groupby(['DATE', '차량번호4', '노선', '코스', '목표연비설정', '운전자번호']).agg({
            '주행거리(km)': 'sum',
            '연료소모량(m3': 'sum',
            '구간3비율(%) 40-60 시간(초)': 'sum',
            '구간4비율(%) 60-80 시간(초)': 'sum',
            '공회전,웜업제외 시간': 'sum',
            '최고속도': 'max',
            '급가속횟수': 'sum',
            '급감속횟수': 'sum'
        }).reset_index()

        daily_grouped = daily_grouped[daily_grouped['운전자번호'] == driver_id].fillna('')

        if not daily_grouped.empty:

            daily_grouped['연비'] = daily_grouped['주행거리(km)'] / daily_grouped['연료소모량(m3']
            daily_grouped['안전지수(급가속)'] = daily_grouped['급가속횟수']*100 / daily_grouped['주행거리(km)']
            daily_grouped['안전지수(급감속)'] = daily_grouped['급감속횟수']*100 / daily_grouped['주행거리(km)']
            daily_grouped['최고속도(km/h)'] = daily_grouped['최고속도'] 

            daily_grouped = daily_grouped.fillna('')

            def grade(row):
                ratio = row['연비'] / row['목표연비설정']
                if ratio >= 1.0: return 'S'
                elif ratio >= 0.95: return 'A'
                elif ratio >= 0.9: return 'B'
                elif ratio >= 0.85: return 'C'
                elif ratio >= 0.8: return 'D'
                else: return 'F'

            daily_grouped['등급'] = daily_grouped.apply(grade, axis=1)
            daily_grouped['경제속도구간(%)'] = ((daily_grouped['구간3비율(%) 40-60 시간(초)'] + daily_grouped['구간4비율(%) 60-80 시간(초)']) / daily_grouped['공회전,웜업제외 시간']) * 100

            # 포맷팅
            daily_grouped = daily_grouped[daily_grouped['주행거리(km)'] >= 1]  # 1 미만 제거
            daily_grouped['DATE'] = pd.to_datetime(daily_grouped['DATE']).dt.strftime('%-m/%-d')
            daily_grouped['주행일'] = daily_grouped['DATE'] 
            daily_grouped['차량번호'] = daily_grouped['차량번호4']
            daily_grouped['코스'] = daily_grouped['코스'].astype(int)
            daily_grouped['주행거리(km)'] = daily_grouped['주행거리(km)'].apply(lambda x: f"{int(x):,} km")
            daily_grouped['연비'] = daily_grouped['연비'].apply(lambda x: f"<b><span style='color:#4FC3F7;'>{x:.2f}</span></b>")
            daily_grouped['안전지수(급가속)'] = daily_grouped['안전지수(급가속)'].apply(lambda x: f"<b>{x:.2f}</b>")
            daily_grouped['안전지수(급감속)'] = daily_grouped['안전지수(급감속)'].apply(lambda x: f"<b>{x:.2f}</b>")
            daily_grouped['등급'] = daily_grouped['등급'].apply(lambda x: f"<b><span style='color:{get_grade_color(x)};'>{x}</span></b>")
            daily_grouped['경제속도구간(%)'] = daily_grouped['경제속도구간(%)'].apply(lambda x: f"{x:.0f}%" if pd.notnull(x) else '-')

            # 출력
            st.markdown(
                daily_grouped[['주행일', '차량번호', '노선', '코스', '주행거리(km)', '연비', '등급', '안전지수(급가속)', '안전지수(급감속)', '경제속도구간(%)', '최고속도(km/h)']].to_html(index=False, escape=False),
                unsafe_allow_html=True
            )



