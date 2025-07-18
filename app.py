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

st.set_page_config(page_title="충남고속 운행 대시보드", layout="centered")


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
  background-color: transparent !important;
  color: #222 !important;
  border: 2px solid #666 !important;
  padding: 0.5rem 1.2rem !important;
  font-weight: bold !important;
  border-radius: 8px !important;
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

/* ✅ 강조 클래스 예외 처리 - 여기에선 !important로 덮어쓰기 허용 */
span.eco-green { color: green !important; font-weight: bold !important; }
span.red-bold { color: red !important; font-weight: bold !important; }
span.orange-bold { color: orange !important; font-weight: bold !important; }
span.blue-bold { color: blue !important; font-weight: bold !important; }
span.grade-S, span.grade-A { color: green !important; font-weight: bold !important; }
div.grade-S, div.grade-A { color: green !important; font-weight: bold !important; }
span.grade-B, span.grade-C { color: orange !important; font-weight: bold !important; }
div.grade-B, div.grade-C { color: orange !important; font-weight: bold !important; }
span.grade-D, span.grade-F { color: red !important; font-weight: bold !important; }
div.grade-D, div.grade-F { color: red !important; font-weight: bold !important; }
            
.indicator-box {
  flex: 1;
  min-width: 200px;
  padding: 20px;
  margin: 5px;
  border: 1px solid #ccc;
  border-radius: 8px;
  background-color: #fff;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
            
.indicator-bar-bg {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  margin-top: 4px;
  background-color: #eee !important;
  padding: 0;
  position: relative;
  overflow: hidden;
}
.indicator-bar-fill {
  display: block !important;
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 8px;
  border-radius: 4px;
  z-index: 10;
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

@keyframes flicker {
  0%   {opacity: 1;}
  50%  {opacity: 0.3;}
  100% {opacity: 1;}
}

.flicker-text {
  font-size: 30px;
  font-weight: bold;
  color: #f39c12;
  animation: flicker 1s infinite;
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
        <h1 style='margin:0; font-size:32px;'>충남고속_나만의 운행 대시보드</h1>
    </div>
    <hr style='border:1px solid #ccc; margin-top:10px;'>
""", unsafe_allow_html=True)


user_input = st.text_input("운전자번호(ECO모니터 입력 아이디 / 핸드폰번호 뒤 4자리)를 입력하세요", "")
조회버튼 = st.button("조회하기")

if 조회버튼 and user_input:
    driver_id = int(user_input)

    if driver_id not in df_id_check['ECO관리번호'].values:
        st.warning("등록된 운전자가 아닙니다. 관리자에 등록 요청을 해주세요.")

    else:

        ### 1. 전체 지표 ###
        driver_name = df_id_check[df_id_check['ECO관리번호'] == driver_id].iloc[0]['성명']

        st.subheader(f"📌{driver_name}님의 전체 주행 지표📌")
        tang_filtered = df_tang[df_tang['운전자번호'] == driver_id].fillna('')
        driver_info = df_driver[df_driver['운전자ID'] == driver_id].fillna('')

        #등급에 따른 폰트색깔 함수
        def get_grade_color(this_grade):
            return f"<span class='grade-{this_grade}'>{this_grade}</span>"
            # if this_grade in ["S", "A"]:
            #     return "green"
            # elif this_grade in ["B", "C"]:
            #     return "orange"
            # else:
            #     return "red"

        if not driver_info.empty:
            driver_info_df = driver_info.iloc[0]
            rep_car = driver_info_df['주차량']
            rep_course = int(driver_info_df['주코스'])
            rep_route = driver_info_df['주노선']

            # st.markdown(f"""
            # <div class="flicker-text">🔥 최고속도 초과 주의!</div>
            # """, unsafe_allow_html=True)

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
                # grade_color = get_grade_color(driver_info_df['등급'])
                grade_value = driver_info_df['등급']
                grade_class = f"grade-{grade_value}"

                grade_text_map = {
                    "S": "S(최우수)",
                    "A": "A(우수)",
                    "B": "B(양호)",
                    "C": "C(보통)",
                    "D": "D(관리필요)",
                    "F": "F(관리필요)"
                }
                grade_text = grade_text_map.get(grade_value, grade_value)

                st.markdown(f"""
                <div style='display: flex; justify-content: space-around; padding: 20px; border: 1px solid #ccc; border-radius: 8px;'>
                <div style='text-align:center;'>
                    <div style='font-weight: bold;'>6월 등급</div>
                    <div class='{grade_class}' style='font-size: 40px; font-weight: bold;'>{grade_text}</div>
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

                #<div style='font-size: 40px; color: {grade_color}; font-weight: bold;'>{driver_info_df['등급']}</div>

                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

                # 비교 항목 시각화 함수
                def render_indicator(title, value, avg, unit="", reverse=False):
                    diff = value - avg
                    is_higher = diff > 0 if not reverse else diff < 0
                    label = "🔴 ⚠️ 평균보다 높습니다. 🔴" if is_higher else "🟢 평균보다 낮습니다. 🟢"
                    color = "#f87171" if is_higher else "#10b981"  # red or green

                    if "공회전율(%)" in title:
                        label = (
                            "🔴 연료낭비 중! 시동 건 후 바로 출발하기! 🔴" if is_higher 
                            else "🟢 실전 연비 마스터! 나무 5그루를 살렸어요! 🌳🟢"
                        )
                    elif "안전지수(급가속)" in title:
                        label = (
                            "🔴 급출발 금지! 탑승객도 놀라고 연료도 새요! 🔴" if is_higher 
                            else "🟢 승차감 최상! 고객 만족도 만점입니다! 👏"
                        )
                    elif "안전지수(급감속)" in title:
                        label = (
                            "⚠️ 급브레이크 위험! 미리 감속하세요! ⚠️" if is_higher 
                            else "🟢 예측운전 최고! 안전하게 감속했어요 👍"
                        )
                    elif "최고속도(km)" in title:
                        label = (
                            "🚨 속도도 좋지만 안전이 먼저입니다!" if is_higher 
                            else "🟢 속도 제어까지 완벽! 모범 운전! 🟢"
                        )
                    # 기본 멘트
                      # label = (
                      #     "⚠️ 평균보다 높습니다." if is_higher 
                      #     else "✅ 평균보다 낮습니다."
                      # )

                    return f"""
                    <div class='indicator-box'>
                        <div style='font-size: 20px; font-weight: bold;'>{title}</div>
                        <div style='font-size: 40px;'>{value}{unit}</div>
                        <div style='margin-top: 6px; font-size: 20px; font-weight: bold;'>{label}</div>
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
            df['연비'] = df['연비'].apply(lambda x: f"<span class='blue-bold'>{x:.2f}</span>")
            df['급가속(회)'] = df['급가속'].apply(lambda x: f"{x:.2f}")
            df['급감속(회)'] = df['급감속'].apply(lambda x: f"{x:.2f}")
            df['평균속도'] = df['평균속도'].apply(lambda x: f"{x:.0f}")
            df['공회전율(%)'] = df['공회전율(%)'].apply(lambda x: f"{x:.1f}%")
            df['저속구간(%)'] = df['저속구간(%)'].apply(lambda x: f"{x*100:.1f}%")
            df['경제구간(%)'] = df['경제구간(%)'].apply(lambda x: f"<span class='eco-green'>{x*100:.1f}%</span>")
            # df['경제구간(%)'] = df['경제구간(%)'].apply(lambda x: f"<span style='color:green; font-weight:bold;'>{x*100:.1f}%</span>")
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
            daily_grouped['연비'] = daily_grouped['연비'].apply(lambda x: f"<span class='blue-bold'>{x:.2f}</span>")
            daily_grouped['안전지수(급가속)'] = daily_grouped['안전지수(급가속)'].apply(lambda x: f"<b>{x:.2f}</b>")
            daily_grouped['안전지수(급감속)'] = daily_grouped['안전지수(급감속)'].apply(lambda x: f"<b>{x:.2f}</b>")
            daily_grouped['등급'] = daily_grouped['등급'].apply(get_grade_color)
            # daily_grouped['등급'] = daily_grouped['등급'].apply(lambda x: f"<span style='color:{get_grade_color(x)};'>{x}</span>")
            daily_grouped['경제속도구간(%)'] = daily_grouped['경제속도구간(%)'].apply(lambda x: f"{x:.0f}%" if pd.notnull(x) else '-')

            # 출력
            st.markdown(
                daily_grouped[['주행일', '차량번호', '노선', '코스', '주행거리(km)', '연비', '등급', '안전지수(급가속)', '안전지수(급감속)', '경제속도구간(%)', '최고속도(km/h)']].to_html(index=False, escape=False),
                unsafe_allow_html=True
            )



