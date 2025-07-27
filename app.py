import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import joblib

# โหลดโมเดล
model = joblib.load('Model.pkl')

# โหลด secret
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_info = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(credentials_info, scopes=scope)

client = gspread.authorize(creds)
sheet = client.open("FruitSafe").sheet1

# ดึงข้อมูล
try:
    row_data = sheet.row_values(1)
except Exception as e:
    st.error(f"Cannot access Google Sheet: {e}")
    st.stop()

if len(row_data) >= 10:
    input_data = [float(x) for x in row_data[:10]]
    prob_safe = model.predict_proba([input_data])[0][0]
    predicted_percent = int(prob_safe * 100)

    # ลบแถว
    sheet.delete_rows(1)

    # ฝัง HTML + predicted_percent
    html_code = f"""
    <html>
    <head>
    <style>
      body {{
        font-family: 'Sarabun', sans-serif;
        text-align: center;
        padding: 2em;
      }}
      .logo {{
        font-size: 3em;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1em;
      }}
      .results-label {{
        font-size: 2em;
        margin-bottom: 0.5em;
      }}
      .results-value {{
        font-size: 3em;
        font-weight: bold;
      }}
      .advice {{
        margin-top: 1.5em;
        font-size: 1.2em;
      }}
    </style>
    </head>
    <body>
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
            imgSrc = 'https://i.imgur.com/QkWzX5h.png';
            imgAlt = 'รูปความเสี่ยงสูง';
          }} else if (value < 80) {{
            color = '#e67e22';
            advice = '<span style="font-size: 2em; color: #e67e22;">เสี่ยงปานกลาง</span><br> ' +
                     '<span style="font-size: 1.3em">ควรล้างผลไม้เพิ่ม และตรวจอีกครั้ง</span>';
            imgSrc = 'https://i.imgur.com/mrGwFLk.png';
            imgAlt = 'รูปความเสี่ยงปานกลาง';
          }} else {{
            color = 'green';
            advice = '<span style="font-size: 2em; color: green;">เสี่ยงต่ำ ปลอดภัย</span>';
            imgSrc = 'https://i.imgur.com/wq2jCOl.png';
            imgAlt = 'รูปความเสี่ยงต่ำ';
          }}

          advice += `<br><img src="${{imgSrc}}" alt="${{imgAlt}}" width="200">`;

          resultEl.textContent = value + '%';
          resultEl.style.color = color;
          adviceEl.innerHTML = advice;
        }}
        showPrediction({predicted_percent});
      </script>
    </body>
    </html>
    """

    st.components.v1.html(html_code, height=600, scrolling=False)

else:
    st.info("📥 Waiting for new data in Google Sheet row 1...")
