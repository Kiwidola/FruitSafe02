import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import joblib
from streamlit_autorefresh import st_autorefresh
import base64

# รีเฟรชทุก 10 วินาที (10000 ms)
st_autorefresh(interval=10_000, key="refresh")

# โหลดโมเดล (ตรวจสอบให้ Model.pkl อยู่ในโฟลเดอร์เดียวกับไฟล์นี้)
model = joblib.load('Model.pkl')

# กำหนด scope และโหลดข้อมูล service account จาก secrets ของ Streamlit Cloud
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_info = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(credentials_info, scopes=scope)

# เชื่อมต่อ Google Sheet
client = gspread.authorize(creds)
sheet = client.open("FruitSafe").sheet1

# ดึงข้อมูลแถวที่ 1 จาก Sheet
try:
    row_data = sheet.row_values(2)
except Exception as e:
    st.error(f"Cannot access Google Sheet: {e}")
    st.stop()

# ฟังก์ชันแปลงรูปภาพเป็น base64 string สำหรับ embed ใน HTML
def img_to_base64_str(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# โหลดภาพและแปลงเป็น base64
img0_b64 = img_to_base64_str("guava0.png")
img1_b64 = img_to_base64_str("guava1.png")
img3_b64 = img_to_base64_str("guava3.png")

predicted_percent = 0  # ค่าเริ่มต้น ถ้าไม่มีข้อมูลหรือ error จะไม่โชว์ผล

if len(row_data) >= 10:
    try:
        # แปลงข้อมูลจาก sheet เป็น float 10 ค่าแรก
        input_data = [float(x) for x in row_data[:10]]
        # ทำนายความปลอดภัยโดยใช้โมเดล
        prob_safe = model.predict_proba([input_data])[1][1]
        predicted_percent = int(prob_safe * 100)

        # ลบแถวแรกหลังประมวลผล (ไม่ลบถ้ามี error)
        sheet.delete_rows(1)

    except Exception as e:
        st.error(f"Prediction error: {e}")

# เรียก JS ฟังก์ชันแสดงผลเฉพาะเมื่อมีข้อมูล
call_show_prediction_js = f"showPrediction({predicted_percent});" if predicted_percent > 0 else ""

# สร้าง HTML embed ด้วย base64 รูปและผลการทำนาย
html_code = f"""
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no" />
  <title>FruitSafe</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Rubik:wght@500&family=Merriweather:wght@700&display=swap');

    html, body {{
      margin: 0;
      padding: 0;
      height: 100%;
      overflow: hidden;
    }}

    body {{
      font-family: 'Rubik', sans-serif;
      background-color: #fefae0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 20px;
      height: 100vh;
      box-sizing: border-box;
      user-select: none;
      position: relative;
    }}

    .logo {{
      font-family: 'Merriweather', serif;
      font-size: 36px;
      color: #2e7d32;
      text-align: center;
      margin-bottom: 20px;
    }}

    .results-label {{
      color: #e67e22;
      font-size: 20px;
      margin-bottom: 10px;
      border-top: 2px solid #c5e1a5;
      border-bottom: 2px solid #c5e1a5;
      padding: 5px 20px;
    }}

    .advice {{
      font-size: 16px;
      color: #333;
      text-align: center;
      max-width: 300px;
      margin-top: 10px;
      min-height: 160px;
    }}

    .advice img {{
      margin-top: 12px;
      max-width: 100%;
      height: auto;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}

    .confidence {{
      position: absolute;
      bottom: 12px;
      right: 16px;
      font-size: 14px;
      color: #666;
      font-style: italic;
    }}
  </style>
</head>
<body>

  <div class="logo">Fruit<br>Safe</div>

  <div class="results-label">ผลการตรวจ</div>
  <div id="advice" class="advice"></div>
  <div id="confidence" class="confidence"></div>

  <script>
    function showPrediction(value) {{
      const adviceEl = document.getElementById('advice');
      const confEl = document.getElementById('confidence');

      let color = '#2e7d32';
      let advice = '';
      let imgSrc = '';
      let imgAlt = '';

      if (value <= 20) {{
        color = 'green';
        advice = '<span style="font-size: 2em; color: green;">ปลอดภัย</span>';
        imgSrc = "data:image/png;base64,{img1_b64}";
        imgAlt = 'รูปปลอดภัย';
      }} else if (value <= 40) {{
        color = '#e67e22';
        advice = '<span style="font-size: 2em; color: #e67e22;">เสี่ยงปานกลาง</span><br>' +
                 '<span style="font-size: 1.3em">ควรล้างผลไม้เพิ่ม และตรวจอีกครั้ง</span>';
        imgSrc = "data:image/png;base64,{img3_b64}";
        imgAlt = 'รูปเสี่ยงปานกลาง';
      }} else {{
        color = 'red';
        advice = '<span style="font-size: 2em; color: red;">เสี่ยงสูง!</span><br>' +
                 '<span style="font-size: 1.3em;">ควรล้างผลไม้เพิ่มหลายรอบ และตรวจอีกครั้ง</span>';
        imgSrc = "data:image/png;base64,{img0_b64}";
        imgAlt = 'รูปเสี่ยงสูง';
      }}

      advice += `<br><img src="${{imgSrc}}" alt="${{imgAlt}}">`;

      adviceEl.innerHTML = advice;
      confEl.innerHTML = `Confidence: ${value}%`;
    }}

    {call_show_prediction_js}
  </script>
</body>
</html>
"""

# ฝัง HTML ลงใน Streamlit โดยไม่ให้เลื่อนหน้าจอ (scrolling=False)
st.components.v1.html(html_code, height=700, scrolling=False)



