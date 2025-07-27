import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import joblib
from streamlit_autorefresh import st_autorefresh

# Load model
model = joblib.load('Model.pkl')

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("FruitSafe-cred.json", scope)
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
        prob = model.predict_proba([input_data])[0][1]
        predicted_percent = int(prob * 100)

        st.write(f"🧪 Prediction confidence (safe): **{prob:.2f}** ({predicted_percent}%)")

        if prob >= 0.80:
            st.success("✅ Safe to eat")
        elif prob >= 0.40:
            st.warning("⚠️ Not sure – retest or wash thoroughly")
        else:
            st.error("❌ Dangerous – Do not eat")

        # Delete the row after processing
        sheet.delete_rows(1)

        st.info("Waiting for new data...")

    except Exception as e:
        st.error(f"Prediction error: {e}")
else:
    st.info("Waiting for new data in Google Sheet row 1...")
