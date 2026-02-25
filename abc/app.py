import os
import json
import requests
import streamlit as st
from datetime import datetime
from utils.retrieval import keyword_retrieve
import pytz

st.set_page_config(page_title="KrishiSahay", page_icon="🌾", layout="wide")

CSS = '''
body {background-color: #f7f9fb}
.stApp {
  color-scheme: light;
}
.card {padding:16px;border-radius:12px;background:linear-gradient(180deg, #ffffff, #fcfcff);box-shadow:0 6px 18px rgba(15,23,42,0.08)}
'''

st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

# Function to get weather data
def get_weather():
    try:
        # Using Open-Meteo API (no API key required)
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": 28.7041,
                "longitude": 77.1025,
                "current": "temperature_2m,weather_code,wind_speed_10m",
                "timezone": "Asia/Kolkata"
            },
            timeout=5
        )
        data = response.json()
        if "current" in data:
            return data["current"]
    except:
        return None
    return None

# Sidebar with time, date, and weather
with st.sidebar:
    # Current time and date
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    st.markdown(f"### 🕐 {current_time.strftime('%H:%M:%S')}")
    st.markdown(f"📅 {current_time.strftime('%A, %B %d, %Y')}")
    st.divider()
    
    # Weather section
    st.markdown("### 🌤️ Weather")
    weather = get_weather()
    if weather:
        st.metric("Temperature", f"{weather.get('temperature_2m', 'N/A')}°C")
        st.metric("Wind Speed", f"{weather.get('wind_speed_10m', 'N/A')} km/h")
    else:
        st.info("Weather data unavailable")
    st.divider()
    col1, col2 = st.columns([1,3])
    with col1:
        st.image("https://images.unsplash.com/photo-1501004318641-b39e6451bec6?q=80&w=400&auto=format&fit=crop&ixlib=rb-4.0.3&s=0e9a5b2b8b0b4f4fd3ef4c7f8a7a4cde", width=180)
        st.title("KrishiSahay")
        st.write("Generative AI–Powered Agricultural Query Resolution System")
        st.markdown("---")
        st.sidebar.title("Settings")
        mode = st.sidebar.selectbox("Mode", ["Online (Groq)", "Offline (Local KB)"])
        api_key_input = st.sidebar.text_input("Groq API Key (or set GROQ_API_KEY env)", type="password")
        if api_key_input:
            os.environ["GROQ_API_KEY"] = api_key_input
        st.sidebar.markdown("---")
        st.sidebar.write("Tips:")
        st.sidebar.write("- Use Offline mode when connectivity is low.")
        st.sidebar.write("- Provide short clear queries for best results.")

    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        query = st.text_area("Ask your agricultural question", height=140, placeholder="e.g. How to manage aphids in soybean?\nIn Hindi: सोयाबीन में एफिड्स कैसे नियंत्रित करें?")
        lang = st.selectbox("Language (optional)", ["Auto-detect", "English", "Hindi", "Kannada", "Marathi", "Bengali"])
        
        # Image upload feature
        st.markdown("#### 📸 Upload Image (Optional)")
        uploaded_image = st.file_uploader("Upload an image of your crop or problem", type=["jpg", "jpeg", "png", "gif"])
        if uploaded_image:
            st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
        
        submitted = st.button("Get Answer")
        st.markdown("</div>", unsafe_allow_html=True)

        if submitted and query.strip():
            with st.spinner("Retrieving relevant knowledge..."):
                # simple offline retrieval
                kb_path = os.path.join("data", "knowledge.json")
                try:
                    with open(kb_path, "r", encoding="utf-8") as f:
                        kb = json.load(f)
                except Exception:
                    kb = []

                results = keyword_retrieve(query, kb, top_k=3)

            st.markdown("**Retrieved Knowledge**")
            for r in results:
                st.info(r.get("text",""))

            if mode.startswith("Online"):
                groq_key = os.getenv("GROQ_API_KEY")
                if not groq_key:
                    st.error("No Groq API key found — set in sidebar or as GROQ_API_KEY env variable.")
                else:
                    prompt = """
You are KrishiSahay, an agricultural assistant for farmers. Use retrieved knowledge below as context to answer the user's query concisely and in a farmer-friendly tone.

Context:
%s

User Query:
%s
""" % ("\n\n".join([r.get("text","") for r in results]), query)

                    def groq_generate(prompt_text, api_key, model="llama-3.1-70b-versatile", max_tokens=512, temperature=0.0):
                        url = "https://api.groq.com/openai/v1/chat/completions"
                        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                        payload = {
                            "model": model,
                            "messages": [{"role": "user", "content": prompt_text}],
                            "temperature": temperature,
                            "max_tokens": max_tokens
                        }
                        r = requests.post(url, headers=headers, json=payload, timeout=30)
                        try:
                            j = r.json()
                            if isinstance(j, dict) and "choices" in j and len(j["choices"]) > 0:
                                return j["choices"][0].get("message", {}).get("content", "No response")
                            return r.text
                        except Exception:
                            return r.text

                    with st.spinner("Generating response from Groq model..."):
                        try:
                            answer = groq_generate(prompt, groq_key)
                            st.success("Answer")
                            st.write(answer)
                        except Exception as e:
                            st.error(f"Generation failed: {e}")

            else:
                st.success("Offline Answer (based on local KB)")
                offline_answer = "\n\n".join([r.get("text","") for r in results])
                if offline_answer.strip():
                    st.write(offline_answer)
                else:
                    st.write("No relevant local knowledge found. Try Online mode or expand the KB.")

        st.markdown("---")
        st.markdown("Need more features? Add image upload, SMS gateway, or regional translations.")

if __name__ == '__main__':
    pass
