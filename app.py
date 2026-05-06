import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard", layout="wide")

# =========================
# 🔗 Google Sheets
sheet_url = "https://docs.google.com/spreadsheets/d/1JbU_0hNzrYNAGvoEnN0etL9DkJ0vnhbtM6KNHBYtUgY/export?format=csv"

st.title("📊 Employee Dashboard")

mode = st.radio("เลือกการใช้งาน", ["📱 ออนไลน์", "💻 อัปโหลดไฟล์"])

# =========================
# 🔥 ฟังก์ชันอ่าน CSV แบบกันพัง
def load_data():
    for h in [0, 1, 2]:  # ลองหลาย header
        try:
            df = pd.read_csv(sheet_url, header=h)
            if len(df.columns) >= 3:
                return df
        except:
            pass
    return pd.read_csv(sheet_url)

# =========================
# โหลดข้อมูล
if mode == "📱 ออนไลน์":
    df = load_data()
else:
    file = st.file_uploader("อัปโหลด Excel")
    if file:
        df = pd.read_excel(file)
    else:
        st.stop()

# =========================
# 🧹 ล้างชื่อคอลัมน์
df.columns = (
    df.columns.astype(str)
    .str.strip()
    .str.replace("\ufeff", "")
    .str.replace("\n", "")
)

st.write("📋 คอลัมน์ที่อ่านได้:", df.columns.tolist())

# =========================
# 🔍 หา column แบบอัจฉริยะ
def find_col(keywords):
    for col in df.columns:
        for k in keywords:
            if k in col:
                return col
    return None

name_col = find_col(["ชื่อ"])
phone_col = find_col(["เบอร์", "โทร"])
expiry_col = find_col(["วันหมดอายุ", "หมดอายุ", "expiry"])

# =========================
# ❗ fallback ถ้ายังหาไม่เจอ → ใช้ตำแหน่ง
if not expiry_col:
    st.warning("⚠️ หา column ไม่เจอ → ใช้ตำแหน่งแทน")
    df.columns = range(len(df.columns))
    name_col = 0
    phone_col = 2
    expiry_col = 6

# rename
df.rename(columns={
    name_col: "ชื่อพนักงาน",
    phone_col: "เบอร์โทร",
    expiry_col: "วันหมดอายุ"
}, inplace=True)

# =========================
# 📅 แปลงวัน
df['วันหมดอายุ'] = pd.to_datetime(df['วันหมดอายุ'], dayfirst=True, errors='coerce')

# แปลง พ.ศ.
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
# 🔢 KPI
st.subheader("📊 สรุป")
c1, c2, c3 = st.columns(3)
c1.metric("ทั้งหมด", len(df))
c2.metric("ใกล้หมด", (df['สถานะ']=="ใกล้หมด").sum())
c3.metric("หมดอายุ", (df['สถานะ']=="หมดอายุ").sum())

# =========================
# 📊 กราฟ
fig = px.pie(df, names='สถานะ', hole=0.4)
st.plotly_chart(fig, use_container_width=True)

# =========================
# 📋 ตาราง
st.subheader("📋 รายการ")
st.dataframe(df.sort_values(by='วันหมดอายุ'), use_container_width=True)
