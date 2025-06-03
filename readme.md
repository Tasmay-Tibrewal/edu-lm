# EDU‑LM: An Agentic Learning Copilot

**Repository:** `tasmay-tibrewal-edu-lm`

---

## Table of Contents

1. [Project Vision](#project-vision)
2. [Current Prototype](#current-prototype)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Architecture](#architecture)
6. [Developer Guide](#developer-guide)
7. [Roadmap & Feature Plan](#roadmap--feature-plan)
8. [Contributing](#contributing)
9. [License](#license)

---

## Project Vision

An open‑source, student‑centric alternative to Google’s **Notebook LM**.
EDU‑LM aims to **teach, visualise, and deep‑dive** into study material rather than merely summarising it.
Key design principles:

* **Depth over surface.** In‑depth podcasts, diagrams, and reasoning chains.
* **Multi‑modal.** Text ▲ images ▲ audio ▲ code ▲ live‑screen context.
* **Agentic.** Tool‑use (search, RAG, TTS, code‑exec, canvas) orchestrated by large‑context models.
* **Extensible.** Plugin‑like architecture so the community can add new agents & UIs.

---

## Current Prototype

This repo contains a **Gradio** proof‑of‑concept that lets you chat with a PDF.

| Capability    | Details                                                      |
| ------------- | ------------------------------------------------------------ |
| **OCR**       | Mistral `mistral-ocr-latest` → Markdown + base64 images      |
| **LLM**       | Gemini 2.5‑Flash (2 M tokens) via OpenAI‑compatible endpoint |
| **Streaming** | Instant user bubble → token‑streamed assistant bubble        |
| **UI**        | Split‑pane Gradio: left = rendered PDF content, right = chat |
| **State**     | Long‑lived chat history stored in memory between turns       |

> **Try it:**
>
> ```bash
> python main.py
> ```

---

## Quick Start

1. **Clone & cd**

   ```bash
   git clone https://github.com/your‑handle/tasmay-tibrewal-edu-lm.git
   cd tasmay-tibrewal-edu-lm
   ```
2. **Create env & install** (Python ≥ 3.10).

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt  # create this file or pip‑install manually
   ```
3. **Set API keys** – place them in a `.env` file or export:

   ```env
   GEMINI_API_KEY=your_google_api_key
   MISTRAL_API_KEY=your_mistral_api_key
   ```
4. **Run.**

   ```bash
   python main.py
   ```
5. **Open** the printed URL, upload a PDF, ask questions.

---

## Configuration

| Variable          | Description                                     | Default      |
| ----------------- | ----------------------------------------------- | ------------ |
| `GEMINI_API_KEY`  | Google AI Studio API key (used via OpenAI shim) | **required** |
| `MISTRAL_API_KEY` | Mistral AI API key (OCR)                        | **required** |
| `ENV_FILE`        | Alternate env‑file name                         | `.env`       |

All other parameters (model names, chunk sizes, max‑tokens…) live at the top of `main.py` for now.

---

## Architecture

```
User ↔️ Gradio UI
   │
   ├─ PDF → Mistral OCR → Markdown + base64 images
   │           │
   │           └─ Stored in memory (current_document_content/text)
   │
   └─ Chat prompt + doc context → Gemini 2.5‑Flash (stream=True)
               │
               └─ Token stream → Gradio chatbot component
```

| Key files | Purpose                                   |
| --------- | ----------------------------------------- |
| `main.py` | Entire prototype (UI, OCR, LLM streaming) |

---

## Developer Guide

* **Stream logic** – two‑step Gradio chain:

  1. `add_user_and_placeholder` → shows the user message instantly.
  2. `stream_assistant_reply` → hides the spinner once first token arrives.
* **OCR helpers** – `get_combined_markdown`, `extract_text_from_ocr_response`.
* **Large‑context prompts** – Keeps full doc (\~2 M tokens) but can be pruned with embedding‑based retrieval in future.
* **State reset** – `clear_chat` wipes in‑memory history.

Feel free to open issues / PRs that refactor this monolithic script into modules.

---

## Roadmap & Feature Plan

The following staged plan converts this prototype into a full **agentic study companion**.

### Phase 0 — Preamble (✅ **you are here**)

* MVP PDF‑chat with OCR + large‑context LLM.



---

## Contributing

1. Fork → feature branch → PR.
2. Raise a GitHub issue, for the idea/bug/improvement you are working on.
3. Send a well documented PR, will check and integrate it, if it seems apt.

Have an idea or find a bug? Open an issue!  We welcome student input.

---

## License

Distributed under the **MIT License**.  See [`LICENSE`](LICENSE) for details.
