import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import joblib
from streamlit_autorefresh import st_autorefresh
import base64

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
        input_data = [float(x) for x in row_data[:10]]
        prob_safe = model.predict_proba([input_data])[0][0]
        predicted_percent = int(prob_safe * 100)

        # ลบแถวแรกหลังประมวลผล
        sheet.delete_rows(1)

        st.info("รอข้อมูลใหม่จาก Google Sheet...")

    except Exception as e:
        st.error(f"Prediction error: {e}")
else:
    st.info("รอข้อมูลในแถวที่ 1 ของ Google Sheet...")


def img_to_base64_str(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


img0_b64 = img_to_base64_str("guava0.png")
img1_b64 = img_to_base64_str("guava1.png")
img3_b64 = img_to_base64_str("guava3.png")

html_code = f"""
<!DOCTYPE html>
<html lang="th">
<head> ... (your CSS here) ... </head>
<body>
  <div id="result">-</div>
  <div id="advice"></div>

  <script>
    function showPrediction(value) {{
      const resultEl = document.getElementById('result');
      const adviceEl = document.getElementById('advice');

      let color = '#2e7d32';
      let advice = '';
      let imgSrc = '';
      let imgAlt = '';

      if (value < 60) {{
        color = 'red';
        advice = '<span style="font-size: 2em; color: red;">เสี่ยงสูง!</span><br>' +
                 '<span style="font-size: 1.3em;">ควรล้างผลไม้เพิ่มหลายรอบ และตรวจอีกครั้ง</span><br>';
        imgSrc = "data:image/png;base64,{img0_b64}";
        imgAlt = 'รูปความเสี่ยงสูง';
      }} else if (value < 80) {{
        color = '#e67e22';
        advice = '<span style="font-size: 2em; color: #e67e22;">เสี่ยงปานกลาง</span><br>' +
                 '<span style="font-size: 1.3em">ควรล้างผลไม้เพิ่ม และตรวจอีกครั้ง</span>';
        imgSrc = "data:image/png;base64,{img3_b64}";
        imgAlt = 'รูปความเสี่ยงปานกลาง';
      }} else {{
        color = 'green';
        advice = '<span style="font-size: 2em; color: green;">เสี่ยงต่ำ ปลอดภัย</span>';
        imgSrc = "data:image/png;base64,{img1_b64}";
        imgAlt = 'รูปความเสี่ยงต่ำ';
      }}

      advice += `<br><img src="${{imgSrc}}" alt="${{imgAlt}}">`;

      resultEl.textContent = value + '%';
      resultEl.style.color = color;
      adviceEl.innerHTML = advice;
    }}

    showPrediction({predicted_percent});
  </script>
</body>
</html>
"""

st.components.v1.html(html_code, height=400)
