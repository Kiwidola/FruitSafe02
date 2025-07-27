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
credentials_info["private_key"] = credentials_info["private_key"].replace("\\n", "\n")  # แปลง \n เป็น newline จริง
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

        # HTML+CSS+JS Template ใส่ค่า predicted_percent แทนที่ {predicted_value}
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
            .advice img {{
              margin-top: 12px;
              max-width: 100%;
              height: auto;
              border-radius: 8px;
              box-shadow: 0 2px 8px none;
            }}
          </style>
        </head>
        <body>
          <div class="logo">Fruit<br>Safe</div>
          <div class="results-label">ผลการตรวจ</div>
          <div id="result" class="results-value">-</div>
          <div id="advice" class="advice"></div>

          <script>
            const value = {predicted_percent};
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
              imgSrc = 'guava0.png';
              imgAlt = 'รูปความเสี่ยงสูง';
            }} else if (value < 80) {{
              color = '#e67e22';
              advice = '<span style="font-size: 2em; color: #e67e22;">เสี่ยงปานกลาง</span><br> ' +
                       '<span style="font-size: 1.3em">ควรล้างผลไม้เพิ่ม และตรวจอีกครั้ง</span>';
              imgSrc = 'guava3.png';
              imgAlt = 'รูปความเสี่ยงปานกลาง';
            }} else {{
              color = 'green';
              advice = '<span style="font-size: 2em; color: green;">เสี่ยงต่ำ ปลอดภัย</span>';
              imgSrc = 'guava1.png';
              imgAlt = 'รูปความเสี่ยงต่ำ';
            }}

            advice += `<br><img src="${{imgSrc}}" alt="${{imgAlt}}">`;

            resultEl.textContent = value + '%';
            resultEl.style.color = color;
            adviceEl.innerHTML = advice;
          </script>
        </body>
        </html>
        """

        # แสดง HTML ใน Streamlit
        st.components.v1.html(html_code, height=400)

        st.info("รอข้อมูลใหม่จาก Google Sheet...")

    except Exception as e:
        st.error(f"Prediction error: {e}")
else:
    st.info("รอข้อมูลในแถวที่ 1 ของ Google Sheet...")
