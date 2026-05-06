import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
st.set_page_config(page_title="Employee Dashboard", layout="wide")

# 🧠 state
if "filter_status" not in st.session_state:
    st.session_state.filter_status = "ทั้งหมด"

if "popup_shown" not in st.session_state:
    st.session_state.popup_shown = False

# =========================
# 🔗 Google Sheets
sheet_url = "https://docs.google.com/spreadsheets/d/1JbU_0hNzrYNAGvoEnN0etL9DkJ0vnhbtM6KNHBYtUgY/export?format=csv"

# =========================
st.title("📊 Employee Dashboard")

# =========================
# โหลดข้อมูล
@st.cache_data
def load_data(url):
    for h in [0,1,2]:
        try:
            df = pd.read_csv(url, header=h)
            if len(df.columns) >= 3:
                return df
        except:
            pass
    return pd.read_csv(url)

df = load_data(sheet_url)

# =========================
# 🧹 ล้าง column
df.columns = (
    df.columns.astype(str)
    .str.strip()
    .str.replace("\ufeff","")
    .str.replace("\n","")
)

# 🔍 หา column
def find_col(keywords):
    for col in df.columns:
        for k in keywords:
            if k in col:
                return col
    return None

name_col = find_col(["ชื่อ"])
phone_col = find_col(["เบอร์","โทร"])
expiry_col = find_col(["วันหมดอายุ","หมดอายุ"])

# fallback
if not expiry_col:
    df.columns = range(len(df.columns))
    name_col = 0
    phone_col = 2
    expiry_col = 6

df.rename(columns={
    name_col: "ชื่อพนักงาน",
    phone_col: "เบอร์โทร",
    expiry_col: "วันหมดอายุ"
}, inplace=True)

# =========================
# 📅 แปลงวัน
df['วันหมดอายุ'] = pd.to_datetime(df['วันหมดอายุ'], dayfirst=True, errors='coerce')

df['วันหมดอายุ'] = df['วันหมดอายุ'].apply(
    lambda x: x.replace(year=x.year-543) if pd.notnull(x) and x.year > 2400 else x
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
# 🚨 แจ้งเตือน + POPUP
near = (df['สถานะ']=="ใกล้หมด").sum()
expired = (df['สถานะ']=="หมดอายุ").sum()

if expired > 0:
    st.error(f"🚨 หมดอายุ {expired} รายการ")

if near > 0:
    st.warning(f"⚠️ ใกล้หมด {near} รายการ")

@st.dialog("🔔 แจ้งเตือนสำคัญ")
def show_popup():
    st.error(f"🚨 หมดอายุ {expired} รายการ")
    st.warning(f"⚠️ ใกล้หมด {near} รายการ")
    if st.button("ปิด"):
        st.session_state.popup_shown = True

if expired > 0 and not st.session_state.popup_shown:
    show_popup()

# =========================
# 🔢 KPI
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("ทั้งหมด"):
        st.session_state.filter_status = "ทั้งหมด"
    st.metric("ทั้งหมด", len(df))

with c2:
    if st.button("ใกล้หมด"):
        st.session_state.filter_status = "ใกล้หมด"
    st.metric("ใกล้หมด", near)

with c3:
    if st.button("หมดอายุ"):
        st.session_state.filter_status = "หมดอายุ"
    st.metric("หมดอายุ", expired)

# =========================
# 🔍 SEARCH
search = st.text_input("🔍 ค้นหา", placeholder="พิมพ์ชื่อหรือเบอร์โทร...")

# =========================
# 📊 กราฟ
col1, col2 = st.columns(2)

with col1:
    fig = px.pie(df, names='สถานะ', hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

with col2:
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
        df_sorted['ชื่อพนักงาน'].astype(str).str.contains(search, case=False, na=False) |
        df_sorted['เบอร์โทร'].astype(str).str.contains(search, case=False, na=False)
    ]

st.dataframe(df_sorted, use_container_width=True)
