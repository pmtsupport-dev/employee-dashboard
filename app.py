import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# 📱 PAGE CONFIG
st.set_page_config(
    page_title="Employee Dashboard",
    page_icon="📱",
    layout="wide"
)

# =========================
# 📱 MOBILE APP UI
st.markdown("""
<style>

/* 🌌 พื้นหลัง */
.stApp {
    background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
    color: white;
}

/* ซ่อนเมนู */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* 📦 Container */
.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    padding-left: 1rem;
    padding-right: 1rem;
}

/* 🏷️ Title */
h1 {
    color: white !important;
    text-align: center;
    font-size: 34px !important;
    font-weight: bold;
}

/* 📊 KPI */
[data-testid="metric-container"] {
    background: rgba(17, 24, 39, 0.8);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 18px;
    border-radius: 20px;
    backdrop-filter: blur(12px);
    box-shadow: 0 0 20px rgba(0,255,255,0.12);
    transition: 0.3s;
}

/* ✨ Hover */
[data-testid="metric-container"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 0 25px rgba(0,255,255,0.35);
}

/* 🔘 Button */
.stButton > button {
    width: 100%;
    height: 50px;
    border-radius: 14px;
    border: none;
    background: linear-gradient(90deg,#06b6d4,#3b82f6);
    color: white;
    font-size: 16px;
    font-weight: bold;
    transition: 0.3s;
}

/* 🔥 Hover button */
.stButton > button:hover {
    transform: scale(1.02);
    box-shadow: 0 0 20px rgba(59,130,246,0.5);
}

/* 🔍 Search */
.stTextInput input {
    border-radius: 14px;
    height: 50px;
    background-color: rgba(255,255,255,0.06);
    color: white !important;
    border: 1px solid rgba(255,255,255,0.1);
    font-size: 16px;
}

/* 📋 Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 18px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.08);
}

/* 📱 Mobile */
@media (max-width: 768px) {

    h1 {
        font-size: 28px !important;
    }

    .stButton > button {
        height: 54px;
        font-size: 18px;
    }

    .stTextInput input {
        height: 54px;
        font-size: 18px;
    }

    [data-testid="metric-container"] {
        margin-bottom: 10px;
    }

    iframe {
        height: 380px !important;
    }
}

</style>
""", unsafe_allow_html=True)

# =========================
# 🧠 SESSION
if "filter_status" not in st.session_state:
    st.session_state.filter_status = "ทั้งหมด"

if "popup_shown" not in st.session_state:
    st.session_state.popup_shown = False

# =========================
# 🔗 GOOGLE SHEETS CSV
sheet_url = "https://docs.google.com/spreadsheets/d/1JbU_0hNzrYNAGvoEnN0etL9DkJ0vnhbtM6KNHBYtUgY/export?format=csv"

# =========================
# 📥 LOAD DATA
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
# 🧹 CLEAN COLUMN
df.columns = (
    df.columns.astype(str)
    .str.strip()
    .str.replace("\ufeff", "")
    .str.replace("\n", "")
)

# =========================
# 🔍 FIND COLUMN
def find_col(keywords):

    for col in df.columns:

        for k in keywords:

            if k in col:
                return col

    return None

name_col = find_col(["ชื่อ"])
phone_col = find_col(["เบอร์", "โทร"])
expiry_col = find_col(["วันหมดอายุ", "หมดอายุ"])

# =========================
# 🔥 FIX COLUMN
if not expiry_col:

    df.columns = range(len(df.columns))

    name_col = 0
    phone_col = 2
    expiry_col = 6

# =========================
# 🏷️ RENAME
df.rename(columns={
    name_col: "ชื่อพนักงาน",
    phone_col: "เบอร์โทร",
    expiry_col: "วันหมดอายุ"
}, inplace=True)

# =========================
# 📅 DATE
df['วันหมดอายุ'] = pd.to_datetime(
    df['วันหมดอายุ'],
    dayfirst=True,
    errors='coerce'
)

# 🇹🇭 พ.ศ → ค.ศ
df['วันหมดอายุ'] = df['วันหมดอายุ'].apply(
    lambda x: x.replace(year=x.year - 543)
    if pd.notnull(x) and x.year > 2400
    else x
)

# =========================
# 🧮 CALCULATE
today = pd.Timestamp.today().normalize()

df['เหลือ(วัน)'] = (
    df['วันหมดอายุ'] - today
).dt.days

# =========================
# 🎯 STATUS
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
# 🔔 ALERT
near = (df['สถานะ']=="ใกล้หมด").sum()
expired = (df['สถานะ']=="หมดอายุ").sum()

if expired > 0:
    st.error(f"🚨 หมดอายุ {expired} รายการ")

if near > 0:
    st.warning(f"⚠️ ใกล้หมด {near} รายการ")

# =========================
# 🔥 POPUP
@st.dialog("🔔 แจ้งเตือนสำคัญ")
def popup():

    st.error(f"🚨 หมดอายุ {expired} รายการ")
    st.warning(f"⚠️ ใกล้หมด {near} รายการ")

    if st.button("ปิด"):
        st.session_state.popup_shown = True

if expired > 0 and not st.session_state.popup_shown:
    popup()

# =========================
# 🏷️ TITLE
st.title("📱 Employee Dashboard")

# =========================
# 🔢 KPI
c1, c2, c3 = st.columns(3)

with c1:

    if st.button("ทั้งหมด"):
        st.session_state.filter_status = "ทั้งหมด"

    st.metric(
        "ทั้งหมด",
        len(df)
    )

with c2:

    if st.button("ใกล้หมด"):
        st.session_state.filter_status = "ใกล้หมด"

    st.metric(
        "ใกล้หมด",
        near
    )

with c3:

    if st.button("หมดอายุ"):
        st.session_state.filter_status = "หมดอายุ"

    st.metric(
        "หมดอายุ",
        expired
    )

# =========================
# 🔍 SEARCH
search = st.text_input(
    "🔍 ค้นหา",
    placeholder="พิมพ์ชื่อหรือเบอร์โทร..."
)

# =========================
# 📊 GRAPH
col1, col2 = st.columns(2)

with col1:

    fig = px.pie(
        df,
        names='สถานะ',
        hole=0.55,
        color='สถานะ',
        color_discrete_map={
            'ปกติ': '#22c55e',
            'ใกล้หมด': '#f59e0b',
            'หมดอายุ': '#ef4444',
            'ไม่มีข้อมูล': '#6b7280'
        }
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=420
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

with col2:

    df['เดือน'] = df['วันหมดอายุ'].dt.to_period('M').astype(str)

    fig2 = px.bar(
        df,
        x='เดือน',
        color='สถานะ',
        title='แนวโน้มวันหมดอายุ'
    )

    fig2.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=420
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

# =========================
# 📋 FILTER
df_show = df.sort_values(by='วันหมดอายุ')

if st.session_state.filter_status != "ทั้งหมด":

    df_show = df_show[
        df_show['สถานะ']
        == st.session_state.filter_status
    ]

# =========================
# 🔍 SEARCH FILTER
if search:

    df_show = df_show[
        df_show['ชื่อพนักงาน']
        .astype(str)
        .str.contains(search, case=False, na=False)

        |

        df_show['เบอร์โทร']
        .astype(str)
        .str.contains(search, case=False, na=False)
    ]

# =========================
# 📋 TABLE + REALTIME EDIT
st.subheader("📋 จัดการข้อมูลพนักงาน")

df_show = df_show.sort_values(by='วันหมดอายุ')

edited_df = st.data_editor(
    df_show,
    num_rows="dynamic",
    use_container_width=True,
    height=500,
    key="employee_editor"
)

# =========================
# 💾 SAVE + REFRESH
save1, save2 = st.columns(2)

with save1:

    if st.button("💾 บันทึกข้อมูล", use_container_width=True):

        try:

            edited_df.to_csv(
                "updated_employee_data.csv",
                index=False,
                encoding="utf-8-sig"
            )

            st.success("✅ บันทึกข้อมูลเรียบร้อย")

            st.toast(
                "📁 บันทึกข้อมูลแล้ว",
                icon="✅"
            )

        except Exception as e:

            st.error(f"❌ Error: {e}")

with save2:

    if st.button("🔄 รีเฟรช", use_container_width=True):

        st.cache_data.clear()

        st.rerun()

# =========================
# 📥 DOWNLOAD CSV
csv = edited_df.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    label="📥 ดาวน์โหลด CSV",
    data=csv,
    file_name="employee_dashboard.csv",
    mime="text/csv",
    use_container_width=True
)

# =========================
# 📊 SUMMARY
st.markdown(f"""
<div style="
background: rgba(255,255,255,0.05);
padding:15px;
border-radius:15px;
margin-top:10px;
border:1px solid rgba(255,255,255,0.1);
">

📊 จำนวนข้อมูลทั้งหมด:
<b>{len(edited_df)}</b> รายการ

</div>
""", unsafe_allow_html=True)
