# Multi-Media Chat Assistant

**An advanced AI-powered document and video analysis conversational interface**

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

This application is a sophisticated multi-media chat assistant that combines advanced OCR, AI language models, video processing, and audio capabilities. Built with Gradio, it provides an intuitive interface for uploading, processing, and conversing with multiple PDF documents and videos simultaneously.

### Key Capabilities

- **Multi-document support**: Upload and manage multiple PDF files simultaneously
- **Video integration**: Support for local video files and YouTube videos with embedded viewing
- **Advanced OCR**: Extract text and images from PDFs using Mistral's OCR service
- **AI-powered chat**: Conversation with document content using Gemini 2.5 Flash
- **Voice interaction**: Speech-to-text input and text-to-speech output
- **Real-time streaming**: Token-by-token response streaming for immediate feedback
- **Persistent state**: Maintains chat history and document context across sessions
- **Unified media viewer**: Side-by-side document and video viewer with chat interface
- **Structured data export**: Automatic generation of structured JSON data for documents and videos

---

## Features

### 🗂️ Document Management
- **Multi-file upload**: Support for multiple PDF files with drag-and-drop
- **Smart document tracking**: Chronological order preservation and position tracking
- **Dynamic file management**: Add/remove documents without losing chat history
- **Visual content preview**: Expandable document viewer with formatted content
- **OCR with image preservation**: Extract text while maintaining embedded images
- **Structured document data**: Auto-generated JSON schemas for document content

### 🎥 Video Support
- **Local video files**: Upload and view multiple video formats (MP4, AVI, MOV, WMV, FLV, WebM, MKV)
- **YouTube integration**: Add YouTube videos via URL with embedded player
- **In-memory processing**: Videos stored in memory for session-based access
- **Combined media viewer**: Unified interface for documents and videos
- **Video metadata tracking**: Organized video information with structured data export

### 💬 Conversational AI
- **Context-aware responses**: AI understands all uploaded document content simultaneously
- **Streaming responses**: Real-time token-by-token response generation
- **Persistent chat history**: Maintains conversation context across sessions
- **Smart prompting**: Optimized message structure for multi-document queries
- **Enhanced user experience**: Immediate placeholder display with streaming updates

### 🎤 Audio Features
- **Speech-to-text**: Voice input using Groq's Whisper-large-v3 model
- **Text-to-speech**: AI response audio using OpenAI's TTS models
- **Real-time transcription**: Instant audio processing and text insertion
- **Configurable voices**: Multiple voice options for audio output
- **Auto-play responses**: Automatic audio playback for AI responses

### 💾 Data Persistence & Export
- **JSON exports**: Automatic saving of chat history and LLM payloads
- **Structured document info**: `docs_structured_info.json` with complete document metadata
- **Video tracking**: `video_structured_info.json` for video metadata (future feature)
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
   pip install gradio python-dotenv mistralai google-generativeai openai markdown pathlib IPython base64 re shutil json
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

1. **Single or Multiple Files**: Use the PDF upload area to select one or more PDF files
2. **Drag and Drop**: Drag PDF files directly onto the upload area
3. **Document Management**: Files can be added or removed dynamically
4. **Preview Content**: Expand document sections to view full content with images

### Adding Videos

1. **Local Video Files**: Upload video files in supported formats (MP4, AVI, MOV, etc.)
2. **YouTube Videos**: Paste YouTube URLs and click "Add YouTube" button
3. **Video Viewing**: Videos are embedded in the media viewer for instant playback
4. **Duplicate Prevention**: System prevents uploading duplicate videos

### Chatting with Documents

1. **Text Input**: Type questions in the text box and press Enter or click Send
2. **Voice Input**: Click the microphone button to record voice questions
3. **Context Awareness**: The AI has access to all uploaded document content
4. **Streaming Responses**: Watch responses appear in real-time with immediate placeholder display

### Audio Features

1. **Voice Questions**: Record audio that gets automatically transcribed to text input
2. **Listen to Responses**: Click "🔊 Listen to Last Response" for audio playback
3. **Auto-play**: Audio responses play automatically when generated
4. **Voice Input Integration**: Microphone input populates text box without auto-sending

### Media Viewing

1. **Unified Media Panel**: View all uploaded documents and videos in the left panel
2. **Expandable Content**: Click "View Full Content" to see detailed document content
3. **Video Playback**: Watch YouTube videos or local videos directly in the interface
4. **Image Support**: View embedded images from PDF documents
5. **Organized Display**: Clear separation between documents and videos with item counts

---

## Architecture

### System Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Gradio UI     │◄──►│   Application    │◄──►│   External APIs │
│                 │    │     Logic        │    │                 │
│ • File Upload   │    │                  │    │ • Mistral OCR   │
│ • Video Upload  │    │ • Document Mgmt  │    │ • Gemini LLM    │
│ • Chat Interface│    │ • Video Mgmt     │    │ • Groq ASR      │
│ • Audio I/O     │    │ • State Mgmt     │    │ • OpenAI TTS    │
│ • Media Viewer  │    │ • Stream Handling│    │ • YouTube API   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Data Flow

1. **Document Processing**:
   ```
   PDF Upload → Mistral OCR → Markdown + Images → Document Store → Structured JSON
   ```

2. **Video Processing**:
   ```
   Video Upload/YouTube URL → Video Store → Media Viewer → Structured Data
   ```

3. **Chat Processing**:
   ```
   User Input → Context Building → Gemini API → Streaming Response → Audio Output
   ```

4. **Audio Processing**:
   ```
   Audio Input → Groq Whisper → Text Input
   Response Text → OpenAI TTS → Audio Output
   ```

### Key Components

| Component | Responsibility |
|-----------|----------------|
| `upload_and_process()` | PDF upload and OCR processing |
| `process_video_upload()` | Video file and YouTube URL processing |
| `stream_assistant_reply()` | AI response generation with streaming |
| `add_user_and_placeholder()` | Immediate UI feedback for user queries |
| `create_chat_messages_for_llm()` | Context preparation for AI model |
| `generate_media_viewer()` | Unified document and video interface |
| `generate_docs_structured_info()` | Structured document data generation |
| `transcribe_audio()` | Speech-to-text conversion |
| `text_to_speech()` | Text-to-speech generation |
| `save_*_payload()` | Data persistence functions |

---

## API Integration

### Mistral OCR Service
- **Purpose**: Extract text and images from PDF documents
- **Model**: `mistral-ocr-latest`
- **Output**: Markdown with base64-encoded images
- **Features**: Multi-page support, image preservation, structured data export

### Google Gemini (via OpenAI endpoint)
- **Purpose**: Primary conversational AI
- **Model**: `gemini-2.5-flash-preview-05-20`
- **Context**: Up to 2M tokens for large document support
- **Features**: Streaming responses, multi-modal input, immediate feedback

### Groq Whisper
- **Purpose**: Speech recognition
- **Model**: `whisper-large-v3`
- **Input**: Audio files (various formats)
- **Output**: Transcribed text for chat input

### OpenAI TTS
- **Purpose**: Text-to-speech conversion
- **Model**: `gpt-4o-mini-tts`
- **Voice**: Configurable (default: "alloy")
- **Output**: MP3 audio format with auto-play

### YouTube Integration
- **Purpose**: Video embedding and playback
- **Method**: Direct URL parsing and iframe embedding
- **Features**: Automatic video ID extraction, duplicate prevention

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
├── docs_structured_info.json      # Auto-generated structured document data
├── video_structured_info.json     # Auto-generated video metadata (future)
├── doc_json_info_schema.json      # Document data schema (if present)
├── video_json_info_schema.json    # Video data schema (if present)
└── [uploaded_files.pdf]           # Your uploaded PDF documents
```

### Auto-generated Files

The application automatically creates and maintains several JSON files:

- **`chat_history_gradio.json`**: Stores the Gradio chat interface history
- **`llm_structured_call.json`**: Complete LLM conversation payloads
- **`llm_structured_call_show.json`**: Truncated payloads for debugging
- **`docs_structured_info.json`**: Structured document information with content and metadata
- **`video_structured_info.json`**: Video metadata and information (future feature)

### Structured Data Schema

The `docs_structured_info.json` follows a specific schema with:
- Document metadata (name, ID, availability status)
- Page-by-page content with markdown and images
- Image tags with base64 data for AI processing
- Hierarchical organization for multi-document support

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

3. **Video Upload Issues**
   - Check supported video formats (MP4, AVI, MOV, WMV, FLV, WebM, MKV)
   - Verify YouTube URL format and accessibility
   - Ensure sufficient memory for large video files

4. **Audio Not Working**
   - Ensure microphone permissions are granted
   - Check audio file formats and browser compatibility
   - Verify Groq and OpenAI API keys for ASR/TTS

5. **Streaming Issues**
   - Check internet connectivity
   - Verify Gemini API access and quotas
   - Monitor browser console for WebSocket errors

### Performance Tips

1. **Large Documents**: The application handles large PDFs but may be slower with very large files
2. **Memory Usage**: Multiple large documents and videos may consume significant memory
3. **API Limits**: Monitor your API usage across all services
4. **Browser Performance**: Use modern browsers for best streaming and video experience
5. **Video Storage**: Videos are kept in memory during session - restart app to free memory

### Debug Mode

Enable detailed logging by checking the console output when running `python main.py`. The application provides extensive logging for debugging purposes, including:
- Document processing status
- Video upload confirmations
- API call details
- Structured data generation logs

---

## Contributing

We welcome contributions to improve this multi-media chat assistant!

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** with clear, documented code
4. **Test thoroughly** with various PDF types, video formats, and use cases
5. **Submit a pull request** with detailed description

### Areas for Contribution

- **Video Analysis**: Implement AI-powered video content analysis
- **UI/UX improvements**: Enhanced media viewer, better mobile support
- **Performance optimization**: Faster document processing, memory efficiency
- **Additional formats**: Support for more document and video types
- **Export features**: PDF generation, conversation exports, media downloads
- **Security enhancements**: Input validation, API key management
- **Testing**: Unit tests, integration tests, performance benchmarks

### Development Guidelines

- Follow Python PEP 8 style guidelines
- Add docstrings for all functions
- Handle errors gracefully with user-friendly messages
- Test with various PDF types, video formats, and sizes
- Document any new dependencies or configuration options
- Ensure video processing maintains memory efficiency

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Third-party Services

This application integrates with several third-party services. Please review their respective terms of service:

- [Google AI Studio Terms](https://ai.google.dev/terms)
- [Mistral AI Terms](https://mistral.ai/terms/)
- [Groq Terms](https://groq.com/terms-of-service/)
- [OpenAI Terms](https://openai.com/terms/)
- [YouTube Terms of Service](https://www.youtube.com/t/terms)

---

## Acknowledgments

- **Gradio** for the excellent web interface framework
- **Mistral AI** for advanced OCR capabilities
- **Google** for the powerful Gemini language model
- **Groq** for fast Whisper inference
- **OpenAI** for high-quality text-to-speech
- **YouTube** for video embedding capabilities

---

*Last updated: January 2025*
