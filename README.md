# 🚀 AI Resume Gen

**ResumeGen** is an intelligent, AI-powered platform that helps you build ATS-friendly resumes and personalized cover letters in minutes. Leveraging Google's **Gemini 2.0 Flash** model, it chats with you to extract your profile details, grades your resume, and generates professional PDFs.

---

## ✨ Features

- **🤖 AI Interviewer**: An interactive chatbot that interviews you to gather your skills, experience, and projects.
- **📄 Instant Resume Generation**: Creates professional, formatted resumes (PDF) from your chat history.
- **📝 Smart Cover Letters**: Auto-generates personalized cover letters matching your profile to specific job descriptions.
- **🎯 ATS Score & Feedback**: Analyzes your resume against job descriptions to give a match score and improvement tips.
- **🎨 Premium Templates**: Choose from "Modern Clean" and "Minimal Elegant" designs.
- **🔄 API Key Rotation**: Built-in system to handle high traffic by rotating multiple Gemini API keys.
- **📧 Email Integration**: Automatically emails your generated resume to you.

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.10+**
- **Git**

---

## 📥 Installation

Follow these steps to set up the project on any new device:

### 1. Clone the Repository
```bash
git clone https://github.com/Parth8828/ResumeGen.git
cd ResumeGen
```

### 2. Create a Virtual Environment
It's recommended to use a virtual environment to manage dependencies.
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔑 Configuration (Important!)

You must create a `.env` file in the root directory to store your secret keys. 
**Do not skip this step.**

1.  Create a file named `.env` in the project root.
2.  Copy the format below and fill in your details:

```ini
# .env file

# 1. Google Gemini API Keys (Comma-separated list for rotation)
# Get keys here: https://aistudio.google.com/app/apikey
GEMINI_API_KEYS=key1,key2,key3...

# 2. Google Gemini Model Name
GEMINI_MODEL_NAME=gemini-2.0-flash-exp

# 3. Email Configuration (For sending resumes)
# Use a Gmail App Password, NOT your regular password.
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your.email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
```

### 🛡️ How to get these keys?

#### **1. Google AI Studio Keys**
*   Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
*   Click **"Create API Key"**.
*   It is recommended to generate **3-5 keys** using different Google Cloud projects if you plan to use the app heavily, to avoid rate limits.
*   Paste them into `.env` separated by commas (no spaces).

#### **2. Gmail App Password (SMTP)**
*   Go to your [Google Account Security](https://myaccount.google.com/security) settings.
*   Enable **2-Step Verification** if it's not on.
*   Go to the search bar at the top and search for **"App passwords"**.
*   Create a new app password (name it "ResumeGen").
*   Copy the 16-character code (spaces don't matter) and paste it into `SMTP_PASSWORD`.

---

## 🚀 Running the App

Once setup is complete, run the application:

```bash
uvicorn app.main:app --reload --port 8000
```

> The app will run at: **http://127.0.0.1:8000** (or port 8002 if 8000 is busy)

---

## �️ Database

By default, the app uses **SQLite** for zero-configuration storage.
*   **File Location**: `./resume_gen.db` (Created automatically on first run)
*   **Data Migration**: If you move this project to another computer, you can copy the `resume_gen.db` file to the new directory to keep your user accounts and resume history.
*   **Reset**: To factory reset the app, simply delete the `resume_gen.db` file and restart the server.

---

## �📖 Usage Guide

1.  **Sign Up/Login**: Create an account to save your data.
2.  **Chat with AI**: Go to the **Chat** tab. The AI will ask you questions. Answer them to build your profile.
3.  **View Profile**: Check the **Profile** tab to see your structured data (Skills, Experience, etc.). You can manually edit any errors here.
4.  **Generate Resume**: On the Profile page, click **"Generate Resume"**. Select a template and download.
5.  **Cover Letter**: Go to **Cover Letter**. Paste a Job Description. Use the "Get Suggestions" button to auto-fill role details, then click Generate.

---

## 📁 Project Structure

```
ResumeGen/
├── app/
│   ├── api/            # Backend endpoints (Chat, Profile, Resume, CoverLetter)
│   ├── core/           # Config and Security
│   ├── db/             # Database models and session
│   ├── services/       # AI logic (Gemini), PDF generation
│   ├── templates/      # Frontend HTML templates (Jinja2)
│   └── main.py         # Entry point
├── .env                # Secrets (Excluded from Git)
├── .gitignore          # Git exclusion rules
├── requirements.txt    # Python dependencies
└── README.md           # Documentation
```

---

## 🤝 Contributing

Feel free to fork this repository and submit Pull Requests!
For major changes, please open an issue first to discuss what you would like to change.

## 📄 License
[MIT](https://choosealicense.com/licenses/mit/)
