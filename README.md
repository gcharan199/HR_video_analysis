# HR Video Analysis Tool 🎥🧠

This is an interactive Streamlit web application that analyzes video-recorded or uploaded job interviews using Gemini AI. It transcribes, evaluates, and generates a professional PDF report with structured HR feedback based on predefined rubric metrics.

---

## ✨ Features

- 📹 **Record or Upload Interviews** using webcam or file upload
- 🧠 **Gemini AI Evaluation** based on 8 HR rubric metrics:
  - Communication Clarity
  - Confidence & Body Language
  - Technical Knowledge
  - Problem-Solving Ability
  - Professionalism & Attitude
  - Teamwork & Collaboration
  - Adaptability
  - Cultural Fit
- 📝 **Concise Feedback** (2-line summaries per metric)
- 🧾 **Detailed Summary** without restrictions
- 📄 **Auto-generated PDF report** with clean formatting and word-wrapped tables
- 💾 **Transcript viewer** and optional JSON export

---

## 🛠 Requirements

- Python 3.10+
- A working webcam and microphone (for recording)
- A valid Google Gemini API key

---

## 🚀 Setup

# Clone the repo
git clone https://github.com/gcharan199/HR_video_analysis.git
cd HR_video_analysis

# Create and activate a virtual environment
python -m venv venv
venv\\Scripts\\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Create a .env file
echo GEMINI_API_KEY=your_api_key_here > .env

# Run the file in the terminal
streamlit run app.py

📄 Output
 - Generates a downloadable PDF report that includes:
 - Tabular scores with feedback
 - Full AI-generated summary
 - Proper layout and paragraph wrapping

🧠 Powered by
 - Google Gemini
 - Streamlit
 - ReportLab



