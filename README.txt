# SynthesisTalk

**Collaborative Research Assistant**  
CSAI 422: Advanced Topics in Generative AI  

---

## Overview

SynthesisTalk is an LLM-powered web application that helps users explore complex research topics through:

- Multi-turn, context-aware chat  
- Document uploads (PDF, TXT, DOCX) with text extraction and chunking  
- Web search integration for fact-finding  
- Automatic summaries and visualizations  
- Exporting conversation history and uploaded documents  

---

## Features

1. **Contextual Research Conversation**  
   - Maintain a session-specific chat history stored in memory and persisted to disk.  
   - Organize research into multiple “contexts” (topics) that each have their own documents and chats.  
   - Upload documents and query their contents alongside web search results.  

2. **Intelligent Synthesis Engine**  
   - Integrates two LLM services (NGU as primary, GROQ as fallback).  
   - Supports advanced reasoning (ReAct or Chain-of-Thought) when enabled.  
   - Self-correction mechanism: LLM reviews and can improve its own longer responses.  

3. **Document Processing**  
   - Extract text from PDF, TXT, or DOCX files.  
   - Split long documents into ≤ 3000-character chunks for efficient processing.  
   - Store chunks per session and context in a simple in-memory map, backed by JSON persistence.  

4. **Visualizations**  
   - **Keywords**: Top‐K keyword frequency across all uploaded chunks.  
   - **Sources**: Distribution of chunks per source document.  
   - **Conversation Flow**: Timeline of user vs. AI messages with lengths and timestamps.  
   - **Topic Analysis**: LLM-powered topic extraction; falls back to frequency-based if JSON parsing fails.  
   - **Research Timeline**: Chronological events, including document uploads and major user questions.  

5. **Export**  
   - **Conversation Export**: Download full conversation history in TXT, JSON, MD, or CSV format.  
   - **Document Export**: Download all uploaded documents (in text form) as a combined file or ZIP.  

---

## Technology Stack

### Backend

- **Framework**: FastAPI  
- **Language**: Python 3.10+  
- **Server**: Uvicorn  
- **LLM Services**:  
  - NGU (`qwen2.5-coder:7b`) as primary  
  - GROQ (`llama-3.3-70b-versatile`) as fallback  
- **Persistence**: JSON file (`session_data.json`) via `persistence.py`  
- **Routes**:  
  - `/upload/` – file upload & chunking  
  - `/chat/` – chat with context-aware LLM calls  
  - `/search/` – document-only or combined document+web search  
  - `/visualize/` – endpoints for keywords, sources, conversation flow, topic analysis, research timeline  
  - `/insights/` – generate insights in the background (UUID tasks)  
  - `/context/` – list, create, switch, delete, update contexts  
  - `/export/` – download conversation or documents  
- **Utils**:  
  - `file_extraction.py`, `chunking.py`, `summarizer.py`, `concept_linker.py`  
  - `session_store.py` and `persistence.py` manage session data and auto-save on shutdown  

### Frontend

- **Framework**: React (Vite)  
- **Styling**: TailwindCSS  
- **Charts**: Recharts  
- **Key Components**:  
  - `ChatWindow.jsx` – chat interface and message list  
  - `UploadArea.jsx` – drag-and-drop file uploads with progress bar  
  - `ContextSidebar.jsx` – create/switch/delete research contexts  
  - `VisualizationPanel.jsx` – display keyword/source/timeline charts  
  - `InsightsPanel.jsx` – poll background tasks for AI-generated insights  
  - `SearchPanel.jsx` – debounced search input for document/web search  
  - `ExportPanel.jsx` – buttons for downloading conversation/documents  
  - `LoadingIndicator.jsx` – global spinner overlay for in-flight API calls  
  - `MessageBubble.jsx` – renders each chat message with optional typewriter effect  
- **Custom Hooks**:  
  - `useChat.js` – manages messages array, session cookie, and API calls  
  - `useTypewriter.js` – animates assistant’s response text  

---

## Getting Started

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd Synthesis_Talk

Backend Setup
Create and activate a Python virtual environment:

bash
Copy
Edit
python -m venv venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate
Install Python dependencies:

bash
Copy
Edit
pip install -r backend/requirements.txt
Create or edit backend/.env with your API keys:

ini
Copy
Edit
NGU_API_KEY="your-ngu-key"
NGU_BASE_URL="https://ngullama.femtoid.com/v1"
NGU_MODEL="qwen2.5-coder:7b"

GROQ_API_KEY="your-groq-key"
GROQ_BASE_URL="https://api.groq.com/openai/v1"
GROQ_MODEL="llama-3.3-70b-versatile"

MODEL_SERVER="NGU"
Start the FastAPI server (from project root):

bash
Copy
Edit
python -m uvicorn backend.main:app --reload
You should see logs indicating that each router was registered successfully and that Uvicorn is running at http://127.0.0.1:8000.

3. Frontend Setup
Open a new terminal window/tab and change directory to frontend/:

bash
Copy
Edit
cd frontend
Install Node packages:

bash
Copy
Edit
npm install
If not already set, create or edit frontend/.env.development with:

ini
Copy
Edit
VITE_API_URL="http://localhost:8000"
NODE_ENV="development"
Start the Vite dev server:

bash
Copy
Edit
npm run dev
The React app should now be available at http://localhost:5173.

Usage
Open http://localhost:5173 in your browser.

Upload a PDF/TXT/DOCX file via the Upload Area at the top.

Chat with the AI – ask questions about uploaded documents or general research topics.

View Visualizations by selecting the “Charts” tab on the right (desktop) or bottom sheet (mobile).

Generate Insights in the Insights panel (runs a background task, then displays results).

Manage Contexts: Use the sidebar to create, switch, rename, or delete research contexts.

Export conversation history or all uploaded documents from the Export panel.

Environment Variables
NGU_API_KEY: Your NGU LLM API key

NGU_BASE_URL: NGU API base URL

NGU_MODEL: NGU model identifier

GROQ_API_KEY: Your GROQ LLM API key

GROQ_BASE_URL: GROQ API base URL

GROQ_MODEL: GROQ model identifier

MODEL_SERVER: Which LLM to prioritize (NGU or GROQ)

VITE_API_URL: Frontend’s base URL for API calls (http://localhost:8000)

NODE_ENV: Should be development for local builds

Limitations
Summarization and topic-analysis are limited to the first 3,000 characters per document chunk.

No user authentication or multi‐user separation—every session is identified by a cookie.

No rate limiting or pagination; very long sessions can cause timeouts.

Contexts and session data persist only via a JSON file (session_data.json)—no database cleanup.

Future Improvements
Add “/define” or “/compare” tools for quick definitions and document comparisons.

Export documents in PDF or Markdown formats.

Add a long‐term memory store (e.g., SQLite or Redis) for cross‐session persistence.

Implement user authentication and role-based access.

Implement pagination and rate limiting for large conversations.

Add interactive word clouds or network graphs for topic analysis.

Acknowledgments
FastAPI & Uvicorn for the backend framework and ASGI server

React (Vite) & TailwindCSS for the frontend

Recharts for data visualization

NGU and GROQ for LLM services
