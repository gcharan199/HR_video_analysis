import os
import json
import re
import subprocess
import streamlit as st
import requests
import speech_recognition as sr
from dotenv import load_dotenv
from io import BytesIO
from textwrap import wrap
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from aiortc.contrib.media import MediaRecorder
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


# Load API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("GEMINI_API_KEY not found in .env file.")
    st.stop()

st.set_page_config(page_title="HR Interview Analyzer", layout="centered")
st.title("🎥 HR Interview Analyzer (Gemini 2.0 Flash)")

video_path = "input_video.mp4"
if "video_uploaded" not in st.session_state:
    st.session_state.video_uploaded = False
    if os.path.exists(video_path):
        os.remove(video_path)

# Step 1: Upload or Record
mode = st.radio("Video Input Method", ["Upload", "Record"])
if mode == "Upload":
    video_file = st.file_uploader("Upload your interview video", type=["mp4", "mov"])
    if video_file:
        with open(video_path, "wb") as f:
            f.write(video_file.read())
        st.session_state.video_uploaded = True
        st.video(video_path)
        st.success("✅ Video uploaded.")
elif mode == "Record":
    def recorder_factory():
        return MediaRecorder(video_path, format="mp4")
    webrtc_ctx = webrtc_streamer(
        key="recorder",
        mode=WebRtcMode.SENDONLY,
        media_stream_constraints={"video": True, "audio": True},
        in_recorder_factory=recorder_factory,
    )
    if webrtc_ctx.state.playing:
        st.info("⏺️ Recording...")
    elif os.path.exists(video_path):
        st.session_state.video_uploaded = True
        st.success("✅ Recording complete.")
        st.video(video_path)

# Step 2: Transcription
st.subheader("🔊 Step 2: Transcription")
if st.session_state.video_uploaded and os.path.exists(video_path) and os.path.getsize(video_path) > 1000:
    audio_path = "audio.wav"
    subprocess.run(["ffmpeg", "-y", "-i", video_path, "-ac", "1", "-ar", "16000", audio_path],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        transcript_text = recognizer.recognize_google(audio_data)
        st.text_area("Transcript", transcript_text, height=200)
else:
    st.info("⏳ Waiting for video to be uploaded or recorded...")
    transcript_text = ""

# Step 3: Gemini Evaluation
if transcript_text:
    st.subheader("🧠 Step 3: Gemini HR Evaluation")

    prompt = (
        "You are an HR expert evaluating a candidate's job interview.\n"
        "Rate their performance from 1 (poor) to 5 (excellent) based on the following criteria:\n\n"
        "- Communication Clarity\n"
        "- Confidence & Body Language\n"
        "- Technical Knowledge\n"
        "- Problem-Solving Ability\n"
        "- Professionalism & Attitude\n"
        "- Teamwork & Collaboration\n"
        "- Adaptability\n"
        "- Cultural Fit\n\n"
        f'Transcript:\n"""{transcript_text}"""\n\n'
        "Respond in this JSON format. Keep each metric's feedback concise (upto than 2 lines), but keep the full Summary detailed.\n"
        "{\n"
        '  "Communication Clarity": {"score": 1-5, "feedback": "..."},\n'
        '  "Confidence & Body Language": {"score": 1-5, "feedback": "..."},\n'
        '  "Technical Knowledge": {"score": 1-5, "feedback": "..."},\n'
        '  "Problem-Solving Ability": {"score": 1-5, "feedback": "..."},\n'
        '  "Professionalism & Attitude": {"score": 1-5, "feedback": "..."},\n'
        '  "Teamwork & Collaboration": {"score": 1-5, "feedback": "..."},\n'
        '  "Adaptability": {"score": 1-5, "feedback": "..."},\n'
        '  "Cultural Fit": {"score": 1-5, "feedback": "..."},\n'
        '  "Summary": "..." \n'
        "}"
    )

    if "analysis" not in st.session_state:
        with st.spinner("Analyzing with Gemini..."):
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            body = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url, headers=headers, json=body)
            raw = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r'^[^{]*({.*?})[^}]*$', r'\1', cleaned, flags=re.DOTALL)

            try:
                st.session_state.analysis = json.loads(cleaned)
            except json.JSONDecodeError:
                st.error("⚠️ Gemini response was not valid JSON.")
                fallback = BytesIO()
                fallback.write(raw.encode("utf-8"))
                fallback.seek(0)
                st.download_button("⬇️ Download Gemini Response (.json)", data=fallback, file_name="gemini_response.json", mime="application/json")
                st.stop()

    analysis = st.session_state.analysis

    st.subheader("📊 Evaluation")
    for key, val in analysis.items():
        if key != "Summary":
            st.markdown(f"**{key} (Score: {val['score']}/5)**\n- _{val['feedback']}_")

    st.subheader("📋 Summary")
    st.write(analysis.get("Summary", "No summary provided."))

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("HR Interview Evaluation Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Evaluation Scores:", styles["Heading2"]))
    score_data = [[
        Paragraph("Criterion", styles["Heading4"]),
        Paragraph("Score", styles["Heading4"]),
        Paragraph("Feedback", styles["Heading4"])
    ]]
    for key, val in analysis.items():
        if key != "Summary":
            score_data.append([
                Paragraph(key, styles["BodyText"]),
                Paragraph(f"{val['score']}/5", styles["BodyText"]),
                Paragraph(val["feedback"], styles["BodyText"])
            ])

    table = Table(score_data, colWidths=[150, 50, 320])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (1, 1), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 24))

    elements.append(Paragraph("Summary:", styles["Heading2"]))
    elements.append(Paragraph(analysis.get("Summary", ""), styles["BodyText"]))

    doc.build(elements)
    pdf_buffer.seek(0)

    st.download_button(
        label="📄 Download PDF Report",
        data=pdf_buffer,
        file_name="interview_report.pdf",
        mime="application/pdf"
    )