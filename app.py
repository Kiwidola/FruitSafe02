import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import joblib
from streamlit_autorefresh import st_autorefresh
import base64

# รีเฟรชทุก 10 วินาที (10000 ms)
st_autorefresh(interval=10_000, key="refresh")

# โหลดโมเดล
model = joblib.load('Model.pkl')

# กำหนด scope และโหลดข้อมูล service account จาก secrets ของ Streamlit Cloud
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_info = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(credentials_info, scopes=scope)

# เชื่อมต่อ Google Sheet
client = gspread.authorize(creds)
sheet = client.open("FruitSafe01").sheet1

# ดึงข้อมูลแถวที่ 2 จาก Sheet
try:
    row_data = sheet.row_values(2)
except Exception as e:
    st.error(f"Cannot access Google Sheet: {e}")
    st.stop()

# ฟังก์ชันแปลงรูปภาพเป็น base64 string
def img_to_base64_str(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# โหลดภาพและแปลงเป็น base64
img0_b64 = img_to_base64_str("guava0.png")
img1_b64 = img_to_base64_str("guava1.png")
img3_b64 = img_to_base64_str("guava3.png")
fruitsafe_b64 = img_to_base64_str("FruitSafe.jpg")
poster_b64 = img_to_base64_str("Poster.jpg")

predicted_percent = 0  # ค่าเริ่มต้น

if len(row_data) >= 10:
    try:
        input_data = [float(x) for x in row_data[:10]]
        prob_safe = model.predict_proba([input_data])[0][1]
        predicted_percent = int(prob_safe * 100)

        # ลบแถวที่ 1 หลังประมวลผล
        sheet.delete_rows(2)

    except Exception as e:
        st.error(f"Prediction error: {e}")

# เรียก JS ฟังก์ชันเมื่อมีผลลัพธ์ หรือแสดงสถานะเริ่มต้น
if len(row_data) >= 10:
    # มีข้อมูลใหม่ - แสดงผลลัพธ์ใหม่และบันทึก
    call_show_prediction_js = f"showPrediction({predicted_percent});"
    st.session_state.last_prediction = predicted_percent
elif 'last_prediction' in st.session_state and st.session_state.last_prediction > 0:
    # ไม่มีข้อมูลใหม่ แต่มีผลลัพธ์ล่าสุด - แสดงผลลัพธ์ล่าสุด
    call_show_prediction_js = f"showPrediction({st.session_state.last_prediction});"
else:
    # ไม่มีข้อมูลและไม่มีผลลัพธ์ล่าสุด - แสดงสถานะรอ
    call_show_prediction_js = "showDefaultState();"

# ซ่อน Header / Footer / Menu ของ Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stAppViewContainer"] {
        background-color: #fefae0;
        padding: 0 !important;
        margin: 0 !important;
    }
    [data-testid="stAppViewBlockContainer"] {
        padding: 0 !important;
        margin: 0 !important;
    }
    .main .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# HTML ฝังผลลัพธ์
html_code = f"""
<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Fruit Safe Card</title>
<link href="https://fonts.googleapis.com/css2?family=Rubik:wght@500&family=Merriweather:wght@700&display=swap" rel="stylesheet" />
<style>
  :root{{
    --cream: #fef8e5;
    --green: #2f8b3e;   
  }}

  body{{
    margin:0;
    padding:0;
    height:100vh;
    width:100vw;
    overflow:hidden;
    background:var(--cream);
    font-family: 'Rubik', 'Merriweather', system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  }}

  .card{{
    width: 100vw;
    height: 100vh;
    background: var(--cream);
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:space-between;
    padding: 40px 20px;
    box-sizing: border-box;
  }}

  .results-label {{
    color: #e67e22;
    font-size: 16px;
    margin-top: 0;
    margin-bottom: 10px;
    border-top: 2px solid #c5e1a5;
    border-bottom: 2px solid #c5e1a5;
    padding: 4px 16px;
    text-align: center;
  }}

  .results-value {{
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 6px;
    transition: color 0.3s;
    text-align: center;
  }}

  .logo img {{
    max-width: 120px;
    height: auto;
    display: block;
    margin: 0 auto 10px;
  }}

  .result{{
    text-align:center;
  }}

  .image-wrap{{
    width: 80%;
    max-width:250px;
    aspect-ratio: 1.8/1;
    position:relative;
    display:flex;
    flex-direction: column;
    align-items:center;
    justify-content:center;
  }}

  .fruit{{
    width:100%;
    height:100%;
    object-fit:contain;
    border-radius:12px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.06);
    display:block;
  }}

  .meta{{
    width:100%;
    display:flex;
    flex-direction: column;
    align-items:center;
    gap: 6px;
    margin-top: auto;
  }}

  .percent {{
    font-size: 18px;
    font-weight: 700;
    text-align: center;
    display: flex;
    align-items: center;
    gap: 6px;
  }}

  .percent small {{
    font-size: 14px;
    color: #000000;
    font-weight: 500;
  }}

  .btn{{
    width:85%;
    max-width:220px;
    padding:10px;
    border-radius:10px;
    border:2px solid #2e7d32;
    background: #fffdf7;
    text-align:center;
    font-weight:560;
    cursor:pointer;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    font-family: 'Rubik', sans-serif;
    font-size: 0.9em;
  }}

  .button-group {{
    width: 85%;
    max-width: 220px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    justify-content: center;
  }}

  .toggle-btn {{
    width: 100%;
    background: none;
    border: none;
    font-size: 0.9em;
    font-weight: 565;
    color: var(--green);
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0;
  }}

  .arrow {{
    display: inline-block;
    transition: transform 0.3s ease;
    font-weight: 700;
    font-size: 1.2em;
  }}

  .toggle-btn[aria-expanded="true"] .arrow {{
    transform: rotate(180deg);
  }}

  .toggle-content {{
    margin-top: 8px;
    font-size: 0.9em;
    line-height: 1.4;
    color: #333;
  }}

  .toggle-content img {{
    max-width: 100%;
    height: auto;
    border-radius: 8px;
  }}

  .sub {{
    font-size: 1.2em;
    text-align: center;
    margin-top: 8px;
    color: #333;
  }}
</style>
</head>
<body>
  <div class="card" role="region" aria-label="ผลการตรวจ Fruit Safe">
    <div class="logo" aria-hidden="false">
      <img src="data:image/jpeg;base64,{fruitsafe_b64}" alt="FutureEd Logo" />
    </div>

    <div class="divider" aria-hidden="true"></div>

    <div class="results-label">ผลการตรวจ</div>

    <div class="result" role="status" aria-live="polite">
      <div id="result" class="results-value"></div>
      <div id="advice" class="sub">-</div>
    </div>



    <div class="meta">
      <div class="percent" id="percentDisplay"><small>สารตกค้าง</small> --%</div>
      <div class="button-group">
        <button class="btn" onclick="openLink()">วิธีการล้างฝรั่ง</button>
      </div>
    </div>

    <div class="toggle-section" style="margin-top: 10px;">
      <button class="toggle-btn" aria-expanded="false" aria-controls="info1" onclick="toggleInfo('info1', this)">
         <span style="border-bottom: 2px solid #2f8b3e;">สารเคมีผลกระทบคืออะไร</span>
        <span class="arrow">▼</span>
      </button>
      <div id="info1" class="toggle-content" hidden>
        <img src="data:image/jpeg;base64,{poster_b64}" alt="โปสเตอร์สารเคมี organophosphate และ Carbamate" style="max-width:100%; height:auto;">
      </div>
    </div>
  </div>

<script>
  function showPrediction(value) {{
    const adviceEl = document.getElementById('advice');
    const fruitImg = document.getElementById('fruitImage');
    const resultEl = document.getElementById('result');
    const percentEl = document.getElementById('percentDisplay');

    let color = '';
    let advice = '';
    let imgSrc = '';
    let imgAlt = '';

    if (value <= 20) {{
      color = 'green';
      advice = '<span style="font-size: 2em; color: green;">เสี่ยงต่ำ ปลอดภัย</span>';
      imgSrc = "data:image/png;base64,{img1_b64}";
      imgAlt = 'รูปความเสี่ยงต่ำ';
    }} else if (value <= 40) {{
      color = '#e67e22';
      advice = '<span style="font-size: 2em; color: #e67e22;">เสี่ยงปานกลาง</span><br> ' +
               '<span style="font-size: 1.3em">ควรล้างผลไม้เพิ่ม และตรวจอีกครั้ง</span>';
      imgSrc = "data:image/png;base64,{img3_b64}";
      imgAlt = 'รูปความเสี่ยงปานกลาง';
    }} else {{
      color = 'red';
      advice = '<span style="font-size: 2em; color: red;">เสี่ยงสูง!</span><br>' +
               '<span style="font-size: 1.3em;">ต้องล้างผลไม้เพิ่มหลายรอบ และตรวจอีกครั้ง</span><br>';
      imgSrc = "data:image/png;base64,{img0_b64}";
      imgAlt = 'รูปความเสี่ยงสูง';
    }}

    resultEl.textContent = '';
    percentEl.innerHTML = '<small>สารตกค้าง</small> ' + value + '%';
    percentEl.style.color = color;
    adviceEl.innerHTML = advice;
    fruitImg.src = imgSrc;
    fruitImg.alt = imgAlt;
  }}

  function showDefaultState() {{
    const adviceEl = document.getElementById('advice');
    const fruitImg = document.getElementById('fruitImage');
    const resultEl = document.getElementById('result');
    const percentEl = document.getElementById('percentDisplay');
    
    resultEl.textContent = '';
    percentEl.innerHTML = '<small>สารตกค้าง</small> --%';
    percentEl.style.color = '#666';
    adviceEl.innerHTML = '<span style="font-size: 1.4em; color: #666;">รอข้อมูล...</span>';
    fruitImg.src = 'guava.jpg';
    fruitImg.alt = 'รูปฝรั่ง';
  }}

  function openLink() {{
    const url = prompt('วิธีการล้างฝรั่ง:', 'https://youtube.com/shorts/H2OW4IHmfYM?feature=share/');
    if (url) {{
      window.location.href = url;
    }}
  }}

  function toggleInfo(id, btn) {{
    const content = document.getElementById(id);
    const expanded = btn.getAttribute("aria-expanded") === "true";
    if (expanded) {{
      content.hidden = true;
      btn.setAttribute("aria-expanded", "false");
    }} else {{
      content.hidden = false;
      btn.setAttribute("aria-expanded", "true");
    }}
  }}

  {call_show_prediction_js}
</script>
</body>
</html>
"""

st.components.v1.html(html_code, height=0, scrolling=False)
