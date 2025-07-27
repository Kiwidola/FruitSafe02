import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import joblib
from streamlit_autorefresh import st_autorefresh

# Load model (ครั้งเดียว)
model = joblib.load('Model.pkl')
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# ✅ ดึง secrets จาก Streamlit
credentials_info = st.secrets["gcp_service_account"]

# ✅ สร้าง Credentials object
creds = Credentials.from_service_account_info(credentials_info, scopes=scope)

# ✅ ใช้ gspread
client = gspread.authorize(creds)
sheet = client.open("FruitSafe").sheet1


st.title("🍎 Fruit Pesticide Safety Checker")

# Auto-refresh every 10 seconds
st_autorefresh(interval=10_000, key="refresh")

try:
    row_data = sheet.row_values(1)
except Exception as e:
    st.error(f"Cannot access Google Sheet: {e}")
    st.stop()

if len(row_data) >= 10:
    try:
        input_data = [float(x) for x in row_data[:10]]
        # input_data = [10 features...]
        prob_safe = model.predict_proba([input_data])[0][0]  # ← confidence ของ class 0
        predicted_percent = int(prob_safe * 100)
        
        st.write(f"🧪 Prediction confidence (safe): **{prob_safe:.2f}** ({predicted_percent}%)")
        
        # แบ่งออกเป็น 3 ระดับ
        if prob_safe >= 0.80:
            st.success("✅ ปลอดภัย สามารถรับประทานได้")
        elif prob_safe >= 0.40:
            st.warning("⚠️ ไม่แน่ใจ แนะนำให้ล้างให้สะอาด หรือตรวจใหม่")
        else:
            st.error("❌ อันตราย ไม่ควรรับประทาน")


        try:
            sheet.delete_rows(1)
        except Exception as e:
            st.warning(f"Warning: Could not delete row: {e}")

        st.info("Waiting for new data...")

    except Exception as e:
        st.error(f"Prediction error: {e}")
else:
    st.info("Waiting for new data in Google Sheet row 1...")
