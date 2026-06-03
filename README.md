# 🎥 AI-Powered YouTube Video-to-Article Generator

<div align="center">
# 🎥 AI-Powered YouTube Video-to-Article Generator
---
  
### 🚀 Transform YouTube Videos into Professional Articles & PDF Reports

Powered by Groq LLaMA 3.3 • Streamlit • YouTube Transcript API • ReportLab

</div>

<!-- Add your project banner image here -->

<img width="1774" height="887" alt="ChatGPT Image Jun 3, 2026, 02_13_46 PM" src="https://github.com/user-attachments/assets/59322aae-3d09-40f1-88f9-3c6fb9484705" />


---


# ✨ Features

- 🎥 YouTube Video Transcript Extraction
- 🤖 AI-Powered Article Generation
- 📝 Multiple Article Writing Styles
- 🎯 Adjustable Tone Control
- ⚙️ Adjustable Technical Depth
- 🌍 Multi-Language Article Generation
- ⏱️ Reading Time Estimation
- 📊 Article Analytics Dashboard
- 🖼️ Video Thumbnail Preview
- 🕒 Recent Video History Tracking
- 📄 Transcript Viewer
- 📑 PDF Report Generation
- ⬇️ Downloadable PDF Export
- 🎨 Professional Streamlit Dashboard
- 🚀 Groq LLaMA 3.3 Integration
- 📱 Modern Responsive UI


---

# 🧠 Tech Stack

| Technology             | Purpose                |
| ---------------------- | ---------------------- |
| Streamlit              | Frontend UI            |
| Python                 | Backend Logic          |
| Groq API               | LLM Inference          |
| LLaMA 3.3              | Article Generation     |
| youtube-transcript-api | Transcript Extraction  |
| yt-dlp                 | Transcript Fallback    |
| ReportLab              | PDF Generation         |
| Requests               | YouTube Metadata       |
| Python Dotenv          | Environment Management |

---

# 🏗️ Architecture

```text
YouTube URL
      ↓
Video Validation
      ↓
Transcript Extraction
(youtube-transcript-api / yt-dlp)
      ↓
Transcript Processing
      ↓
Groq LLaMA 3.3
      ↓
Article Generation
      ↓
Language Translation
      ↓
PDF Generation
      ↓
Downloadable Report
```

---

# 📂 Project Structure

```bash
youtube-video-to-article-generator/
│
├── app.py
│
├── utils/
│   ├── transcript.py
│   ├── article_generator.py
│   └── pdf_generator.py
│
├── assets/
│   ├── banner.png
│   ├── dashboard.png
│   ├── article_output.png
│   └── pdf_export.png
│
├── .env.example
├── requirements.txt
├── README.md
└── .gitignore
```

---
# 📸 Screenshots

## Dashboard

<img width="876" height="616" alt="image" src="https://github.com/user-attachments/assets/f2c91d43-93f8-4e5f-9b02-dfeafb2a6257" />
<img width="844" height="504" alt="image" src="https://github.com/user-attachments/assets/51e8a76f-e326-4479-9cc3-089163942ae6" />


## Video Preview

<img width="921" height="326" alt="image" src="https://github.com/user-attachments/assets/ea32a4c2-5b2f-4765-bfb7-f3b997a60918" />


## Generated Article

<img width="841" height="782" alt="image" src="https://github.com/user-attachments/assets/15a80602-354c-4f18-aadb-702d7b502555" />


## PDF Download

<img width="595" height="638" alt="image" src="https://github.com/user-attachments/assets/0297c7b8-0335-44a9-a398-9b39f4475e4e" />


---

# Visual Overview and Cheetsheet

<img width="715" height="782" alt="image" src="https://github.com/user-attachments/assets/299236e5-8c0e-45b9-9699-3ddfed243b45" />



# ⚡ Installation

## 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/youtube-video-to-article-generator.git
```

```bash
cd youtube-video-to-article-generator
```

---

## 2️⃣ Create Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Mac/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Setup Groq API Key

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Get your API key from:

👉 https://console.groq.com/

---

# ▶️ Run Application

```bash
streamlit run app.py
```

---

# 🎛️ Supported Generation Options

## 📝 Article Styles

* Informative Blog
* Technical Deep Dive
* Beginner Friendly
* News Summary

---

## 🎯 Tone Levels

* Very Casual
* Casual
* Balanced
* Professional
* Formal

---

## ⚙️ Technical Depth

* Beginner
* Easy Read
* Intermediate
* Advanced
* Expert

---

## 📏 Article Length

* Short (~300 Words)
* Medium (~600 Words)
* Long (~1000 Words)

---

# 📊 Analytics Features

### Generated Article Metrics

✅ Word Count

✅ Reading Time Estimation

✅ Compression Ratio Analysis

✅ Transcript-to-Article Transformation Statistics

---

# 🔍 Processing Pipeline

## 📌 Transcript Extraction

Uses:

```python
youtube-transcript-api
```

Fallback:

```python
yt-dlp
```

Provides better reliability for videos where transcript retrieval fails.

---

## 📌 Video Preview

Uses:

```python
YouTube oEmbed API
```

Displays:

* Video Thumbnail
* Video Title
* Channel Information

---

## 📌 AI Content Generation

Uses:

```python
Groq LLaMA 3.3
```

Generates:

* Structured Articles
* Professional Summaries
* Multi-Language Content
* PDF Ready Reports

---

# 💬 Example Use Cases

### Generate Articles From:

* AI & Machine Learning Tutorials
* Technical Conference Talks
* Educational Lectures
* Programming Tutorials
* Product Reviews
* Business Podcasts
* Research Discussions
* News Videos

---

# 📄 PDF Export

Generated PDFs include:

✅ Complete Article

✅ Structured Formatting

✅ Summary Section

✅ Download Ready Report

---



---

# 📦 Requirements

```txt
streamlit
groq
youtube-transcript-api
yt-dlp
reportlab
python-dotenv
requests
```

---

# 🚀 Future Improvements

* DOCX Export
* Markdown Export
* SEO Score Analysis
* Keyword Extraction
* AI Generated Blog Images
* Cloud Deployment
* User Authentication
* Content History Database
* Article Templates
* RAG-Based Knowledge Enhancement

---

# 👨‍💻 Author

### Pavan Ahire

AI/ML Engineer • Generative AI Developer • Data Analyst

---

# ⭐ If You Like This Project

Give this repository a ⭐ on GitHub.

---


> 🚀 Built to demonstrate Generative AI, Large Language Models (LLMs), Prompt Engineering, Transcript Processing, Content Automation, and Production-Ready Streamlit Development.
