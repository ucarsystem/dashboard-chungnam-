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

st.title("운전자 개인별 연비 컨설팅 대시보드")
driver_id = st.sidebar.text_input("운전자번호 입력", "")

if driver_id:
    driver_id = int(driver_id)
    
    ### 1. 전체 지표 ###
    st.header("1. 전체 지표")
    tang_filtered = df_tang[df_tang['운전자번호'] == driver_id]
    if not tang_filtered.empty:
        rep_car = tang_filtered.groupby('차량번호4')['주행거리(km)'].sum().idxmax()
        rep_course = tang_filtered.groupby('코스')['주행거리(km)'].sum().idxmax()
        rep_route = tang_filtered[tang_filtered['차량번호4'] == rep_car]['노선번호'].mode()[0]
        st.markdown(f"**대표차량:** {rep_car} | **대표노선:** {rep_route} | **대표코스:** {rep_course}")

        driver_info = df_driver[df_driver['운전자ID'] == driver_id].copy()
        driver_info['공회전율(%)'] = (driver_info['공회전시간'] / driver_info['주행시간']) * 100
        driver_info['급가속(회/100km)'] = (driver_info['급가속횟수'] * 100) / driver_info['주행거리(km)']
        driver_info['급감속(회/100km)'] = (driver_info['급감속횟수'] * 100) / driver_info['주행거리(km)']

        st.dataframe(driver_info[['주행거리(km)', '연비(km/m3)', '공회전율(%)', '급가속(회/100km)', '급감속(회/100km)', '평균속도', '등급', '달성율']])

    ### 2. 주행 코스별 운행기록 ###
    st.header("2. 주행 코스별 운행기록")
    course_filtered = df_course_driver[df_course_driver['운전자번호'] == driver_id].copy()
    course_filtered['저속구간(%)'] = course_filtered['구간1비율'] + course_filtered['구간2비율']
    course_filtered['경제구간(%)'] = course_filtered['구간3비율'] + course_filtered['구간4비율']
    course_filtered['과속구간(%)'] = course_filtered['구간5비율'] + course_filtered['구간6비율'] + course_filtered['구간7비율']
    course_filtered['공회전율(%)'] = (course_filtered['공회전시간(초)'] / course_filtered['주행시간(초)']) * 100

    course_filtered = course_filtered.sort_values(by='주행거리', ascending=False)
    st.dataframe(course_filtered[['코스', '주행거리', '연비', '공회전율(%)', '급감속', '평균속도', '저속구간(%)', '경제구간(%)', '과속구간(%)', '등수']])

    ### 3. 개인 vs 코스평균 비교 (연비) ###
    st.header("3. 개인 vs 코스평균 비교 (연비)")
    #코스별 평균연비
    course_mean_grade = df_course_driver.groupby('코스')['연비'].mean().reset_index().rename(columns={'연비': '평균연비'})

    # 개인 데이터와 병합 (코스 기준)
    course_filtered = course_filtered.merge(course_mean_grade, on='코스', how='left')

    fig = px.bar(course_filtered, x='코스', y=['연비', '평균연비'], barmode='group', labels={'value':'연비', 'variable':'코스'})
    st.plotly_chart(fig)

    ### 4. 일별 주행기록 ###
    st.header("4. 일별 주행기록")
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

