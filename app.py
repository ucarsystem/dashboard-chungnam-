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

# 한글 폰트 설정
font_path = "./malgun.ttf"  # 또는 절대 경로로 설정 (예: C:/install/FINAL_APP/dashboard/malgun.ttf)
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['axes.unicode_minus'] = False

# Load Data
excel_path = './file/충남고속.xlsx'
df_tang = pd.read_excel(excel_path, sheet_name='탕데이터')
df_driver = pd.read_excel(excel_path, sheet_name='운전자별')
df_course_driver = pd.read_excel(excel_path, sheet_name='코스+운전자별')
#추후 사용
month_input = 6

#출력시작
# st.set_page_config(page_title="충남고속 연비 대시보드", layout="wide")

# Base64 인코딩 함수
def get_base64_image(img_path):
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
    
logo_path = "./logo.png"
logo_base64 = get_base64_image(logo_path)

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

driver_id = st.text_input("운전자번호를 입력하세요", "")
조회버튼 = st.button("조회하기")

if 조회버튼 and driver_id:
    driver_id = int(driver_id)
    
    ### 1. 전체 지표 ###
    st.subheader("📌전체 주행 지표")
    tang_filtered = df_tang[df_tang['운전자번호'] == driver_id]
    if not tang_filtered.empty:
        rep_car = tang_filtered.groupby('차량번호4')['주행거리(km)'].sum().idxmax()
        rep_course = int(tang_filtered.groupby('코스')['주행거리(km)'].sum().idxmax())
        rep_route = tang_filtered[tang_filtered['차량번호4'] == rep_car]['노선번호'].mode()[0]

        grade_color = {"S": "🟩", "A": "🟩", "B": "🟨", "C": "🟨", "D": "🟥", "F": "🟥"}
        
        #등급에 따른 폰트색깔 함수
        def get_grade_color(this_grade):
            if this_grade in ["S", "A"]:
                return "green"
            elif this_grade in ["B", "C"]:
                return "orange"
            else:
                return "red"

        st.markdown(f"""
        <div style='display: flex; align-items: center; gap:12px'>
            <img src='https://img.icons8.com/color/48/bus.png'; style='height:30px; width:auto;'>
            <div>
                <div><strong>대표 차량:</strong> {rep_car}</div>
                <div><strong>노선:</strong> {rep_route}</div>
                <div><strong>주코스:</strong> {rep_course}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        #간격
        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)  # 간격 조절 (20px → 원하면 더 키워도 됨)

        driver_info = df_driver[df_driver['운전자ID'] == driver_id].copy()
        driver_info['공회전율(%)'] = round(((driver_info['공회전시간'] / driver_info['주행시간']) * 100),2)
        driver_info['급가속(회/100km)'] = round(((driver_info['급가속횟수'] * 100) / driver_info['주행거리(km)']),2)
        driver_info['급감속(회/100km)'] = round(((driver_info['급감속횟수'] * 100) / driver_info['주행거리(km)']),2)

        if not driver_info.empty:
            driver_info_df = driver_info.iloc[0]
            grade_color = get_grade_color(driver_info_df['등급'])

            col1, col2, col3, col4, col5, col6 = st.columns(6)
            with col1:
                st.markdown(f"<div style='font-size: 20px; font-weight: bold;'>{int(month_input)}월 등급</div><div style='font-size: 60px; font-weight: bold; color: {grade_color};'>{driver_info_df['등급']}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div style='font-size:24px; font-weight:bold;'>{driver_info_df['주행거리(km)']:,.0f} km</div><div>주행거리</div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div style='font-size:24px; font-weight:bold;'>{driver_info_df['연비(km/m3)']:.2f}</div><div>연비</div>", unsafe_allow_html=True)
            with col4:
                st.markdown(f"<div style='font-size:24px; font-weight:bold;'>{driver_info_df['공회전율(%)']:.1f}%</div><div>공회전율</div>", unsafe_allow_html=True)
            with col5:
                st.markdown(f"<div style='font-size:24px; font-weight:bold;'>{driver_info_df['급감속(회/100km)']:.2f}</div><div>안전지수(급감속)</div>", unsafe_allow_html=True)
            with col6:
                st.markdown(f"<div style='font-size:24px; font-weight:bold;'>{driver_info_df['평균속도']:.1f} km/h</div><div>평균속도</div>", unsafe_allow_html=True)

    ### 2. 주행 코스별 운행기록 ###
    st.subheader("코스별 나의 운행 데이터")

    #반환함수수
    def format_course_table(df):
        df = df.copy()
        df['주행거리'] = df['주행거리'].apply(lambda x: f"{int(x):,} km")
        df['연비'] = df['연비'].apply(lambda x: f"<span style='color:blue;'>{x:.2f}</span>")
        df['급감속'] = df['급감속'].apply(lambda x: f"{x:.2f}")
        df['평균속도'] = df['평균속도'].apply(lambda x: f"{x:.2f}")
        df['공회전율(%)'] = df['공회전율(%)'].apply(lambda x: f"{x:.1f}%")
        df['저속구간(%)'] = df['저속구간(%)'].apply(lambda x: f"{x*100:.1f}%")
        df['경제구간(%)'] = df['경제구간(%)'].apply(lambda x: f"<span style='color:green; font-weight:bold;'>{x*100:.1f}%</span>")
        df['과속구간(%)'] = df['과속구간(%)'].apply(lambda x: f"{x*100:.1f}%")
        df['등수'] = df['등수'].apply(lambda x: f"<b>{x}등</b>")
        return df
    
    course_filtered = df_course_driver[df_course_driver['운전자번호'] == driver_id].copy()
    course_filtered['저속구간(%)'] = course_filtered['구간1비율'] + course_filtered['구간2비율']
    course_filtered['경제구간(%)'] = course_filtered['구간3비율'] + course_filtered['구간4비율']
    course_filtered['과속구간(%)'] = course_filtered['구간5비율'] + course_filtered['구간6비율'] + course_filtered['구간7비율']
    course_filtered['공회전율(%)'] = (course_filtered['공회전시간(초)'] / course_filtered['주행시간(초)']) * 100

    course_filtered_display = format_course_table(course_filtered)

    course_filtered_display = course_filtered_display.sort_values(by='주행거리', ascending=False)
    course_filtered_final = course_filtered_display[['코스', '주행거리', '연비', '공회전율(%)', '급감속', '평균속도', '저속구간(%)', '경제구간(%)', '과속구간(%)', '등수']]

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

    ### 3. 개인 vs 코스평균 비교 (연비) ###
    st.subheader("나의 연비 vs 코스 평균 연비")
    #코스별 평균연비
    course_mean_grade = df_course_driver.groupby('코스')['연비'].mean().reset_index().rename(columns={'연비': '평균연비'})

    # 개인 데이터와 병합 (코스 기준)
    course_filtered = course_filtered.merge(course_mean_grade, on='코스', how='left')

    # 색상 정의 (로고 컬러에 맞춰 주황계열 + 보조색)
    colors = ['#4C78A8', '#9FB2C6']  # 주황 계열 (로고 색과 유사)

    # 막대그래프
    fig = px.bar(
        course_filtered,
        x='코스',
        y=['연비', '평균연비'],
        barmode='group',
        labels={'value':'냐의 연비', 'variable':'코스별평균연비'},
        color_discrete_sequence=colors
    )

    # X축 눈금 표시
    fig.update_xaxes(
        tickmode='linear',  # 모든 코스 번호 다 보여주기
        dtick=1,            # 1단위 간격으로
        title_text='코스'
        gridcolor='#F0F0F0',
        zeroline=False
    )

    # Y축 레이블
    fig.update_yaxes(
        title_text='연비(km/ℓ)',
        showgrid=True,
        gridcolor='#F0F0F0',
        zeroline=False
    )

    # 레이아웃 스타일
    fig.update_layout(
        title_x=0.5,
        font=dict(size=14, family='Arial, sans-serif', color='#333333'),
        legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=40, r=40, t=60, b=40),
    )

    # 출력
    st.plotly_chart(fig, use_container_width=True)

    # fig = px.bar(course_filtered, x='코스', y=['연비', '평균연비'], barmode='group', labels={'value':'연비', 'variable':'코스'})
    # st.plotly_chart(fig)

    ### 4. 일별 주행기록 ###
    st.subheader("일별 주행기록")
    daily_grouped = tang_filtered.groupby(['DATE', '차량번호4', '코스', '목표연비']).agg({
        '주행거리(km)': 'sum',
        '연료소모량(m3': 'sum',
        '구간3비율(%) 40-60 시간(초)': 'sum',
        '구간4비율(%) 60-80 시간(초)': 'sum',
        '공회전,웜업제외 시간': 'sum'
    }).reset_index()

    daily_grouped['연비'] = daily_grouped['주행거리(km)'] / daily_grouped['연료소모량(m3']

    def grade(row):
        ratio = row['연비'] / row['목표연비']
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
    daily_grouped['주행거리(km)'] = daily_grouped['주행거리(km)'].apply(lambda x: f"{int(x):,} km")
    daily_grouped['연비'] = daily_grouped['연비'].apply(lambda x: f"{x:.2f}")
    daily_grouped['경제속도구간(%)'] = daily_grouped['경제속도구간(%)'].apply(lambda x: f"{x:.0f}%" if pd.notnull(x) else '-')

    # 6출력
    st.markdown(
        daily_grouped[['주행일', '차량번호', '코스', '주행거리(km)', '연비', '등급', '경제속도구간(%)']].to_html(index=False, escape=False),
        unsafe_allow_html=True
    )



