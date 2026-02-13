# 🤖 AI Support Ticket Agent

An AI-powered support automation system that analyzes customer tickets, retrieves relevant documentation using RAG (Retrieval-Augmented Generation), generates professional responses, and routes issues intelligently — all running locally with Ollama.

---

## 🚀 Overview

AI Support Ticket Agent simulates a real-world support workflow.

The system:

- Classifies incoming support tickets  
- Detects urgency level  
- Retrieves relevant knowledge base content  
- Generates a professional customer response  
- Evaluates confidence and grounding  
- Applies escalation rules automatically  
- Logs all tickets for record keeping  
- Returns structured output ready for automation tools (e.g., n8n)  

Everything runs locally using open-source models.

---

## 🏗 Key Features

- AI-powered ticket classification  
- Priority detection  
- RAG-based document retrieval (FAISS)  
- Professional response generation  
- Confidence scoring (1–10)  
- Hallucination guard (grounded check)  
- Automatic escalation logic  
- SQLite ticket logging  
- FastAPI backend  
- Streamlit frontend  
- Automation-ready API  

---

## 📁 Project Structure

```
ai-support-agent/
│
├── app/                # Backend logic
│   ├── main.py
│   ├── agent.py
│   ├── classifier.py
│   ├── sentiment.py
│   ├── retriever.py
│   ├── responder.py
│   ├── router.py
│   ├── config.py
│   └── database.py
│
├── data/               # Knowledge base + FAISS index
├── ui/                 # Streamlit frontend
├── support_logs.db     # Ticket records (auto-created)
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

### 1️⃣ Clone Repository

```bash
git clone https://github.com/AniketDeshpande-23/ai-support-agent.git
cd ai-support-agent
```

---

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

Activate:

**Windows**
```bash
venv\Scripts\activate
```

**Mac/Linux**
```bash
source venv/bin/activate
```

---

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Install Ollama

Download and install from:

https://ollama.com

Pull required models:

```bash
ollama pull mistral
ollama pull nomic-embed-text
```

---

## ▶️ Running the Application

### Start Backend

```bash
uvicorn app.main:app --reload
```

Backend runs at:

```
http://localhost:8000
```

---

### Start Frontend

Open a new terminal:

```bash
streamlit run ui/app.py
```

---

## 🧠 How to Use

1. Open the Streamlit interface.
2. Enter a customer support ticket in the text area.
3. Click **Analyze**.
4. The system will display:

   - Category  
   - Priority  
   - Confidence Score  
   - Escalation Route  
   - Final Customer Response  

All tickets are automatically recorded in the local database.

---

## 🔄 Automation Ready

The backend returns structured JSON like:

```json
{
  "category": "Login Issue",
  "priority": "Medium",
  "confidence": 8,
  "grounded": true,
  "route_to": "General Support",
  "reply_draft": "Hi, please reset your password using the Forgot Password link..."
}
```

This makes it easy to integrate with:

- n8n  
- Slack  
- Email workflows  
- CRM systems  
- Helpdesk platforms  

You can automate routing or escalation based on confidence and priority.

---

## 📊 Ticket Logging

Every processed ticket is stored in:

```
support_logs.db
```

Each record includes:

- Timestamp  
- Ticket text  
- Category  
- Priority  
- Confidence score  
- Grounded status  
- Escalation route  
- Final AI response  

This enables auditing and future analytics integration.

---

## 🛠 Future Improvements

- Admin dashboard for reviewing tickets  
- Multi-turn conversation support  
- Docker deployment  
- Cloud hosting  
- Authentication layer  

---

## 💡 Why This Project

This project demonstrates:

- Practical RAG implementation  
- AI safety mechanisms  
- Escalation logic design  
- Automation-ready backend architecture  
- Real-world AI system structuring  

It is designed to simulate a structured support automation workflow rather than a simple chatbot.
