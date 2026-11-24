import base64
import os
import time
from pathlib import Path

import streamlit as st
from google import genai
from google.genai import types

# ---------------------------------------------------------------
# 1. إعداد واجهة التطبيق
# ---------------------------------------------------------------
st.set_page_config(
    page_title="UAQ Chamber Smart Assistant",
    page_icon="🏛️",
    layout="centered",
)


def set_bg(img_path):
    file = Path(img_path)
    if not file.exists():
        return
    ext = file.suffix.lower().replace(".", "")
    if ext == "jpg":
        ext = "jpeg"
    data = base64.b64encode(file.read_bytes()).decode()
    st.markdown(
        f"""
    <style>
        [data-testid="stAppViewContainer"] {{
            background-image: linear-gradient(
                rgba(248, 250, 252, 0.85),
                rgba(248, 250, 252, 0.88)
            ), url("data:image/{ext};base64,{data}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        [data-testid="stChatMessage"] {{
            background-color: rgba(255, 255, 255, 0.94) !important;
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )


set_bg("uaq_bg.jpg")

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&family=Noto+Nastaliq+Urdu:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Cairo', 'Noto Nastaliq Urdu', sans-serif;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent;}

    .uaq-header {
        background: linear-gradient(135deg, #0F2A4A 0%, #1B4370 100%);
        padding: 1.5rem 2rem;
        border-radius: 14px;
        color: white;
        text-align: right;
        direction: rtl;
        border-bottom: 4px solid #C5A059;
        box-shadow: 0 4px 15px rgba(15, 42, 74, 0.12);
        margin-bottom: 1.2rem;
    }
    .uaq-header h1 {
        margin: 0;
        font-size: 1.65rem;
        font-weight: 700;
        color: #FFFFFF;
    }
    .uaq-header p {
        margin: 0.35rem 0 0 0;
        font-size: 0.95rem;
        color: #E2E8F0;
    }
    .uaq-badge {
        display: inline-block;
        background-color: rgba(197, 160, 89, 0.2);
        color: #F3D99B;
        border: 1px solid #C5A059;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        margin-top: 0.6rem;
    }

    [data-testid="stChatMessage"] {
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
        direction: rtl;
        text-align: right;
    }

    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        border: 1px solid #CBD5E1;
        background-color: #FFFFFF;
        color: #0F2A4A;
        font-weight: 600;
        padding: 0.6rem 0.8rem;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        border-color: #C5A059;
        background-color: #0F2A4A;
        color: #FFFFFF;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="uaq-header">
    <h1>🏛️ المساعد الذكي لغرفة تجارة وصناعة أم القيوين</h1>
    <p>UAQ Chamber Smart Assistant — دليلك الفوري للخدمات، العضوية، والجهات داخل المبنى</p>
    <span class="uaq-badge">● الخدمات الإلكترونية متاحة 24/7 | الرقم المجاني: 800827</span>
</div>
""",
    unsafe_allow_html=True,
)

col1, col2, col3, col4 = st.columns(4)
quick_prompt = None

with col1:
    if st.button("🏢 الجهات داخل المبنى"):
        quick_prompt = "ما هي الجهات والأقسام الموجودة داخل مبنى غرفة أم القيوين مع الشرح وأرقام التواصل؟"
with col2:
    if st.button("🪪 خدمات العضوية"):
        quick_prompt = "ما هي خدمات العضوية المتوفرة في غرفة أم القيوين؟"
with col3:
    if st.button("📄 شهادات المنشأ"):
        quick_prompt = "ما هي خدمات شهادات المنشأ والتصديق المتوفرة؟"
with col4:
    if st.button("📞 التواصل وساعات العمل"):
        quick_prompt = "ما هي ساعات العمل الرسمية وأرقام التواصل وحسابات التواصل الاجتماعي؟"

st.title("🏛️ UAQ Chamber Smart Assistant | المساعد الذكي لغرفة أم القيوين")
st.markdown("Ask me in Arabic, English, or Urdu about UAQ Chamber services, memberships, and departments.")

# ---------------------------------------------------------------
# 2. المفتاح والموديلات
# ---------------------------------------------------------------
API_KEY = None
try:
    API_KEY = st.secrets.get("GEMINI_API_KEY", None)
except Exception:
    pass

API_KEY = API_KEY or os.environ.get("GEMINI_API_KEY") or "AQ.Ab8RN6IarvmkluaXSZPy0n9KMvuARbyJk3lt20rpYLIqvksnoQ"

if not API_KEY:
    st.error("مفتاح Gemini غير موجود. ضعه في .streamlit/secrets.toml أو في متغير البيئة GEMINI_API_KEY.")
    st.stop()

client = genai.Client(api_key=API_KEY)

MODEL_CHAIN = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
]
RETRIES_PER_MODEL = 3

WELCOME = "مرحباً بك في غرفة أم القيوين! / Welcome to UAQ Chamber! / ام القیوین چیمبر میں خوش آمدید! کیسے مدد کر سکتا ہوں؟"
IDLE_TIMEOUT_SECONDS = 30  # 30 ثانية

# ---------------------------------------------------------------
# 3. الشريط الجانبي
# ---------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ إعدادات التحكم")
    if st.button("🗑️ مسح المحادثة (Clear Chat)"):
        st.session_state.messages = [{"role": "assistant", "content": WELCOME}]
        st.session_state.last_activity = time.time()
        st.rerun()

# ---------------------------------------------------------------
# 4. قاعدة المعرفة
# ---------------------------------------------------------------
try:
    with open("chamber_info.txt", "r", encoding="utf-8") as f:
        chamber_knowledge = f.read()
except FileNotFoundError:
    chamber_knowledge = "UAQ Chamber of Commerce and Industry provides services for businesses, trade licenses, and memberships."

system_instruction = f"""
You are the official trilingual (Arabic, English, and Urdu) AI Assistant for the Umm Al Quwain (UAQ) Chamber of Commerce and Industry.
Answer accurately based ONLY on the official knowledge base below. If the answer is not in the knowledge base,
say you don't have that information and suggest contacting the Chamber on 800827.
Detect the user's language (Arabic, English, or Urdu) and reply in the same language, in a polite, official tone.

Knowledge Base:
{chamber_knowledge}
"""

# ---------------------------------------------------------------
# 5. سجل المحادثة والمسح التلقائي بعد 30 ثانية سكون
# ---------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": WELCOME}]

if "last_activity" not in st.session_state:
    st.session_state.last_activity = time.time()


@st.fragment(run_every=5)
def auto_clear_watcher():
    has_chat = len(st.session_state.messages) > 1 or st.session_state.messages[0]["content"] != WELCOME
    if has_chat and (time.time() - st.session_state.last_activity >= IDLE_TIMEOUT_SECONDS):
        st.session_state.messages = [{"role": "assistant", "content": WELCOME}]
        st.session_state.last_activity = time.time()
        st.rerun()


auto_clear_watcher()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ---------------------------------------------------------------
# 6. دوال مساعدة
# ---------------------------------------------------------------
def build_history():
    history = []
    for m in st.session_state.messages[-11:-1]:
        role = "user" if m["role"] == "user" else "model"
        history.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))
    return history


def ask_gemini(user_parts):
    contents = build_history() + [types.Content(role="user", parts=user_parts)]
    last_error = None
    for model in MODEL_CHAIN:
        for attempt in range(min(RETRIES_PER_MODEL, 2)):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                    ),
                )
                return response.text, model
            except Exception as e:
                last_error = e
                msg = str(e)
                transient = any(code in msg for code in ("503", "429", "500", "UNAVAILABLE", "RESOURCE_EXHAUSTED"))
                if not transient:
                    break
                if attempt == 0:
                    time.sleep(0.5)
    raise last_error


# ---------------------------------------------------------------
# 7. استقبال السؤال
# ---------------------------------------------------------------
chat_input_text = st.chat_input("اكتب سؤالك / Type your question / اپنا سوال لکھیں...")
prompt = quick_prompt or chat_input_text

if prompt:
    st.session_state.last_activity = time.time()
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("جاري التفكير... / Thinking..."):
            try:
                parts = [types.Part.from_text(text=prompt)]
                reply, used_model = ask_gemini(parts)
                st.markdown(reply)
                st.caption(f"model: {used_model}")
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.session_state.last_activity = time.time()
            except Exception as e:
                st.error(f"الخدمة مشغولة حالياً، حاول بعد قليل. / The service is busy, please try again shortly. ({e})")