import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import joblib
from streamlit_autorefresh import st_autorefresh

# รีเฟรชทุก 10 วินาที
st_autorefresh(interval=10_000, key="refresh")

# โหลดโมเดล
model = joblib.load('Model.pkl')

# กำหนด scope และโหลดข้อมูล service account จาก secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_info = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(credentials_info, scopes=scope)

client = gspread.authorize(creds)
sheet = client.open("FruitSafe").sheet1

st.title("🍎 Fruit Pesticide Safety Checker")

try:
    row_data = sheet.row_values(1)
except Exception as e:
    st.error(f"Cannot access Google Sheet: {e}")
    st.stop()

if len(row_data) >= 10:
    try:
        # แปลงข้อมูลในแถวเป็น float 10 ค่า
        input_data = [float(x) for x in row_data[:10]]

        # ใช้ model.predict_proba() และเอาความน่าจะเป็นของ class 0 (safe)
        prob_safe = model.predict_proba([input_data])[0][0]
        predicted_percent = int(prob_safe * 100)

        # ฟังก์ชันแสดงผลแบบสีและข้อความเหมือนใน HTML ตัวอย่าง
        def display_result(value):
            if value < 60:
                color = "red"
                text = "เสี่ยงสูง! ควรล้างผลไม้เพิ่มหลายรอบ และตรวจอีกครั้ง"
                emoji = "❌"
            elif value < 80:
                color = "#e67e22"
                text = "เสี่ยงปานกลาง ควรล้างผลไม้เพิ่ม และตรวจอีกครั้ง"
                emoji = "⚠️"
            else:
                color = "green"
                text = "เสี่ยงต่ำ ปลอดภัย"
                emoji = "✅"
            return color, text, emoji

        color, advice_text, emoji = display_result(predicted_percent)

        st.markdown(f"<h1 style='color:{color};'>{emoji} ความปลอดภัย: {predicted_percent}%</h1>", unsafe_allow_html=True)
        st.write(advice_text)

        # ลบแถวที่ 1 หลังประมวลผลเสร็จ
        sheet.delete_rows(1)

        st.info("รอข้อมูลใหม่จาก Google Sheet...")

    except Exception as e:
        st.error(f"Prediction error: {e}")
else:
    st.info("รอข้อมูลในแถวที่ 1 ของ Google Sheet...")
