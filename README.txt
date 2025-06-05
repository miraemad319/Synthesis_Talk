# SynthesisTalk

**Collaborative Research Assistant**  
**Course**: CSAI 422: Advanced Topics in Generative AI  

---

## Table of Contents

1. [Overview](#overview)  
2. [Features](#features)  
   - [Contextual Research Conversation](#contextual-research-conversation)  
   - [Intelligent Synthesis Engine](#intelligent-synthesis-engine)  
   - [Flexible Output Generation](#flexible-output-generation)  
   - [Tool-Enhanced Experience](#tool-enhanced-experience)  
3. [Technical Stack](#technical-stack)  
   - [Backend](#backend)  
   - [Frontend](#frontend)  
   - [LLM Integration](#llm-integration)  
4. [Project Structure](#project-structure)  
5. [Installation & Running](#installation--running)  
   - [Prerequisites](#prerequisites)  
   - [Backend Setup](#backend-setup)  
   - [Frontend Setup](#frontend-setup)  
6. [Environment Variables](#environment-variables)  
7. [How to Use](#how-to-use)  
   - [Uploading Documents](#uploading-documents)  
   - [Chat Interface](#chat-interface)  
   - [Visualizations](#visualizations)  
   - [Insights & Search](#insights--search)  
   - [Context Management](#context-management)  
   - [Exporting Data](#exporting-data)  
8. [Limitations](#limitations)  
9. [Future Improvements](#future-improvements)  
10. [Acknowledgments](#acknowledgments)  

---

## Overview

SynthesisTalk is an intelligent, LLM-powered research assistant designed to help users explore complex topics through an interactive conversational interface. Users can upload documents (PDF/TXT/DOCX), perform web searches, maintain context across multiple sources, and generate structured summaries, visualizations, and exports. The system showcases:

- **Multi-turn, context-aware chat**  
- **Document processing pipeline with chunking & indexing**  
- **LLM tool orchestration including self-correction**  
- **Advanced reasoning (ReAct / Chain-of-Thought) if enabled**  
- **Visualization endpoints for keyword frequency, source distribution, conversation flow, topic analysis, and timeline**  

---

## Features

### Contextual Research Conversation

- **Session Management**  
  - Centralized session store (`session_store.py`) keeps conversation history, context IDs, and document references.  
  - Sessions persist across server restarts (via `persistence.py`).

- **Multi-context Organization**  
  - Users can create, switch, update, and delete “contexts” (research topics).  
  - Each context has its own document set and chat history.  

- **Document Upload & Chunking**  
  - Upload PDF, TXT, or DOCX files.  
  - Text is extracted (via `file_extraction.py`) and split into ≤ 3,000-character chunks (`chunking.py`).  
  - Chunks stored under `document_store[session_id]` and associated with the current context.  

### Intelligent Synthesis Engine

- **LLM Tool Orchestration**  
  - `react_with_llm()` in `backend/llm.py` routes calls to primary (NGU) or fallback (GROQ) services.  
  - Supports advanced reasoning patterns (ReAct or Chain-of-Thought) when `use_reasoning=True
