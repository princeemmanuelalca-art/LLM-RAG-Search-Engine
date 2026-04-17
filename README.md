# Archon — The Intellectual Architect 

> A RAG-powered intelligent document assistant built for the CortexX Hackathon 2026.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-HuggingFace-yellow)](https://Prince-Alca-Archon.hf.space)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Features

-Upload PDFs, TXTs, or paste raw text as a knowledge base
-Semantic search via ChromaDB + sentence-transformers
-LLM answers powered by Groq (`llama-3.1-8b-instant`)
-Multi-session conversation memory
-"The Intellectual Architect" Material Design UI

---

## Quick Start (Local)

```bash
git clone https://github.com/Prince-Alca/Archon.git
cd Archon
cp .env.example .env
# Fill in your GROQ_API_KEY in .env
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:7860`.

---

## Deployment

Deployed on **HuggingFace Spaces** using Docker.  
Set your `GROQ_API_KEY` in Space → Settings → Secrets.

---

## Project Structure
Archon/
├── app.py                  # Flask entry point
├── rag_system.py           # RAG core (ChromaDB + LLM)
├── templates/index.html    # Full frontend UI
├── utils/
│   ├── config.py           # LLM provider config
│   └── llm_interface.py    # Groq API handler
├── requirements.txt
├── Dockerfile
└── .env.example

---

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask (Python) |
| LLM | Groq — `llama-3.1-8b-instant` |
| Vector DB | ChromaDB |
| Embeddings | sentence-transformers |
| Hosting | HuggingFace Spaces (Docker) |

---

## License

MIT — see [LICENSE](LICENSE).
