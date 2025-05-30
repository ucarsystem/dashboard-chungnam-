import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import plotly.express as px
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
st.set_page_config(page_title="충남고속 연비 대시보드", layout="wide")
logo_path = "./logo.png"
st.markdown(f"""
    <div style='display: flex; align-items: center; gap: 10px;'>
        <img src="data:image/png;base64,{st.image(logo_path, output_format="png").data.decode()}" style='width:40px; height:40px;'>
        <h1 style='margin:0; font-size:32px;'>충남고속_나만의 연비 대시보드</h1>
    </div>
    <hr style='border:1px solid #ccc; margin-top:10px;'>
""", unsafe_allow_html=True)

# col1, col2 = st.columns([1, 8])
# with col1:
#     st.image("./logo.png", width=80)  # 로고 파일 경로 및 크기 설정

# with col2:
#     st.markdown("<h1 style='margin-bottom:0;'>충남고속_나만의 연비 대시보드</h1>", unsafe_allow_html=True)
st.markdown("---")  # 구분선

driver_id = st.text_input("운전자번호를 입력하세요", "")
조회버튼 = st.button("조회하기")

if 조회버튼 and driver_id:
    driver_id = int(driver_id)
    
    ### 1. 전체 지표 ###
    st.header("전체 주행 지표")
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
        <div style='display: flex; align-items: center;'>
            <img src='https://img.icons8.com/color/48/bus.png';'>
            <div>
                <div><strong>대표 차량:</strong> {rep_car}</div>
                <div><strong>노선:</strong> {rep_route}</div>
                <div><strong>주코스:</strong> {rep_course}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        driver_info = df_driver[df_driver['운전자ID'] == driver_id].copy()
        driver_info['공회전율(%)'] = round(((driver_info['공회전시간'] / driver_info['주행시간']) * 100),2)
        driver_info['급가속(회/100km)'] = round(((driver_info['급가속횟수'] * 100) / driver_info['주행거리(km)']),2)
        driver_info['급감속(회/100km)'] = round(((driver_info['급감속횟수'] * 100) / driver_info['주행거리(km)']),2)

        if not driver_info.empty:
            driver_info_df = driver_info.iloc[0]
            grade_color = get_grade_color(driver_info_df['등급'])

            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.markdown(f"<div style='font-size: 20px; font-weight: bold;'>{int(month_input)}월 등급</div><div style='font-size: 30px; font-weight: bold; color: {grade_color};'>{driver_info_df['등급']}</div>", unsafe_allow_html=True)
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
    st.header("코스별 나의 운행 데이터")
    course_filtered = df_course_driver[df_course_driver['운전자번호'] == driver_id].copy()
    course_filtered['저속구간(%)'] = course_filtered['구간1비율'] + course_filtered['구간2비율']
    course_filtered['경제구간(%)'] = course_filtered['구간3비율'] + course_filtered['구간4비율']
    course_filtered['과속구간(%)'] = course_filtered['구간5비율'] + course_filtered['구간6비율'] + course_filtered['구간7비율']
    course_filtered['공회전율(%)'] = (course_filtered['공회전시간(초)'] / course_filtered['주행시간(초)']) * 100

    course_filtered = course_filtered.sort_values(by='주행거리', ascending=False)
    st.dataframe(course_filtered[['코스', '주행거리', '연비', '공회전율(%)', '급감속', '평균속도', '저속구간(%)', '경제구간(%)', '과속구간(%)', '등수']])

    ### 3. 개인 vs 코스평균 비교 (연비) ###
    st.header("나의 연비 vs 코스 평균 연비")
    #코스별 평균연비
    course_mean_grade = df_course_driver.groupby('코스')['연비'].mean().reset_index().rename(columns={'연비': '평균연비'})

    # 개인 데이터와 병합 (코스 기준)
    course_filtered = course_filtered.merge(course_mean_grade, on='코스', how='left')

    fig = px.bar(course_filtered, x='코스', y=['연비', '평균연비'], barmode='group', labels={'value':'연비', 'variable':'코스'})
    st.plotly_chart(fig)

    ### 4. 일별 주행기록 ###
    st.header("일별 주행기록")
    daily_grouped = tang_filtered.groupby(['DATE', '차량번호4', '코스']).agg({
        '주행거리(km)': 'sum',
        '연료소모량(m3': 'sum',
        '구간3비율(%) 40-60 시간(초)': 'sum',
        '구간4비율(%) 60-80 시간(초)': 'sum',
        '공회전,웜업제외 시간': 'sum'
    }).reset_index()

    daily_grouped['연비'] = daily_grouped['주행거리(km)'] / daily_grouped['연료소모량(m3']
    def grade(x):
        ratio = x / 3.0
        if ratio >= 1.0: return 'S'
        elif ratio >= 0.95: return 'A'
        elif ratio >= 0.9: return 'B'
        elif ratio >= 0.85: return 'C'
        elif ratio >= 0.8: return 'D'
        else: return 'F'
    daily_grouped['등급'] = daily_grouped['연비'].apply(grade)
    daily_grouped['경제속도구간(%)'] = ((daily_grouped['구간3비율(%) 40-60 시간(초)'] + daily_grouped['구간4비율(%) 60-80 시간(초)']) / daily_grouped['공회전,웜업제외 시간']) * 100

    st.dataframe(daily_grouped[['DATE', '차량번호4', '코스', '주행거리(km)', '연비', '등급', '경제속도구간(%)']])

