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
# 🔗 Google Sheets (แก้ตรงนี้)
sheet_url = "https://docs.google.com/spreadsheets/d/1JbU_0hNzrYNAGvoEnN0etL9DkJ0vnhbtM6KNHBYtUgY/edit?usp=sharing"

# =========================
st.title("📊 Employee Dashboard")

mode = st.radio("เลือกการใช้งาน", ["📱 มือถือ (ออนไลน์)", "💻 คอม (อัปโหลดไฟล์)"])

# =========================
# โหลดข้อมูล
if mode == "📱 มือถือ (ออนไลน์)":
    df = pd.read_csv(sheet_url)
else:
    uploaded_file = st.file_uploader("📥 อัปโหลด Excel", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
    else:
        st.stop()

# =========================
# 🧹 ล้างชื่อคอลัมน์ (กัน error)
df.columns = (
    df.columns
    .astype(str)
    .str.strip()
    .str.replace("\ufeff", "")
    .str.replace("\n", "")
    .str.replace("\r", "")
)

# 🔍 debug
st.write("📋 คอลัมน์:", df.columns.tolist())

# =========================
# 🎯 หา column อัตโนมัติ
def find_col(keywords):
    for col in df.columns:
        for k in keywords:
            if k in col:
                return col
    return None

name_col = find_col(["ชื่อ"])
phone_col = find_col(["เบอร์", "โทร"])
expiry_col = find_col(["วันหมดอายุ", "หมดอายุ", "expiry"])

# ❗ เช็ค
if not expiry_col:
    st.error("❌ ไม่พบคอลัมน์วันหมดอายุ")
    st.stop()

# rename
df.rename(columns={
    name_col: "ชื่อพนักงาน" if name_col else "ชื่อพนักงาน",
    phone_col: "เบอร์โทร" if phone_col else "เบอร์โทร",
    expiry_col: "วันหมดอายุ"
}, inplace=True)

# =========================
# 📅 แปลงวัน
df['วันหมดอายุ'] = pd.to_datetime(df['วันหมดอายุ'], dayfirst=True, errors='coerce')

# แปลง พ.ศ. → ค.ศ.
df['วันหมดอายุ'] = df['วันหมดอายุ'].apply(
    lambda x: x.replace(year=x.year - 543) if pd.notnull(x) and x.year > 2400 else x
)

# =========================
# 🧮 คำนวณ
today = pd.Timestamp.today().normalize()
df['เหลือ(วัน)'] = (df['วันหมดอายุ'] - today).dt.days

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
    st.error(f"🚨 หมดอายุ {expired_count} รายการ")

if near_count > 0:
    st.warning(f"⚠️ ใกล้หมด {near_count} รายการ")

@st.dialog("🔔 แจ้งเตือน")
def popup():
    st.error(f"🚨 หมดอายุ {expired_count}")
    st.warning(f"⚠️ ใกล้หมด {near_count}")
    if st.button("ปิด"):
        st.session_state.popup_shown = True

if expired_count > 0 and not st.session_state.popup_shown:
    popup()

# =========================
# 🔢 KPI
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("ทั้งหมด"):
        st.session_state.filter_status = "ทั้งหมด"
    st.metric("พนักงานทั้งหมด", len(df))

with col2:
    if st.button("ใกล้หมด"):
        st.session_state.filter_status = "ใกล้หมด"
    st.metric("ใกล้หมด", near_count)

with col3:
    if st.button("หมดอายุ"):
        st.session_state.filter_status = "หมดอายุ"
    st.metric("หมดอายุ", expired_count)

# =========================
# 🔍 SEARCH
search = st.text_input("🔍 ค้นหา (ชื่อ / เบอร์)")

# =========================
# 📊 กราฟ
col4, col5 = st.columns(2)

with col4:
    fig = px.pie(df, names='สถานะ', hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

with col5:
    df['เดือน'] = df['วันหมดอายุ'].dt.to_period('M').astype(str)
    fig2 = px.bar(df, x='เดือน', color='สถานะ')
    st.plotly_chart(fig2, use_container_width=True)

# =========================
# 📋 ตาราง
df_sorted = df.sort_values(by='วันหมดอายุ')

if st.session_state.filter_status != "ทั้งหมด":
    df_sorted = df_sorted[df_sorted['สถานะ'] == st.session_state.filter_status]

if search:
    df_sorted = df_sorted[
        df_sorted['ชื่อพนักงาน'].astype(str).str.contains(search, case=False) |
        df_sorted['เบอร์โทร'].astype(str).str.contains(search, case=False)
    ]

st.dataframe(df_sorted, use_container_width=True)
