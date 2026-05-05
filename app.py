import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# 🎨 ตั้งค่า Theme
st.set_page_config(page_title="Dashboard", layout="wide")

# 💅 CSS เพิ่มความสวย + animation
st.markdown("""
<style>
.main {
    background: linear-gradient(to right, #eef2f3, #ffffff);
}

h1 {
    color: #2c3e50;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
    transition: 0.3s;
}

.card:hover {
    transform: scale(1.03);
}

.kpi {
    font-size: 28px;
    font-weight: bold;
    color: #27ae60;
}
</style>
""", unsafe_allow_html=True)

# =========================
st.title("📊 Employee Dashboard")

uploaded_file = st.file_uploader("📥 อัปโหลด Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # 📅 แปลงวัน
    df['วันหมดอายุ'] = pd.to_datetime(df['วันหมดอายุ'], dayfirst=True, errors='coerce')
    df['วันหมดอายุ'] = df['วันหมดอายุ'].apply(
        lambda x: x.replace(year=x.year - 543) if pd.notnull(x) and x.year > 2400 else x
    )

    # 🧮 คำนวณ
    today = pd.Timestamp.today().normalize()
    df['เหลือ(วัน)'] = (df['วันหมดอายุ'] - today).dt.days

    # 🎯 สถานะ
    def status(x):
        if pd.isna(x):
            return "ไม่มีข้อมูล"
        elif x < 0:
            return "หมดอายุ"
        elif x <= 30:
            return "ใกล้หมด"
        else:
            return "ปกติ"

    df['สถานะ'] = df['เหลือ(วัน)'].apply(status)

    # =========================
    # 🔢 KPI แบบการ์ด
    col1, col2, col3 = st.columns(3)

    col1.markdown(f"""
    <div class="card">
        <div>📦 พนักงานทั้งหมด</div>
        <div class="kpi">{len(df)}</div>
    </div>
    """, unsafe_allow_html=True)

    col2.markdown(f"""
    <div class="card">
        <div>⚠️ ใกล้หมด</div>
        <div class="kpi">{(df['สถานะ']=="ใกล้หมด").sum()}</div>
    </div>
    """, unsafe_allow_html=True)

    col3.markdown(f"""
    <div class="card">
        <div>❌ หมดอายุ</div>
        <div class="kpi">{(df['สถานะ']=="หมดอายุ").sum()}</div>
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # 📊 กราฟ (มี animation)
    col4, col5 = st.columns(2)

    with col4:
        fig = px.pie(
            df,
            names='สถานะ',
            title='สัดส่วนพนักงาน',
            hole=0.4,
            color='สถานะ',
            color_discrete_map={
                'ปกติ': 'skyblue',
                'ใกล้หมด': 'orange',
                'หมดอายุ': 'red',
                'ไม่มีข้อมูล': 'gray'
            }
        )

        fig.update_traces(textinfo='percent+label')
        fig.update_layout(transition_duration=800)  # ✨ animation

        st.plotly_chart(fig, use_container_width=True)

    with col5:
        df['เดือน'] = df['วันหมดอายุ'].dt.to_period('M').astype(str)

        fig2 = px.bar(
            df,
            x='เดือน',
            color='สถานะ',
            title='แนวโน้มวันหมดอายุ'
        )

        fig2.update_layout(transition_duration=800)

        st.plotly_chart(fig2, use_container_width=True)

    # =========================
    # 📋 ตาราง
    st.subheader("📋 ตารางวันหมดอายุ")

    df_sorted = df.sort_values(by='วันหมดอายุ')

    st.dataframe(df_sorted, use_container_width=True)

else:
    st.info("👆 กรุณาอัปโหลด Excel")