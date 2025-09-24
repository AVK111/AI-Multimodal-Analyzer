import streamlit as st
import os
import tempfile
import subprocess
import cv2
import speech_recognition as sr
import google.generativeai as genai
from langchain_community.tools import DuckDuckGoSearchRun
from dotenv import load_dotenv

# =============================
# Setup
# =============================
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash-exp')
search_tool = DuckDuckGoSearchRun()

st.set_page_config(page_title="AI Multimodal Analyzer", layout="wide")
st.title("AI Multimodal Analyzer")
st.markdown("Advanced multimedia analysis with semantic vector storage and knowledge base")

# Session state to store past analyses
if "past_analyses" not in st.session_state:
    st.session_state.past_analyses = []

# =============================
# Helper Functions
# =============================

def save_temp_file(uploaded_file):
    if uploaded_file:
        suffix = f".{uploaded_file.name.split('.')[-1]}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getbuffer())
            return tmp.name
    return None

def extract_thumbnail(video_path):
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    if ret:
        thumb_path = video_path + "_thumb.jpg"
        cv2.imwrite(thumb_path, frame)
        return thumb_path
    return None

def transcribe_audio(video_path):
    audio_path = video_path + "_audio.wav"
    subprocess.run(
        ['ffmpeg', '-i', video_path, '-q:a', '0', '-map', 'a', audio_path, '-y'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    recognizer = sr.Recognizer()
    transcription = ""
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
            transcription = recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        transcription = "Could not understand audio"
    except sr.RequestError as e:
        transcription = f"Could not request results; {e}"
    except Exception as e:
        transcription = f"Transcribe Failed {e}"
    os.remove(audio_path)
    return transcription

def analyze_content(prompt, image_path=None, transcription=None):
    content = prompt
    if transcription:
        content += f"\n\nTranscription: {transcription}"

    try:
        if image_path:
            with open(image_path, "rb") as img:
                response = model.generate_content(
                    [content, {"mime_type": "image/jpeg", "data": img.read()}]
                )
        else:
            response = model.generate_content(content)

        return response.text
    except Exception as e:
        return f"Analysis Failed: {e}"

def perform_web_search(query):
    results = search_tool.run(query)
    prompt = f"Web Search results for '{query}': \n {results}\n\n Provide a comprehensive analysis."
    return analyze_content(prompt)

# =============================
# Sidebar Navigation
# =============================
st.sidebar.title("Navigate")
page = st.sidebar.radio("Go to", ["New Analysis", "Past Analyses", "Knowledge Base Search"])

# =============================
# Pages
# =============================

# ---- New Analysis ----
if page == "New Analysis":
    analysis_type = st.selectbox("Choose analysis type:", ["Image", "Video", "Web Search"])

    if analysis_type == "Image":
        image_file = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])
        if st.button("Analyze Image") and image_file:
            image_path = save_temp_file(image_file)
            st.image(image_path, width=400)
            prompt = "Provide a detailed analysis of the image."
            result = analyze_content(prompt, image_path=image_path)
            st.markdown(result)

            st.session_state.past_analyses.append({
                "type": "Image",
                "file": image_path,
                "result": result
            })

    elif analysis_type == "Video":
        video_file = st.file_uploader("Upload video", type=["mp4", "mov", "avi"])
        if st.button("Analyze Video") and video_file:
            video_path = save_temp_file(video_file)
            thumbnail_path = extract_thumbnail(video_path)
            transcription = transcribe_audio(video_path)

            col1, col2 = st.columns(2)
            with col1:
                if thumbnail_path:
                    st.image(thumbnail_path, caption="Thumbnail", width=350)
            with col2:
                st.markdown("**Transcription:**")
                st.write(transcription)

            prompt = "Analyze this video based on the thumbnail and transcription."
            result = analyze_content(prompt, image_path=thumbnail_path, transcription=transcription)
            st.markdown(result)

            st.session_state.past_analyses.append({
                "type": "Video",
                "file": thumbnail_path,
                "transcription": transcription,
                "result": result
            })

    elif analysis_type == "Web Search":
        query = st.text_input("Enter search query")
        if st.button("Search and Analyze") and query:
            result = perform_web_search(query)
            st.markdown(result)

            st.session_state.past_analyses.append({
                "type": "Web Search",
                "query": query,
                "result": result
            })

# ---- Past Analyses ----
elif page == "Past Analyses":
    st.header("Past Analyses")
    if st.session_state.past_analyses:
        for i, analysis in enumerate(st.session_state.past_analyses):
            st.subheader(f"Analysis {i+1} - {analysis['type']}")
            if "file" in analysis and analysis["file"]:
                if analysis["type"] == "Image":
                    st.image(analysis["file"], width=200)
                elif analysis["type"] == "Video":
                    st.image(analysis["file"], width=200)  # showing thumbnail
            if "transcription" in analysis:
                st.markdown("**Transcription:**")
                st.write(analysis["transcription"])
            if "query" in analysis:
                st.markdown(f"**Query:** {analysis['query']}")
            st.markdown("**Result:**")
            st.write(analysis["result"])
    else:
        st.info("No past analyses yet.")

# ---- Knowledge Base Search ----
elif page == "Knowledge Base Search":
    st.header("Knowledge Base Search")
    query = st.text_input("Ask a question about past analyses")

    if st.button("Search") and query:
        combined_results = "\n\n".join(
            [f"{a['type']}:\n{a['result']}" for a in st.session_state.past_analyses]
        )
        if combined_results.strip():
            prompt = f"User query: {query}\n\nRelevant past analyses:\n{combined_results}\n\nAnswer based on the above context:"
            answer = analyze_content(prompt)
            st.markdown(answer)
        else:
            st.warning("No past analyses available for knowledge search.")

st.markdown ("---")
st.markdown("Developed by Atharv Kale")
st.markdown("INSTRUCTIONS:")
st.markdown("1. Select the type of analysis you want ")