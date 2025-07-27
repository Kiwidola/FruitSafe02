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

def img_to_base64_str(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

img0_b64 = img_to_base64_str("guava0.png")
img1_b64 = img_to_base64_str("guava1.png")
img3_b64 = img_to_base64_str("guava3.png")


predicted_percent = 0  # default value

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

# Now build your html_code with predicted_percent safely set:
html_code = f"""
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>FruitSafe</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Rubik:wght@500&family=Merriweather:wght@700&display=swap');

    body {{
      font-family: 'Rubik', sans-serif;
      background-color: #fefae0;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 20px;
      position: relative;
      min-height: 100vh;
      margin: 0;
    }}

    .logo {{
      font-family: 'Merriweather', serif;
      font-size: 36px;
      color: #2e7d32;
      text-align: center;
      margin-bottom: 20px;
      user-select: none;
    }}

    .results-label {{
      color: #e67e22;
      font-size: 20px;
      margin-bottom: 10px;
      border-top: 2px solid #c5e1a5;
      border-bottom: 2px solid #c5e1a5;
      padding: 5px 20px;
      user-select: none;
    }}

    .results-value {{
      font-size: 32px;
      font-weight: bold;
      margin-bottom: 10px;
      color: #2e7d32;
      transition: color 0.3s;
    }}

    .advice {{
      font-size: 16px;
      color: #333;
      text-align: center;
      max-width: 300px;
      margin-top: 10px;
      min-height: 160px;
    }}

    .reset-button {{
      position: fixed;
      bottom: 15px;
      right: 15px;
      background-color: #fefae0;
      border: none;
      color: #2e7d32;
      font-size: 14px;
      padding: 6px 12px;
      border-radius: 6px;
      cursor: pointer;
      box-shadow:none;
      transition: background-color 0.3s;
      z-index: 1000;
      user-select: none;
    }}

    .reset-button:hover {{
      background-color: #dcedc8;
    }}

    .advice img {{
      margin-top: 12px;
      max-width: 100%;
      height: auto;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
  </style>
</head>
<body>

  <button class="reset-button" onclick="randomScan()">รีเซ็ต</button>

  <div class="logo">Fruit<br>Safe</div>

  <div class="results-label">ผลการตรวจ</div>
  <div id="result" class="results-value">-</div>
  <div id="advice" class="advice"></div>

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

    function randomScan() {{
      // Optional: reset or simulate a new scan with random value
      const randomValue = Math.floor(Math.random() * 101);
      showPrediction(randomValue);
    }}

    // Show prediction with your Python-passed value
    showPrediction({predicted_percent});
  </script>
</body>
</html>
"""


st.components.v1.html(html_code, height=700)

