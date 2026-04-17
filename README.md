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
