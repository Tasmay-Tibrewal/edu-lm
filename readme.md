# Multi-Document PDF Chat Assistant

**An advanced AI-powered document analysis and conversational interface**

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Usage Guide](#usage-guide)
6. [Architecture](#architecture)
7. [API Integration](#api-integration)
8. [File Structure](#file-structure)
9. [Troubleshooting](#troubleshooting)
10. [Contributing](#contributing)
11. [License](#license)

---

## Overview

This application is a sophisticated multi-document PDF chat assistant that combines advanced OCR, AI language models, and audio processing capabilities. Built with Gradio, it provides an intuitive interface for uploading, processing, and conversing with multiple PDF documents simultaneously.

### Key Capabilities

- **Multi-document support**: Upload and manage multiple PDF files simultaneously
- **Advanced OCR**: Extract text and images from PDFs using Mistral's OCR service
- **AI-powered chat**: Conversation with document content using Gemini 2.5 Flash
- **Voice interaction**: Speech-to-text input and text-to-speech output
- **Real-time streaming**: Token-by-token response streaming for immediate feedback
- **Persistent state**: Maintains chat history and document context across sessions
- **Visual document preview**: Side-by-side document viewer with chat interface

---

## Features

### 🗂️ Document Management
- **Multi-file upload**: Support for multiple PDF files with drag-and-drop
- **Smart document tracking**: Chronological order preservation and position tracking
- **Dynamic file management**: Add/remove documents without losing chat history
- **Visual content preview**: Expandable document viewer with formatted content
- **OCR with image preservation**: Extract text while maintaining embedded images

### 💬 Conversational AI
- **Context-aware responses**: AI understands all uploaded documents simultaneously
- **Streaming responses**: Real-time token-by-token response generation
- **Persistent chat history**: Maintains conversation context across sessions
- **Smart prompting**: Optimized message structure for multi-document queries

### 🎤 Audio Features
- **Speech-to-text**: Voice input using Groq's Whisper-large-v3 model
- **Text-to-speech**: AI response audio using OpenAI's TTS models
- **Real-time transcription**: Instant audio processing and text insertion
- **Configurable voices**: Multiple voice options for audio output

### 💾 Data Persistence
- **JSON exports**: Automatic saving of chat history and LLM payloads
- **Session management**: State preservation across application restarts
- **Debug capabilities**: Detailed logging and payload inspection

---

## Quick Start

### Prerequisites
- Python 3.8 or higher
- API keys for required services (see [Configuration](#configuration))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. **Install dependencies**
   ```bash
   pip install gradio python-dotenv mistralai google-generativeai openai markdown pathlib IPython
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_google_api_key_here
   MISTRAL_API_KEY=your_mistral_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Access the interface**
   Open your browser and navigate to the URL displayed in the terminal (typically `http://localhost:7860`)

---

## Configuration

### Required API Keys

| Service | Purpose | Environment Variable |
|---------|---------|---------------------|
| **Google Gemini** | Primary LLM for chat responses | `GEMINI_API_KEY` |
| **Mistral AI** | OCR processing for PDF documents | `MISTRAL_API_KEY` |
| **Groq** | Speech-to-text (Whisper model) | `GROQ_API_KEY` |
| **OpenAI** | Text-to-speech generation | `OPENAI_API_KEY` |

### Optional Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ENV_FILE` | Alternative environment file path | `.env` |

### Model Configuration

The application uses the following models (configurable in `main.py`):

- **LLM**: `gemini-2.5-flash-preview-05-20` (via OpenAI-compatible endpoint)
- **OCR**: `mistral-ocr-latest`
- **ASR**: `whisper-large-v3` (Groq)
- **TTS**: `gpt-4o-mini-tts` (OpenAI)

---

## Usage Guide

### Uploading Documents

1. **Single or Multiple Files**: Use the file upload area to select one or more PDF files
2. **Drag and Drop**: Drag PDF files directly onto the upload area
3. **Document Management**: Files can be added or removed dynamically
4. **Preview Content**: Expand document sections to view full content with images

### Chatting with Documents

1. **Text Input**: Type questions in the text box and press Enter or click Send
2. **Voice Input**: Click the microphone button to record voice questions
3. **Context Awareness**: The AI has access to all uploaded document content
4. **Streaming Responses**: Watch responses appear in real-time

### Audio Features

1. **Voice Questions**: Record audio that gets automatically transcribed
2. **Listen to Responses**: Click "🔊 Listen to Last Response" for audio playback
3. **Auto-play**: Audio responses play automatically when generated

### Document Viewing

1. **Side Panel**: View all uploaded documents in the left panel
2. **Expandable Content**: Click "View Full Content" to see detailed document content
3. **Image Support**: View embedded images from PDF documents
4. **Navigation**: Easily switch between different document sections

---

## Architecture

### System Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Gradio UI     │◄──►│   Application    │◄──►│   External APIs │
│                 │    │     Logic        │    │                 │
│ • File Upload   │    │                  │    │ • Mistral OCR   │
│ • Chat Interface│    │ • Document Mgmt  │    │ • Gemini LLM    │
│ • Audio I/O     │    │ • State Mgmt     │    │ • Groq ASR      │
│ • Document View │    │ • Stream Handling│    │ • OpenAI TTS    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Data Flow

1. **Document Processing**:
   ```
   PDF Upload → Mistral OCR → Markdown + Images → Document Store
   ```

2. **Chat Processing**:
   ```
   User Input → Context Building → Gemini API → Streaming Response
   ```

3. **Audio Processing**:
   ```
   Audio Input → Groq Whisper → Text Input
   Response Text → OpenAI TTS → Audio Output
   ```

### Key Components

| Component | Responsibility |
|-----------|----------------|
| `upload_and_process()` | PDF upload and OCR processing |
| `stream_assistant_reply()` | AI response generation with streaming |
| `create_chat_messages_for_llm()` | Context preparation for AI model |
| `transcribe_audio()` | Speech-to-text conversion |
| `text_to_speech()` | Text-to-speech generation |
| `save_*_payload()` | Data persistence functions |

---

## API Integration

### Mistral OCR Service
- **Purpose**: Extract text and images from PDF documents
- **Model**: `mistral-ocr-latest`
- **Output**: Markdown with base64-encoded images
- **Features**: Multi-page support, image preservation

### Google Gemini (via OpenAI endpoint)
- **Purpose**: Primary conversational AI
- **Model**: `gemini-2.5-flash-preview-05-20`
- **Context**: Up to 2M tokens for large document support
- **Features**: Streaming responses, multi-modal input

### Groq Whisper
- **Purpose**: Speech recognition
- **Model**: `whisper-large-v3`
- **Input**: Audio files (various formats)
- **Output**: Transcribed text

### OpenAI TTS
- **Purpose**: Text-to-speech conversion
- **Model**: `gpt-4o-mini-tts`
- **Voice**: Configurable (default: "alloy")
- **Output**: MP3 audio format

---

## File Structure

```
project/
├── main.py                          # Main application file
├── .env                            # Environment variables (create this)
├── readme.md                       # This documentation
├── requirements.txt                # Python dependencies (create this)
├── chat_history_gradio.json       # Auto-generated chat history
├── llm_structured_call.json       # Auto-generated LLM payloads
├── llm_structured_call_show.json  # Auto-generated LLM payloads (truncated)
└── [uploaded_files.pdf]           # Your uploaded PDF documents
```

### Auto-generated Files

The application automatically creates and maintains several JSON files:

- **`chat_history_gradio.json`**: Stores the Gradio chat interface history
- **`llm_structured_call.json`**: Complete LLM conversation payloads
- **`llm_structured_call_show.json`**: Truncated payloads for debugging

---

## Troubleshooting

### Common Issues

1. **Missing API Keys**
   ```
   Error: GEMINI_API_KEY is not set in the environment variables.
   ```
   **Solution**: Ensure all required API keys are set in your `.env` file

2. **PDF Processing Errors**
   ```
   Error processing filename.pdf: [error details]
   ```
   **Solution**: Check PDF file integrity and Mistral API connectivity

3. **Audio Not Working**
   - Ensure microphone permissions are granted
   - Check audio file formats and browser compatibility
   - Verify Groq and OpenAI API keys for ASR/TTS

4. **Streaming Issues**
   - Check internet connectivity
   - Verify Gemini API access and quotas
   - Monitor browser console for WebSocket errors

### Performance Tips

1. **Large Documents**: The application handles large PDFs but may be slower with very large files
2. **Memory Usage**: Multiple large documents may consume significant memory
3. **API Limits**: Monitor your API usage across all services
4. **Browser Performance**: Use modern browsers for best streaming experience

### Debug Mode

Enable detailed logging by checking the console output when running `python main.py`. The application provides extensive logging for debugging purposes.

---

## Contributing

We welcome contributions to improve this multi-document PDF chat assistant!

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** with clear, documented code
4. **Test thoroughly** with various PDF types and use cases
5. **Submit a pull request** with detailed description

### Areas for Contribution

- **UI/UX improvements**: Enhanced document viewer, better mobile support
- **Performance optimization**: Faster document processing, memory efficiency
- **Additional models**: Support for other LLM providers or OCR services
- **Export features**: PDF generation, conversation exports
- **Security enhancements**: Input validation, API key management
- **Testing**: Unit tests, integration tests, performance benchmarks

### Development Guidelines

- Follow Python PEP 8 style guidelines
- Add docstrings for all functions
- Handle errors gracefully with user-friendly messages
- Test with various PDF types and sizes
- Document any new dependencies or configuration options

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Third-party Services

This application integrates with several third-party services. Please review their respective terms of service:

- [Google AI Studio Terms](https://ai.google.dev/terms)
- [Mistral AI Terms](https://mistral.ai/terms/)
- [Groq Terms](https://groq.com/terms-of-service/)
- [OpenAI Terms](https://openai.com/terms/)

---

## Acknowledgments

- **Gradio** for the excellent web interface framework
- **Mistral AI** for advanced OCR capabilities
- **Google** for the powerful Gemini language model
- **Groq** for fast Whisper inference
- **OpenAI** for high-quality text-to-speech

---

*Last updated: January 2025*
