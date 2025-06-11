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
7. [Module Structure](#module-structure)
8. [Detailed Implementation](#detailed-implementation)
9. [API Integration](#api-integration)
10. [File Structure](#file-structure)
11. [Troubleshooting](#troubleshooting)
12. [Contributing](#contributing)
13. [License](#license)

---

## Overview

This application is a sophisticated multi-media chat assistant that combines advanced OCR, AI language models, video processing, and audio capabilities. Built with Gradio and organized into modular components, it provides an intuitive interface for uploading, processing, and conversing with multiple PDF documents and videos simultaneously.

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
- **Modular architecture**: Well-organized codebase with separated concerns for maintainability

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
- **JSON exports**: Automatic saving of chat history and LLM payloads to `json/` folder
- **Structured document info**: `json/docs_structured_info.json` with complete document metadata
- **Video tracking**: `json/video_structured_info.json` for video metadata (future feature)
- **Session management**: State preservation across application restarts
- **Debug capabilities**: Detailed logging and payload inspection
- **Document deletion handling**: On document removal, the LLM call payload replaces the removed document's content block with a deletion info block and appends an internal deletion notification.

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
   pip install gradio python-dotenv mistralai google-generativeai openai markdown pathlib IPython base64 re shutil json groq
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

The application uses the following models (configurable in [`config.py`](config.py:1)):

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
│                 │    │     Modules      │    │                 │
│ • File Upload   │    │                  │    │ • Mistral OCR   │
│ • Video Upload  │    │ • Document Utils │    │ • Gemini LLM    │
│ • Chat Interface│    │ • Video Utils    │    │ • Groq ASR      │
│ • Audio I/O     │    │ • Audio Utils    │    │ • OpenAI TTS    │
│ • Media Viewer  │    │ • State Manager  │    │ • YouTube API   │
│                 │    │ • Data Manager   │    │                 │
│                 │    │ • UI Utils       │    │                 │
│                 │    │ • Config         │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## Module Structure

The application is organized into separate modules for better maintainability and separation of concerns:

### Core Modules

| Module | File | Purpose |
|--------|------|---------|
| **Configuration** | [`config.py`](config.py:1) | Environment loading and API client initialization |
| **Data Management** | [`manage/data_manager.py`](manage/data_manager.py:1) | JSON file persistence and data operations |
| **Document Processing** | [`utils/document_utils.py`](utils/document_utils.py:1) | PDF processing, OCR, and document management |
| **Video Processing** | [`utils/video_utils.py`](utils/video_utils.py:1) | Video upload and YouTube integration |
| **Audio Processing** | [`utils/audio_utils.py`](utils/audio_utils.py:1) | Speech-to-text and text-to-speech functionality |
| **UI Components** | [`utils/ui_utils.py`](utils/ui_utils.py:1) | HTML generation and user interface components |
| **State Management** | [`manage/state_manager.py`](manage/state_manager.py:1) | Application state and chat history management |
| **Main Application** | [`main.py`](main.py:1) | Gradio UI setup and global variable coordination |

### Module Dependencies

```
main.py
├── config.py (API clients)
├── manage/
│   ├── data_manager.py (JSON persistence)
│   └── state_manager.py (chat management)
└── utils/
    ├── document_utils.py (PDF processing)
    ├── video_utils.py (video handling)
    ├── audio_utils.py (speech processing)
    └── ui_utils.py (HTML generation)
```

### Key Features of Modular Design

- **Separation of Concerns**: Each module handles a specific aspect of functionality
- **Maintainability**: Easy to update and debug individual components
- **Testability**: Modules can be tested independently
- **Reusability**: Functions can be reused across different parts of the application
- **Global State Management**: [`main.py`](main.py:1) maintains global variables while modules handle business logic
- **Organized Structure**: Related modules are grouped into logical folders (`utils/` and `manage/`)

---

## Detailed Implementation

### 1. Configuration Module ([`config.py`](config.py:1))

**Environment Setup & Client Initialization**
- **[`load_env()`](config.py:6)**: Loads environment variables from `.env` file
- **API Key Validation**: Validates all required API keys (Gemini, Mistral, Groq, OpenAI)
- **[`initialize_api_clients()`](config.py:28)**: Creates and returns all API client instances
- **Client Types**:
  - `mistral_client` – PDF OCR processing
  - `openai_client` (Gemini endpoint) – LLM chat responses
  - `groq_client` – Whisper ASR via Groq
  - `openai_tts_client` – OpenAI TTS generation

### 2. Data Management Module ([`manage/data_manager.py`](manage/data_manager.py:1))

**JSON Persistence & Data Operations**
- **[`initialize_json_files()`](manage/data_manager.py:163)**: Creates empty JSON files on startup
- **[`save_chat_history()`](manage/data_manager.py:37)**: Persists Gradio chat history
- **[`save_llm_call_payload()`](manage/data_manager.py:16)**: Saves LLM conversation payloads
- **[`save_docs_structured_info()`](manage/data_manager.py:135)**: Exports structured document data
- **[`generate_docs_structured_info()`](manage/data_manager.py:55)**: Creates structured JSON from document data
- **Absolute Path Handling**: Uses `os.path.dirname(os.path.abspath(__file__))` to ensure correct JSON folder access

### 3. Document Processing Module ([`utils/document_utils.py`](utils/document_utils.py:1))

**PDF Processing & OCR Management**
- **[`upload_and_process_document()`](utils/document_utils.py:145)**: Handles single PDF upload and OCR
- **[`create_document_content_block()`](utils/document_utils.py:14)**: Generates LLM-compatible content blocks
- **[`create_chat_messages_for_llm()`](utils/document_utils.py:106)**: Builds complete LLM context
- **[`view_document()`](utils/document_utils.py:135)**: Handles document viewing functionality
- **OCR Processing**: Integrates with Mistral OCR for text and image extraction

### 4. Video Processing Module ([`utils/video_utils.py`](utils/video_utils.py:1))

**Video Upload & YouTube Integration**
- **[`process_video_upload()`](utils/video_utils.py:6)**: Handles local video files and YouTube URLs
- **[`extract_youtube_id()`](utils/video_utils.py:49)**: Extracts video ID from YouTube URLs
- **Video Storage**: In-memory storage with metadata tracking
- **Duplicate Prevention**: Avoids re-uploading same videos

### 5. Audio Processing Module ([`utils/audio_utils.py`](utils/audio_utils.py:1))

**Speech Processing & Audio Generation**
- **[`transcribe_audio()`](utils/audio_utils.py:6)**: Groq Whisper speech-to-text
- **[`text_to_speech()`](utils/audio_utils.py:38)**: OpenAI TTS text-to-speech
- **[`process_audio_input()`](utils/audio_utils.py:72)**: Voice input processing
- **[`get_last_response_and_convert_to_speech()`](utils/audio_utils.py:94)**: TTS for AI responses

### 6. UI Components Module ([`utils/ui_utils.py`](utils/ui_utils.py:1))

**HTML Generation & Interface Components**
- **[`generate_document_buttons()`](utils/ui_utils.py:6)**: Creates document navigation HTML
- **[`generate_media_viewer()`](utils/ui_utils.py:23)**: Unified document and video viewer
- **Responsive Design**: Mobile-friendly HTML components
- **Interactive Elements**: Expandable content and video players

### 7. State Management Module ([`manage/state_manager.py`](manage/state_manager.py:1))

**Application State & Chat Management**
- **[`add_user_and_placeholder()`](manage/state_manager.py:49)**: Adds user message with placeholder
- **[`stream_assistant_reply()`](manage/state_manager.py:100)**: Handles streaming LLM responses
- **[`clear_chat()`](manage/state_manager.py:75)**: Clears chat while preserving documents
- **[`reset_all_state()`](manage/state_manager.py:7)**: Complete application state reset
- **Relative Imports**: Uses proper relative imports (`.data_manager` and `..utils.document_utils`)

### 8. Main Application ([`main.py`](main.py:1))

**Gradio UI & Global Coordination**
- **Global Variables**: Manages application-wide state
- **Wrapper Functions**: Bridges modules with global state
- **UI Event Handlers**: Connects Gradio events to module functions
- **Session Management**: Coordinates data flow between modules

### Data Flow Architecture

1. **Document Processing Flow**:
   ```
   PDF Upload → utils/document_utils.py → Mistral OCR → manage/data_manager.py → JSON Storage
   ```

2. **Video Processing Flow**:
   ```
   Video Upload/YouTube → utils/video_utils.py → In-Memory Storage → utils/ui_utils.py → Display
   ```

3. **Chat Processing Flow**:
   ```
   User Input → manage/state_manager.py → utils/document_utils.py → Gemini API → Streaming Response
   ```

4. **Audio Processing Flow**:
   ```
   Audio Input → utils/audio_utils.py → Groq Whisper → Text Input
   Response Text → utils/audio_utils.py → OpenAI TTS → Audio Output
   ```

---

## API Integration

### Mistral OCR Service
- **Purpose**: Extract text and images from PDF documents
- **Model**: `mistral-ocr-latest`
- **Module**: [`utils/document_utils.py`](utils/document_utils.py:1)
- **Output**: Markdown with base64-encoded images
- **Features**: Multi-page support, image preservation, structured data export

### Google Gemini (via OpenAI endpoint)
- **Purpose**: Primary conversational AI
- **Model**: `gemini-2.5-flash-preview-05-20`
- **Module**: [`manage/state_manager.py`](manage/state_manager.py:1)
- **Context**: Up to 2M tokens for large document support
- **Features**: Streaming responses, multi-modal input, immediate feedback

### Groq Whisper
- **Purpose**: Speech recognition
- **Model**: `whisper-large-v3`
- **Module**: [`utils/audio_utils.py`](utils/audio_utils.py:1)
- **Input**: Audio files (various formats)
- **Output**: Transcribed text for chat input

### OpenAI TTS
- **Purpose**: Text-to-speech conversion
- **Model**: `gpt-4o-mini-tts`
- **Module**: [`utils/audio_utils.py`](utils/audio_utils.py:1)
- **Voice**: Configurable (default: "alloy")
- **Output**: MP3 audio format with auto-play

### YouTube Integration
- **Purpose**: Video embedding and playback
- **Module**: [`utils/video_utils.py`](utils/video_utils.py:1)
- **Method**: Direct URL parsing and iframe embedding
- **Features**: Automatic video ID extraction, duplicate prevention

---

## File Structure

```
project/
├── main.py                          # Main application with Gradio UI
├── config.py                        # Environment and API client configuration
├── .env                            # Environment variables (create this)
├── readme.md                       # This documentation
├── requirements.txt                # Python dependencies (create this)
├── utils/                          # Utility modules folder
│   ├── __init__.py                     # Package initialization
│   ├── document_utils.py               # PDF processing and OCR functionality
│   ├── video_utils.py                  # Video upload and YouTube integration
│   ├── audio_utils.py                  # Speech-to-text and text-to-speech
│   └── ui_utils.py                     # HTML generation and UI components
├── manage/                         # Management modules folder
│   ├── __init__.py                     # Package initialization
│   ├── data_manager.py                 # JSON persistence and data operations
│   └── state_manager.py                # Application state and chat management
├── json/                           # JSON data folder
│   ├── chat_history_gradio.json       # Auto-generated chat history
│   ├── llm_structured_call.json       # Auto-generated LLM payloads
│   ├── llm_structured_call_show.json  # Auto-generated LLM payloads (truncated)
│   ├── docs_structured_info.json      # Auto-generated structured document data
│   ├── video_structured_info.json     # Auto-generated video metadata (future)
│   ├── doc_json_info_schema.json      # Document data schema (if present)
│   └── video_json_info_schema.json    # Video data schema (if present)
├── material/                       # Sample materials folder
│   └── AGV_Task_2023.pdf              # Sample PDF document
└── [uploaded_files.pdf]           # Your uploaded PDF documents (temporary)
```

### Auto-generated Files

The application automatically creates and maintains several JSON files in the `json/` folder:

- **`json/chat_history_gradio.json`**: Stores the Gradio chat interface history
- **`json/llm_structured_call.json`**: Complete LLM conversation payloads
- **`json/llm_structured_call_show.json`**: Truncated payloads for debugging
- **`json/docs_structured_info.json`**: Structured document information with content and metadata
- **`json/video_structured_info.json`**: Video metadata and information (future feature)

### Module Organization

Each module is self-contained with specific responsibilities:

- **[`config.py`](config.py:1)**: Centralized configuration management
- **[`manage/data_manager.py`](manage/data_manager.py:1)**: All JSON operations and data persistence (uses absolute paths to json/ folder)
- **[`utils/document_utils.py`](utils/document_utils.py:1)**: Complete PDF processing pipeline
- **[`utils/video_utils.py`](utils/video_utils.py:1)**: Video handling and YouTube integration
- **[`utils/audio_utils.py`](utils/audio_utils.py:1)**: Audio processing and speech services
- **[`utils/ui_utils.py`](utils/ui_utils.py:1)**: HTML generation and UI components
- **[`manage/state_manager.py`](manage/state_manager.py:1)**: Chat state and conversation management
- **[`main.py`](main.py:1)**: Global state coordination and Gradio interface (uses `material/` for examples)

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

6. **Module Import Errors**
   - Ensure all module files are in their respective folders (`utils/` and `manage/`)
   - Check for syntax errors in individual modules
   - Verify Python path and module accessibility
   - Ensure `__init__.py` files exist in utils/ and manage/ folders

7. **JSON File Path Issues**
   - The data_manager.py uses absolute paths to ensure reliable JSON file access
   - If JSON files aren't being created, check file permissions in the json/ folder
   - Verify the json/ folder exists and is writable

### Performance Tips

1. **Large Documents**: The application handles large PDFs but may be slower with very large files
2. **Memory Usage**: Multiple large documents and videos may consume significant memory
3. **API Limits**: Monitor your API usage across all services
4. **Browser Performance**: Use modern browsers for best streaming and video experience
5. **Video Storage**: Videos are kept in memory during session - restart app to free memory
6. **Modular Loading**: Individual modules can be debugged separately for faster development

### Debug Mode

Enable detailed logging by checking the console output when running `python main.py`. The application provides extensive logging for debugging purposes, including:
- Document processing status
- Video upload confirmations
- API call details
- Structured data generation logs
- Module loading and initialization status

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
- **Module enhancements**: Additional features for existing modules
- **New modules**: Additional functionality in separate modules

### Development Guidelines

- Follow Python PEP 8 style guidelines
- Add docstrings for all functions
- Handle errors gracefully with user-friendly messages
- Test with various PDF types, video formats, and sizes
- Document any new dependencies or configuration options
- Ensure video processing maintains memory efficiency
- **Modular Development**: Add new features as separate modules when possible
- **Function Documentation**: Include parameter and return value documentation
- **Error Handling**: Implement proper error handling in each module
- **Global State**: Use wrapper functions in [`main.py`](main.py:1) to manage global variables

### Module Development Guidelines

When creating new modules or modifying existing ones:

1. **Single Responsibility**: Each module should handle one specific area of functionality
2. **Clean Interfaces**: Functions should have clear parameters and return values
3. **Error Handling**: Include try/catch blocks and meaningful error messages
4. **Documentation**: Add comprehensive docstrings and comments
5. **Testing**: Test modules independently when possible
6. **Global State**: Avoid direct global variable access; use parameters instead

### Folder Organization

- **`utils/`**: Contains all utility modules for specific functionality (document, video, audio, UI processing)
- **`manage/`**: Contains management modules for state and data persistence
- **`json/`**: Contains all automatically generated JSON files for data persistence
- **`material/`**: Contains sample materials and example documents
- **Root directory**: Contains main application file, configuration, and documentation

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
- **Python Community** for excellent libraries and development tools

---

*Last updated: December 2025 - Refactored to modular architecture with organized folder structure*
