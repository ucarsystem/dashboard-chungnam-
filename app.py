import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
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

# 기본 경로 설정
file_dir = "./file"
company_file = os.path.join(file_dir, "company_info.xlsx")
id_check_file = os.path.join(file_dir, "인천ID.xlsx")
file_url_template = "https://github.com/ucarsystem/driver_dashboard/file/인천%20개인별%20대시보드_{year}년{month}월.xlsx"

# 엑셀 파일 로드 함수
def load_excel(path, sheetname):
    try:
        return pd.read_excel(path, sheet_name=sheetname)
    except Exception as e:
        st.error(f"엑셀 파일 로드 오류: {e}")
        return None
    
# 📂 운수사 목록 불러오기
df_company = pd.read_excel(company_file, sheet_name="Sheet1", header=None) if os.path.exists(company_file) else pd.DataFrame()
company_list = df_company[0].dropna().tolist() if not df_company.empty else []
df_code = pd.read_excel(company_file, sheet_name="code") if os.path.exists(company_file) else pd.DataFrame()

#24년 인증제
medal_filepath = os.path.join(file_dir, "인증제.xlsx")
cert_24_all = load_excel(medal_filepath, "24년 명단")
cert_25_all = load_excel(medal_filepath, "25년 명단")


# Streamlit UI 구성🚍
st.title("🚍 운전자별 대시보드")
company_input = st.selectbox("운수사를 입력하세요", options=company_list, index=company_list.index(st.session_state.get("company_input", company_list[0])) if "company_input" in st.session_state else None)

user_id_input = st.text_input("운전자 ID를 입력하세요", value=st.session_state.get("user_id_input", ""))
# st.markdown("""
#     <a href='https://driverid-xgkps9rbvh4iph8yrcvovb.streamlit.app/' target='_blank' 
#     style='display: inline-block; padding: 10px 20px; background-color: green; color: white; font-weight: bold; 
#     text-align: center; text-decoration: none; border-radius: 5px;'>내 ID를 모른다면? >> ID 조회하기</a>
# """, unsafe_allow_html=True)
user_name_input = st.text_input("운전자 이름을 입력하세요", value=st.session_state.get("user_name_input", ""))

# ID목록 체크
if st.button("1️⃣ 운전자 정보 확인"):
    if company_input and user_id_input and user_name_input:
        df_id_list = load_excel(id_check_file, "ID목록") if os.path.exists(id_check_file) else pd.DataFrame()

        valid_user = df_id_list[
            (df_id_list['운수사'] == company_input) &
            (df_id_list['운전자ID'].astype(str) == user_id_input) &
            (df_id_list['운전자이름'] == user_name_input)
        ]

        if not valid_user.empty:
            st.success("✅ 해당 운전자의 정보를 조회하겠습니다.")

            with st.form("select_month_form"):
                year_input = st.selectbox("년도를 입력하세요", [25])
                month_input = st.selectbox("월을 입력하세요", ["01", "02", "03", "04"]).zfill(2)
                submitted = st.form_submit_button("2️⃣ 조회 실행하기")

            if submitted:
                input_yyyymm = f"{year_input}{month_input}"
                file_name = f"인천 개인별 대시보드_{year_input}년{month_input}월.xlsx"
                file_path = os.path.join(file_dir, file_name)
                st.session_state.update({
                    'company_input': company_input,
                    'user_id_input': user_id_input,
                    'user_name_input': user_name_input,
                    'input_yyyymm': input_yyyymm,
                    'file_path': file_path,
                    'year_input': year_input,
                    'month_input': month_input
                })
                st.experimental_rerun()
    
# Step 2: 파일 로드 후 조회
if "file_path" in st.session_state:
    company_input = st.session_state["company_input"]
    user_id_input = st.session_state["user_id_input"]
    user_name_input = st.session_state["user_name_input"]
    input_yyyymm = st.session_state["input_yyyymm"]
    file_path = st.session_state["file_path"]

    if os.path.exists(file_path):
        df = load_excel(file_path, "매크로(운전자리스트)")
        df_vehicle = load_excel(file_path, "차량+운전자별")
        df_monthly = load_excel(file_path, "운전자별")
        df_daily = load_excel(file_path, "일별)차량+운전자")
        # df_cert_24 = load_excel(file_path, "24년 명단")
        # df_cert_25 = load_excel(file_path, "25년 후보자")

        # 조건 필터링
        filtered = df[
            (df["운수사"] == company_input) &
            (df["운전자이름"] == user_name_input) &
            (df["운전자ID"].astype(str) == user_id_input)
        ]

        #등급함수
        def calc_grade(score):
            score *= 100
            if score >= 100: return "S"
            elif score >= 95: return "A"
            elif score >= 90: return "B"
            elif score >= 85: return "C"
            elif score >= 80: return "D"
            elif score >= 65: return "F"
            else: return ""

        if not filtered.empty:
            row = filtered.iloc[0]
            st.success(f"✅ 운전자 {user_name_input} (ID: {user_id_input}) 정보 조회 성공")

            st.markdown("---")

            #값 정의
            #이번달
            this_grade = row[f"{input_yyyymm}"] #등급
            this_percent = row['이번달달성율']
            this_warm = row['이번달웜업비율(%)']
            this_idle = row["이번달공회전비율(%)"] 
            this_break = row['이번달급감속(회)/100km']
            this_line = row['주운행노선']
            this_bus = row['주운행차량']

            #전월
            last_grade = row['전월등급']
            last_percent = row['전월달성율']
            last_warm = row['전월웜업비율(%)']
            last_idle = row["전월공회전비율(%)"] 
            last_break = row['전월급감속(회)/100km']

            #노선평균
            ave_grade = row['노선평균등급']
            ave_percent = row['노선평균달성율']
            ave_warm = row['노선평균웜업비율(%)']
            ave_idle = row["노선평균공회전비율(%)"] 
            ave_break = row['노선평균급감속(회)/100km']

            #다음달
            next_month = 1 if int(month_input) == 12 else int(month_input)+1 


            grade_color = {"S": "🟩", "A": "🟩", "B": "🟨", "C": "🟨", "D": "🟥", "F": "🟥"}
            grade_target = "C" if this_grade in ["F", "D"] else "B" if this_grade == "C" else "A" if this_grade == "B" else "S"
            grade_text_color = "green" if this_grade in ["S", "A"] else "orange" if this_grade in ["B", "C"] else "red"

            # 🚌 이번달 핵심 성과 요약
            summary_msg = ""
            if this_grade in ["S", "A"]:
                summary_msg = f"🎉 {int(month_input)}월 <b>{this_grade}</b>등급 달성! 안정적인 운전 감사합니다."
            elif this_break > 20:
                summary_msg = f"⚠️ {int(month_input)}월 급감속 <b>{this_break:.1f}</b>회! 탕별 급감속 1회 목표로 <b>{grade_target}등급</b>까지 도전해보세요!"
            elif this_idle > ave_idle:
                summary_msg = f"⚠️ 공회전율이 다소 높습니다. 시동 관리를 통해 <b>{grade_target}등급</b> 도전해보세요!"
            else:
                summary_msg = f"📌 {int(month_input)}월 <b>{this_grade}</b>등급! 조금만 더 노력하면 <b>{grade_target}</b>도 가능합니다."

            st.markdown(f"""
            <div style='
                background-color: #f9f9f9; 
                padding: 12px; 
                margin-bottom: 20px; 
                border-left: 6px solid #FFA500; 
                font-size: 18px;
                font-weight: bold;
            '>
            {summary_msg}
            </div>
            """, unsafe_allow_html=True)

            # ✅ 2. 기존 요약 (대표 차량, 노선, 등급, 주요 지표)
            st.markdown(f"""
            <div style='display: flex; align-items: center;'>
                <img src='https://img.icons8.com/color/48/bus.png' style='margin-right: 10px;'>
                <div>
                    <div><strong>대표 차량:</strong> {this_bus}</div>
                    <div><strong>노선:</strong> {this_line}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns(4)
            col1.markdown(f"<div style='font-size: 80px; font-weight: bold; color: {grade_text_color}; text-shadow: 2px 2px 3px rgba(0,0,0,0.2); margin-top: 10px;'>{this_grade}</div><div style='text-align: center; font-size: 20px; font-weight: bold;'>{int(month_input)}월 등급</div>", unsafe_allow_html=True)
            col2.metric("달성률", f"{round(row['이번달달성율'] * 100)}%")
            col3.metric("공회전", f"{round(this_idle * 100)}%")
            col4.metric("급감속", f"{round(this_break, 2)}")

            # 순위표시

            # [운전자별] 시트에서 순위 계산
            df_incheon = df_monthly[(df_monthly['년월'] == int(input_yyyymm))&
                                (df_monthly['운전자이름'].notnull())
            ].copy()

            # 인천 전체 순위
            df_incheon = df_incheon.sort_values(by="가중달성율", ascending=False).reset_index(drop=True)
            incheon_rank = df_incheon[(df_incheon['운전자ID'].astype(str) == user_id_input) & (df_incheon['운수사'] == company_input)].index[0] + 1
            incheon_total = len(df_incheon)
            incheon_percent = incheon_rank / incheon_total * 100

            df_company_driver = df_monthly[
                (df_monthly['년월'] == int(input_yyyymm)) &
                (df_monthly['운수사'] == company_input) &
                (df_monthly['운전자이름'].notnull())
            ].sort_values(by="가중달성율", ascending=False).reset_index(drop=True)
            # 운수사 내부 순위
            company_driver_match = df_company_driver[df_company_driver['운전자ID'].astype(str) == user_id_input]
            if not company_driver_match.empty:
                company_rank = company_driver_match.index[0] + 1
                company_total = len(df_company_driver)
                company_percent = company_rank / company_total * 100
            else:
                company_rank = "-"
                company_total = len(df_company_driver)
                company_percent = 0.0  # 또는 표시하지 않도록 설정

            # 표시(순위)
            st.markdown(f"""
            <div style='background-color: #f9f9f9; padding: 15px; border-radius: 8px; line-height: 1.8;'>

            <p style='font-size: 18px; margin: 5px 0;'>
                <strong>🚩 인천시 전체 순위</strong>: 
                <span style='font-size: 20px; font-weight: bold; color: orange;'>{incheon_rank}등</span> / 총 {incheon_total}명 → 
                <span style='font-size: 20px; font-weight: bold; color: orange;'>상위 {incheon_percent:.1f}%</span>
            </p>

            <p style='font-size: 18px; margin: 5px 0;'>
                <strong>🧑‍💼 {company_input} 내 순위</strong>: 
                <span style='font-size: 20px; font-weight: bold; color: orange;'>{company_rank}등</span> / 총 {company_total}명 → 
                <span style='font-size: 20px; font-weight: bold; color: orange;'>상위 {company_percent:.1f}%</span>
            </p>

            </div>
            """, unsafe_allow_html=True)

            # 2. 인증 현황🏅
            st.markdown("---")
            st.subheader("🏆나의 인증 현황")


            st.markdown(f"<div style='background-color: rgba(211, 211, 211, 0.3); padding: 10px; border-radius: 5px; margin-bottom: 20px;'> 4분기 모두 우수인증자 수여 시 그랜드슬림 달성!", unsafe_allow_html=True)

            from calendar import month_abbr
            df_cert_25_summary = df_monthly[
                (df_monthly['운수사'] == company_input) &
                (df_monthly['운전자ID'].astype(str) == user_id_input) &
                (df_monthly['운전자이름'] == user_name_input)&
                (df_monthly['년월'].astype(str).str.startswith("25"))
            ]

            medal_url = "https://raw.githubusercontent.com/ucarsystem/driver_dashboard/main/medal.png"
            medal_black_url = "https://raw.githubusercontent.com/ucarsystem/driver_dashboard/main/medal_black.png"

            # 분기/월 전처리
            df_cert_25_summary['년'] = df_cert_25_summary['년월'].astype(str).str[:2].astype(int)
            df_cert_25_summary['월'] = df_cert_25_summary['년월'].astype(str).str[2:].astype(int)
            df_cert_25_summary['분기'] = df_cert_25_summary['월'].apply(lambda m: (m - 1) // 3 + 1)

            # 분기별 평균: 각 분기에 해당하는 월의 평균
            quarter_avg = (
                df_cert_25_summary
                .groupby(['년', '분기'])
                .agg({'가중달성율': 'mean'})
                .reset_index()
            )

            quarter_avg['등급'] = quarter_avg['가중달성율'].apply(calc_grade)

            grouped_month = df_cert_25_summary[['년', '월', '등급']].copy()
            grouped_month = grouped_month.rename(columns={'등급': '월별등급'})

            # ✅ 24년 인증자 진행바 표시
            cert_24_total = int(cert_24_all['전체명수'].sum())
            cert_24_win = int(cert_24_all['시상명수'].sum())
            cert_24_percent = round(cert_24_win / cert_24_total * 100, 1) if cert_24_total > 0 else 0

            st.markdown("**24년 인증자**")
            st.progress(cert_24_percent / 100)
            st.markdown(f"상위 {cert_24_percent}% (총 {cert_24_total}명 중 {cert_24_win}명 인증서 수여)")

            is_cert_24_bar = not cert_24_all[
                (cert_24_all['운수사'] == company_input) &
                (cert_24_all['성명'] == user_name_input) &
                (cert_24_all['아이디'].astype(str) == user_id_input)
            ].empty

            if is_cert_24_bar:
                st.success(f"24년 상위 {cert_24_percent}% 우수운전자이십니다! 🏅")

            # ✅ 25년 진행바 (25년 명단 시트 기반) - 실제 열 존재 여부 기준으로 진행바 표시
            progress_columns = [col for col in cert_25_all.columns if "분기 등급" in str(col)]

            for col_name in progress_columns:
                bar_quarter = col_name.split("분기")[0]
                st.markdown(f"**25년 인증 현황 - {bar_quarter}분기**")

                cert_25_q = cert_25_all[cert_25_all[col_name].notnull()]
                bar_total = len(cert_25_q)
                bar_win = len(cert_25_q[cert_25_q[col_name].isin(['A', 'S'])])
                bar_percent = round(bar_win / bar_total * 100, 1) if bar_total > 0 else 0

                st.progress(bar_percent / 100)
                st.markdown(f"상위 {bar_percent}% (총 {bar_total}명 중 {bar_win}명 인증서 수여)")

                is_certified = not cert_25_q[
                    (cert_25_q['운수사'] == company_input) &
                    (cert_25_q['운전자ID'].astype(str) == user_id_input) &
                    (cert_25_q['운전자이름'] == user_name_input) &
                    (cert_25_q[col_name].isin(['A', 'S']))
                ].empty

                if is_certified:
                    st.success(f"{bar_quarter}분기 상위 {bar_percent}% 우수운전자이십니다! 🎖")

            # 매달 표시 (24년 인증, 25년 분기별)
            # 24년 인증 확인
            is_cert_24 = not cert_24_all[
                (cert_24_all['운수사'] == company_input) &
                (cert_24_all['성명'] == user_name_input) &
                (cert_24_all['아이디'].astype(str) == user_id_input)
            ].empty

            if is_cert_24:
                medal_24 = (
                    "<div style='width: 180px; height: 180px; text-align: center; border: 2px solid #888; border-radius: 10px; padding: 10px; margin-bottom: 30px;'>"
                    "<div style='font-size: 15px; font-weight: bold;'>24년 전체</div>"
                    f"<img src='{medal_url}' width='100'>"
                    f"<div style='font-weight:bold; font-size: 15px; background: linear-gradient(to right, #FFD700, #FFA500); -webkit-background-clip: text; -webkit-text-fill-color: transparent;display: inline-block;'>🏅 우수운전자 🏅</div>"
                    "</div>"
                )
            else:
                medal_24 = (
                    "<div style='width: 180px; height: 180px; text-align: center; border: 2px solid #888; border-radius: 10px; padding: 10px; margin-bottom: 30px;'>"
                    "<div style='font-size: 15px; font-weight: bold;'>24년 전체</div>"
                    f"<img src='{medal_black_url}' width='100'>"
                    f"<div style='font-weight:bold; font-size: 13px; display: inline-block;'>다음 기회를 도전해보세요!</div>"
                    "</div>"

                )
            st.markdown(medal_24, unsafe_allow_html=True)

            cert_grid = "<div style='display: flex; flex-wrap: wrap; gap: 20px; align-items: flex-start;'>"

            # 25년 인증현황
            # 현재 날짜 기준으로 현재 연도/월 확인
            now = datetime.datetime.now()
            current_year = int(str(now.year)[-2:])  # 25
            current_month = now.month
            current_quarter = (current_month - 1) // 3 + 1

            for q_idx, q_row in quarter_avg.iterrows():
                year, quarter, avg_score, grade = q_row['년'], int(q_row['분기']), q_row['가중달성율'], q_row['등급']
                quarter_title = f"{year}년 {quarter}분기"

                months_in_quarter = grouped_month[
                    (grouped_month['년'] == year) & 
                    (grouped_month['월'].between((quarter - 1) * 3 + 1, quarter * 3))
                ]

                if year < current_year or (year == current_year and quarter < current_quarter):
                    if avg_score >= 0.95:
                        medal = (
                            f"<img src='{medal_url}' width='100'>"
                            f"<div style='font-weight:bold; font-size: 15px; background: linear-gradient(to right, #FFD700, #FFA500); -webkit-background-clip: text; -webkit-text-fill-color: transparent;display: inline-block;'>✨ 우수운전자 ✨</div>"
                        )
                    else:
                        medal = (
                            f"<img src='{medal_black_url}' width='100'>"
                            f"<div style='font-weight:bold;'>{grade}({avg_score*100:.0f}%)</div>"
                        )
                else:
                    medal = (
                        f"<img src='{medal_black_url}' width='100'>"
                        f"<div style='font-size: 13px;'>진행중...({avg_score*100:.0f}%)</div>"
                    )

                # 월별 박스를 가로 배치하기 위한 container 추가
                month_boxes = "".join([
                    "<div style='margin: 15px; text-align: center; display: inline-block;'>"
                    f"<div style='font-size: 16px; font-weight: bold;'>{m_row['월']}월</div>"
                    f"<div style='font-size: 24px;'>{'🥇' if m_row['월별등급'] in ['S', 'A'] else m_row['월별등급']}</div>"
                    "</div>"
                    for _, m_row in months_in_quarter.iterrows()
                ])

                cert_grid += (
                    "<div style='width: 200px; text-align: center; border: 1px solid #ccc; border-radius: 10px; padding: 10px;'>"
                    f"<div style='font-size: 15px; font-weight: bold;'>{quarter_title}</div>"
                    f"{medal}"
                    f"<div style='margin-top: 15px; display: flex; justify-content: center;'>{month_boxes}</div>"
                    "</div>"
                )

            cert_grid += "</div>"
            st.markdown(cert_grid, unsafe_allow_html=True)

            # 3. 📅 일별 달성률 및 등급 표시
            st.markdown("---")
            st.subheader("📅 일별 등급 스탬프")
            df_daily_filtered = df_daily[
                (df_daily['운수사'] == company_input) &
                (df_daily['운전자ID'].astype(str) == user_id_input) &
                (df_daily['운전자이름'] == user_name_input)
            ]
            if not df_daily_filtered.empty:
                grouped = df_daily_filtered.groupby('DATE')['가중평균달성율'].sum().reset_index()

                grouped['달성률값'] = (grouped['가중평균달성율'] * 100).round(0)
                grouped['등급'] = grouped['가중평균달성율'].apply(calc_grade)
                grouped['날짜'] = pd.to_datetime(grouped['DATE'])


                # 📅 달력형 등급 표시
                import calendar
                year = grouped['날짜'].dt.year.iloc[0]
                month = grouped['날짜'].dt.month.iloc[0]
                grade_map = grouped.set_index(grouped['날짜'].dt.day)['등급'].to_dict()
                cal = calendar.Calendar()
                month_days = cal.monthdayscalendar(year, month)

                calendar_rows = []
                for week in month_days:
                    low = []
                    for i, day in enumerate(week):
                        if day == 0:
                            low.append("<td style='height: 80px;'></td>")
                        else:
                            grade = grade_map.get(day, "")
                            if grade in ["S", "A"]:
                                emoji = "<div style='font-size: 30px;'>🎖️</div>"
                                label = ""
                            elif grade in ["B", "C"]:
                                emoji = f"<div style='color: orange; font-size: 30px; font-weight: bold;'>{grade}</div>"
                            elif grade in ["D", "F"]:
                                emoji = f"<div style='color: red; font-size: 30px; font-weight: bold;'>{grade}</div>"
                            else:
                                emoji = f"<span style='font-weight: bold; font-size: 20px;'>"  "</span>"
                            color = "red" if i == 0 else "black"
                            low.append(f"""
                                <td style='padding: 8px; border: 1px solid #ccc; color: {color}; height: 80px;'>
                                    <div style='font-size: 16px; font-weight: bold;'>{day}</div>
                                    {emoji}
                                </td>""")
                    calendar_rows.append("<tr>" + "".join(low) + "</tr>")

                html = """
                <table style='border-collapse: collapse; margin: auto; background-color: #fff;'>
                <tr style='background-color: #f2f2f2;'>
                    <th style='color: red; width: 80px;'>일</th><th style='width: 80px;'>월</th><th style='width: 80px;'>화</th><th style='width: 80px;'>수</th><th style='width: 80px;'>목</th><th style='width: 80px;'>금</th><th style='width: 80px;'>토</th>
                </tr>
                """ + "".join(calendar_rows) + "</table>"
                # <table style='border-collapse: collapse; width: 100%; text-align: center; background-color: #f0f5ef;'>
                # <tr style='background-color: #e0e0e0;'>
                #     <th style='color: red;'>일</th><th>월</th><th>화</th><th>수</th><th>목</th><th>금</th><th>토</th>
                # </tr>
                # """ + "".join(calendar_rows) + "</table>"

                st.markdown(html, unsafe_allow_html=True)


            # 4. 운전습관 지표 비교
            st.markdown("---")
            st.subheader("🚦 운전 습관 핵심 지표 비교 🚦")
            compare_df = pd.DataFrame({
                "지표": ["달성률(%)", "웜업률(%)", "공회전률(%)", "급감속(회/100km)"],
                "이달": [
                    f"{round(this_percent * 100)}%",
                    f"{round(this_warm * 100, 1)}%",
                    f"{round(this_idle * 100, 1)}%",
                    f"{round(this_break, 2)}"
                ],
                "전월": [
                    f"{round(last_percent * 100)}%",
                    f"{round(last_warm * 100, 1)}%",
                    f"{round(last_idle * 100, 1)}%",
                    f"{round(last_break, 2)}"
                ],  # 예시값
                "노선 평균": [
                    f"{round(ave_percent * 100)}%",
                    f"{round(ave_warm * 100, 1)}%",
                    f"{round(ave_idle * 100, 1)}%",
                    f"{round(ave_break, 2)}"
                ],  # 예시값
            })

            st.write("""
            <style>
            td span {
                font-size: 13px;
            }
            table td {
                white-space: nowrap !important;
                text-align: center;
                vertical-align: middle;
            }
            </style>
            """, unsafe_allow_html=True)
            st.write(compare_df.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            st.markdown("---")
            st.subheader("📊 이달 vs 노선 평균 그래프")
            labels = [
                "웜업률(%)", "공회전률(%)", "탄력운전률(%)",
                "연료소모율", "급가속(/100km)", "급감속(/100km)"
            ]
            driver_vals = [
                this_warm * 100,
                this_idle * 100,
                row["이번달탄력운전비율(%)"] * 100,
                row["이번달평균연료소모율"],
                row["이번달급가속(회)/100km"],
                this_break
            ]
            avg_vals = [
                ave_warm * 100,
                ave_idle * 100,
                row["노선평균탄력운전비율(%)"] * 100,
                row["노선평균평균연료소모율"],
                row["노선평균급가속(회)/100km"],
                ave_break
            ]

            # 조건에 따른 색상 정의
            def get_color(i, d, a):
                good_if_higher = (i == 2)  # 탄력운전률만 높을수록 좋음
                if (good_if_higher and d >= a) or (not good_if_higher and d <= a):
                    return '#C8E6C9'  # 연한 녹색
                else:
                    return '#2E7D32'  # 진한 녹색 (기준보다 나쁠 때)

            colors = [get_color(i, d, a) for i, (d, a) in enumerate(zip(driver_vals, avg_vals))]

            fig, ax = plt.subplots(figsize=(9, 5))
            x = range(len(labels))
            bar_width = 0.4

            bars1 = ax.barh(x, driver_vals, height=bar_width, label='운전자', align='center', color=colors)
            bars2 = ax.barh([i + bar_width for i in x], avg_vals, height=bar_width, label='노선 평균', align='center', color='#FFE08C')

            # 값 표시
            for i, (d, a) in enumerate(zip(driver_vals, avg_vals)):
                ax.text(d + 0.8, i, f"{d:.1f}", va='center', fontsize=10, fontweight='bold', color='black')
                ax.text(a + 0.8, i + bar_width, f"{a:.1f}", va='center', fontsize=10, fontweight='bold', color='black')

            # 라벨 및 제목 스타일 조정
            ax.set_yticks([i + bar_width / 2 for i in x])
            ax.set_yticklabels(labels, fontproperties=font_prop, fontsize=11)
            ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
            ax.invert_yaxis()
            ax.legend(prop=font_prop)
            ax.set_title("이달 수치 vs 노선 평균 비교", fontsize=15, fontweight='bold', fontproperties=font_prop)
            ax.set_axisbelow(True)
            ax.grid(True, axis='x', linestyle='--', alpha=0.4)

            st.pyplot(fig)

            # 5. 전월대비 변화
            st.markdown("---")
            st.subheader("📈 전월 대비 개선 여부")
            def get_prev_yyyymm(yyyymm):
                y, m = int(yyyymm[:2]), int(yyyymm[2:])
                if m == 1:
                    return f"{y - 1 if y > 0 else 99}12"
                else:
                    return f"{y:02d}{m - 1:02d}"
                
            prev_yyyymm = get_prev_yyyymm(input_yyyymm)
            df_prev = df_monthly[
                (df_monthly['운수사'] == company_input) &
                (df_monthly['운전자ID'].astype(str) == user_id_input) &
                (df_monthly['운전자이름'] == user_name_input)
            ]

            prev_row = df_prev[df_prev['년월'] == int(prev_yyyymm)]
            curr_row = df_prev[df_prev['년월'] == int(input_yyyymm)]

            if not prev_row.empty and not curr_row.empty:
                prev = prev_row.iloc[0]
                curr = curr_row.iloc[0]
                compare = pd.DataFrame({
                    "지표": ["달성률(%)", "웜업률(%)", "공회전률(%)", "탄력운전비율(%)", "급감속"],
                    "전월": [
                        round(last_percent * 100, 0),
                        round(last_warm* 100, 2),
                        round(last_idle * 100, 2),
                        round(row['전월탄력운전비율(%)'] * 100, 2),
                        round(last_break, 2)
                    ],
                    "이달": [
                        round(this_percent* 100, 0),
                        round(this_warm * 100, 2),
                        round(this_idle* 100, 2),
                        round(row['이번달탄력운전비율(%)'] * 100, 2),
                        round(this_break, 2)
                    ]
                })

                #변화 계산 및 방향 아이콘 추가
                def trend_icon(idx, diff):
                    if idx in [0, 3]:  # 달성률, 탄력운전률: 높을수록 좋음
                        if diff > 0:
                            return f"<span style='color: green;'>🟢 +{diff:.2f} 개선</span>"
                        elif diff < 0:
                            return f"<span style='color: red;'>🔴 -{abs(diff):.2f} 악화</span>"
                    else: #웜업률, 공회전률, 급감속: 낮을수록 좋음
                        if diff < 0:
                            return f"<span style='color: green;'>🟢 +{abs(diff):.2f} 개선</span>"
                        elif diff > 0:
                            return f"<span style='color: red;'>🔴 -{diff:.2f} 악화</span>"
                    return "-"

                compare['변화'] = [trend_icon(i, compare['이달'][i] - compare['전월'][i]) for i in range(len(compare))]
                st.write("""
                <style>
                td span {
                    font-size: 13px;
                }
                table td {
                    white-space: nowrap !important;
                    text-align: center;
                    vertical-align: middle;
                }
                </style>
                """, unsafe_allow_html=True)
                st.write(compare.to_html(escape=False, index=False), unsafe_allow_html=True)

            st.markdown("---")

            # 6.차량별요약      
            st.subheader("🚘 차량별 요약")
            df_vehicle_filtered = df_vehicle[
                (df_vehicle['운수사'] == company_input) &
                (df_vehicle['운전자ID'].astype(str) == user_id_input) &
                (df_vehicle['운전자이름'] == user_name_input) &
                (df_vehicle['년월'] == int(input_yyyymm))
            ].sort_values(by="주행거리(km)", ascending=False).head(5)

            if not df_vehicle_filtered.empty:
                df_vehicle_display = df_vehicle_filtered.copy()
                df_vehicle_display["주행거리(km)"] = df_vehicle_display["주행거리(km)"].apply(lambda x: f"{int(x):,} km")
                df_vehicle_display["웜업비율(%)"] = df_vehicle_display["웜업비율(%)"].apply(lambda x: f"{x * 100:.2f}%")
                df_vehicle_display["공회전비율(%)"] = df_vehicle_display["공회전비율(%)"].apply(lambda x: f"{x * 100:.2f}%")
                df_vehicle_display["급감속(회)/100km"] = df_vehicle_display["급감속(회)/100km"].apply(lambda x: f"{x:.2f}")
                df_vehicle_display["연비(km/m3)"] = df_vehicle_display["연비(km/m3)"].apply(lambda x: f"{x:.2f}")

                def format_grade(g):
                    color = "green" if g in ["S", "A"] else "orange" if g in ["B", "C"] else "red"
                    return f"<span style='color:{color}; font-weight:bold'>{g}</span>"

                df_vehicle_display["등급"] = df_vehicle_display["등급"].apply(format_grade)

                df_vehicle_display = df_vehicle_display[["노선번호", "차량번호4", "주행거리(km)", "웜업비율(%)", "공회전비율(%)", "급감속(회)/100km", "연비(km/m3)", "등급"]]

                df_vehicle_display = df_vehicle_display.rename(columns={
                    "노선번호" : "노선",
                    "차량번호4": "차량번호",
                    "주행거리(km)" : "주행거리",
                    "웜업비율(%)" : "웜업률(%)", 
                    "공회전비율(%)" : "공회전율(%)",
                    "연비(km/m3)": "연비"
                })

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

                st.write(df_vehicle_display.to_html(escape=False, index=False), unsafe_allow_html=True)

            st.markdown("---")

            # 7. 개인 맞춤 피드백
            st.subheader("🗣️ 개인 맞춤 피드백")

            #급감속 멘트
            break_text = f"""
            <br>
            <p style='font-size: 22px; font-style: italic;'>
            <b>{next_month}</b>월에는, <b>급감속</b>을 줄여봅시다.<br>
            이번달 급감속 <b>{round(this_break, 2)}</b> 급감속은 <b>매탕 1회 미만!</b><br>
            이것만 개선해도 연비 5% 개선, 
            <span style='color: green; font-weight: bold;'>{grade_target}등급</span>까지 도달 목표!!
            </p>"""

            #공회전멘트
            idle_text = f"""
            <br>
            <p style='font-size: 22px; font-style: italic;'>
            <b>{next_month}</b>월에는, <b>공회전</b>을 줄여봅시다.<br>
            이번달 공회전 <b>{round(this_idle * 100)}%</b> 공회전은 <b>5분 미만!</b><br>
            이것만 개선해도 연비 5% 개선, 
            <span style='color: green; font-weight: bold;'>{grade_target}등급</span>까지 도달 목표!!
            </p>"""

            #급감속이 20보다 작으면 공회전관리멘트 보여주기
            additional_text = idle_text if this_break <20 else  break_text

            st.markdown(f"""
            <div style='background-color: rgba(211, 211, 211, 0.3); padding: 10px; border-radius: 5px;'>
            {additional_text}
            </div>
            """, unsafe_allow_html=True)

            # 조건별 자동 피드백 생성
            # st.markdown("### 📌 사고위험/공회전 분석 피드백")
            break_ = row["이번달급가속(회)/100km"]
            idle = row["이번달공회전비율(%)"] * 100

            feedback_parts = []
            if break_ < row["노선평균급감속(회)/100km"]:
                feedback_parts.append("✅ 사고위험 발생이 매우 적어 안전 운전에 기여하고 있습니다.")
            elif break_ < 80:
                feedback_parts.append("🟡 사고위험이 다소 발생하고 있습니다. ")
            else:
                feedback_parts.append("⚠️ 사고위험 지수가 높습니다. 매탕 급감속 횟수 1회씩만 줄여보세요.")

            if idle > row["노선평균공회전비율(%)"]*100:
                feedback_parts.append("⚠️ 공회전 비율이 높습니다. 정차 시 시동 관리에 유의해 주세요.")
            elif idle > 40:
                feedback_parts.append("🟡 공회전이 평균보다 다소 높습니다. 불필요한 정차를 줄여주세요.")
            else:
                feedback_parts.append("✅ 공회전 관리가 잘 되고 있습니다.")

            st.markdown("<br>".join(feedback_parts), unsafe_allow_html=True)
        else:
            st.warning("해당 운전자의 정보가 없습니다. 관리자에 문의해주세요.")
    else:
        st.warning("운수사, 운전자 ID, 운전자 이름을 확인해주세요.")
else:
    st.warning("운수사, 운전자 ID, 운전자 이름을 입력하세요.")


