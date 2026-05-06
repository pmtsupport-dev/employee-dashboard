import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
st.set_page_config(page_title="Dashboard", layout="wide")

# 🧠 state
if "filter_status" not in st.session_state:
    st.session_state.filter_status = "ทั้งหมด"

if "popup_shown" not in st.session_state:
    st.session_state.popup_shown = False

# =========================
# 🔗 🔥 ใส่ลิงก์ Google Sheets ของคุณตรงนี้
sheet_url = "https://docs.google.com/spreadsheets/d/1JbU_0hNzrYNAGvoEnN0etL9DkJ0vnhbtM6KNHBYtUgY/edit?usp=sharing"

# =========================
# 🎨 CSS
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
    position: relative;
}

.card:hover {
    transform: scale(1.03);
}

.kpi {
    font-size: 28px;
    font-weight: bold;
    color: #27ae60;
}

.card button {
    position: absolute;
    width: 100%;
    height: 100%;
    opacity: 0;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)

# =========================
st.title("📊 Employee Dashboard")

# 🎯 เลือกโหมด
mode = st.radio("เลือกการใช้งาน", ["📱 มือถือ (ออนไลน์)", "💻 คอม (อัปโหลดไฟล์)"])

# =========================
# 📥 โหลดข้อมูล
if mode == "📱 มือถือ (ออนไลน์)":
    df = pd.read_csv(sheet_url)

else:
    uploaded_file = st.file_uploader("📥 อัปโหลด Excel", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
    else:
        st.stop()

# =========================
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
# 🚨 ALERT + POPUP
near_count = (df['สถานะ'] == "ใกล้หมด").sum()
expired_count = (df['สถานะ'] == "หมดอายุ").sum()

if expired_count > 0:
    st.error(f"🚨 มีเบอร์หมดอายุ {expired_count} รายการ!")

if near_count > 0:
    st.warning(f"⚠️ มีเบอร์ใกล้หมด {near_count} รายการ!")

@st.dialog("🔔 แจ้งเตือนระบบ")
def show_popup():
    st.error(f"🚨 หมดอายุ {expired_count} รายการ")
    st.warning(f"⚠️ ใกล้หมด {near_count} รายการ")
    if st.button("ปิด"):
        st.session_state.popup_shown = True

if expired_count > 0 and not st.session_state.popup_shown:
    show_popup()

# =========================
# 🔢 KPI
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if st.button("all", key="btn_all"):
        st.session_state.filter_status = "ทั้งหมด"
    st.markdown(f"<div>📦 พนักงานทั้งหมด</div><div class='kpi'>{len(df)}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if st.button("near", key="btn_near"):
        st.session_state.filter_status = "ใกล้หมด"
    st.markdown(f"<div>⚠️ ใกล้หมด</div><div class='kpi'>{near_count}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if st.button("expired", key="btn_expired"):
        st.session_state.filter_status = "หมดอายุ"
    st.markdown(f"<div>❌ หมดอายุ</div><div class='kpi'>{expired_count}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 🔍 SEARCH
search = st.text_input("🔍 ค้นหา (ชื่อพนักงาน / เบอร์โทร)")

# =========================
# 📊 กราฟ
col4, col5 = st.columns(2)

with col4:
    fig = px.pie(df, names='สถานะ', hole=0.4)
    fig.update_layout(transition_duration=800)
    st.plotly_chart(fig, use_container_width=True)

with col5:
    df['เดือน'] = df['วันหมดอายุ'].dt.to_period('M').astype(str)
    fig2 = px.bar(df, x='เดือน', color='สถานะ')
    fig2.update_layout(transition_duration=800)
    st.plotly_chart(fig2, use_container_width=True)

# =========================
# 📋 TABLE
st.subheader("📋 ตารางวันหมดอายุ")

df_sorted = df.sort_values(by='วันหมดอายุ')

if st.session_state.filter_status == "ใกล้หมด":
    df_show = df_sorted[df_sorted['สถานะ'] == "ใกล้หมด"]
elif st.session_state.filter_status == "หมดอายุ":
    df_show = df_sorted[df_sorted['สถานะ'] == "หมดอายุ"]
else:
    df_show = df_sorted

# 🔍 filter search
if search:
    df_show = df_show[
        df_show['ชื่อพนักงาน'].astype(str).str.contains(search, case=False) |
        df_show['เบอร์โทร'].astype(str).str.contains(search, case=False)
    ]

st.write(f"🔎 กำลังแสดง: {st.session_state.filter_status}")
st.dataframe(df_show, use_container_width=True)
