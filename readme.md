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
- **Multiple YouTube URLs**: Add multiple YouTube videos at once by pasting a list of URLs.
- **Video Removal**: Easily remove videos from the session using a cross button on the video card or in the upload list.
- **In-memory processing**: Videos stored in memory for session-based access
- **Combined media viewer**: Unified interface for documents and videos
- **Video metadata tracking**: Organized video information with structured data export
- **AI-powered video description**: Generate detailed transcripts and descriptions using Gemini 2.5 Flash
- **Automatic chunking**: Handle long videos (>50 minutes) by breaking into segments
- **Contextual analysis**: Rich descriptions including visuals, tone, and educational content
- **XML-based processing**: Robust XML format for reliable AI model output parsing
- **Dual UI display**: Separate dropdowns for video player and JSON descriptions
- **Syntax highlighting**: Beautiful, colorful JSON display with code-like formatting
- **Automatic generation**: Videos processed immediately upon upload without manual intervention
- **Parallel processing**: Multiple videos analyzed simultaneously for optimal performance
- **Smart caching**: Intelligent video ID tracking to prevent duplicate processing

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
- **Video descriptions**: `json/video_structured_info.json` with AI-generated video transcripts and descriptions
- **Session management**: State preservation across application restarts
- **Debug capabilities**: Detailed logging and payload inspection
- **Document deletion handling**: On document removal, the LLM call payload replaces the removed document's content block with a deletion info block and appends an internal deletion notification.

### 🤖 Video AI Analysis
- **Transcript generation**: Automatic speech-to-text with timestamps and expressions
- **Visual description**: Detailed analysis of video content, speaker gestures, and visual elements
- **Educational focus**: Optimized for lectures, tutorials, and informative content
- **Contextual timestamps**: Logical segmentation aligned with natural viewing patterns
- **Multi-part processing**: Automatic handling of videos longer than 50 minutes
- **Parallel processing**: Multiple videos processed simultaneously for efficiency
- **Rich metadata**: Comprehensive information capture including equations, diagrams, and key concepts
- **XML-to-JSON conversion**: Reliable parsing using structured XML format to prevent model output errors
- **Automatic triggering**: Video analysis starts immediately upon upload without user intervention
- **Duplicate prevention**: Smart tracking system prevents reprocessing of existing videos
- **Colorful JSON display**: Syntax-highlighted JSON output with professional code formatting
- **Real-time status updates**: Live feedback during processing with progress indicators
- **Error handling**: Robust error recovery and user-friendly error messages
- **Schema validation**: Structured data output following predefined JSON schema specifications

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
   pip install gradio python-dotenv mistralai google-generativeai google-genai openai markdown pathlib IPython base64 re shutil json groq asyncio
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
| **Google Gemini** | Primary LLM for chat responses and video analysis | `GEMINI_API_KEY` |
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
- **Video Analysis**: `gemini-2.5-flash-preview-05-20` (via Google GenAI SDK)
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

1. **Local Video Files**: Upload one or more video files in supported formats (MP4, AVI, MOV, etc.).
2. **Multiple YouTube Videos**: Paste multiple YouTube URLs (one per line) into the text area and click "Add YouTube Videos".
3. **Video Viewing**: Videos are embedded in the media viewer for instant playback.
4. **Duplicate Prevention**: The system prevents uploading duplicate videos.

### Removing Videos

1. **From Media Viewer**: Click the red cross (×) button on any video card in the media viewer to remove it.
2. **From Upload List**: For local videos, clicking the cross (×) next to the file in the upload component will also remove it from the session.

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
2. **Document Features**:
   - **Expandable Content**: Click "View Full Content" to see detailed document content
   - **Image Support**: View embedded images from PDF documents
   - **Content Preview**: Quick preview of document content before expanding
3. **Video Features**:
   - **Dual Dropdown Interface**: Each video has two separate expandable sections:
     - **📺 "Watch Video"**: Video player for YouTube or local video playback
     - **📄 "View AI Description (JSON)"**: Colorful syntax-highlighted JSON descriptions
   - **Professional JSON Display**: Code-like formatting with syntax highlighting
   - **Status Indicators**: Visual feedback showing processing state and availability
   - **Real-time Updates**: JSON descriptions appear automatically after processing
4. **Organized Display**: Clear separation between documents and videos with item counts
5. **Interactive Elements**: Smooth expand/collapse animations and responsive design
6. **Error Handling**: Graceful display of processing errors or missing descriptions

### Video Description Generation

1. **Upload Videos**: Add local video files or YouTube URLs to your collection
2. **Automatic Processing**: Videos are immediately analyzed upon upload with Gemini 2.5 Flash
3. **AI Analysis**: The system automatically creates detailed transcripts and descriptions using XML-based prompting
4. **Intelligent Handling**:
   - Videos under 50 minutes are processed as single units
   - Longer videos are automatically chunked into 50-minute segments
   - Multiple videos are processed in parallel using async/await for optimal performance
   - Smart caching prevents duplicate processing of previously analyzed videos
5. **Rich Output**: Generated descriptions include:
   - Timestamped transcripts with expressions and reactions
   - Visual analysis of content, gestures, and background elements
   - Educational context and technical concept explanations
   - Tone, mood, and audio environment descriptions
6. **Enhanced UI Display**:
   - **Dual dropdown interface**: Separate sections for video player and JSON descriptions
   - **Syntax highlighting**: Beautiful, colorful JSON display with code-like formatting
   - **Professional formatting**: Monospace fonts and color-coded syntax elements
   - **Expandable sections**: Click to view detailed JSON data structures
7. **Data Export**: Results are automatically saved to `json/video_structured_info.json` and cached in memory
8. **Status Updates**: Real-time feedback during the automatic processing with detailed progress information
9. **XML Processing**: Robust XML-to-JSON conversion eliminates model output parsing errors
10. **Error Recovery**: Comprehensive error handling with user-friendly status messages

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
| **Video Processing** | [`utils/video_utils.py`](utils/video_utils.py:1) | Video upload, YouTube integration, and processing coordination |
| **Video Description** | [`utils/video_description.py`](utils/video_description.py:1) | AI-powered video analysis, XML processing, transcription, and description generation |
| **Audio Processing** | [`utils/audio_utils.py`](utils/audio_utils.py:1) | Speech-to-text and text-to-speech functionality |
| **UI Components** | [`utils/ui_utils.py`](utils/ui_utils.py:1) | HTML generation, syntax highlighting, and user interface components |
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
  - `genai_client` – Google GenAI SDK for video analysis

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
- **[`process_video_upload()`](utils/video_utils.py:39)**: Handles local video files and multiple YouTube URLs with automatic description generation.
- **[`remove_video()`](utils/video_utils.py:342)**: Removes a specific video from the system, including from memory and JSON files.
- **[`parse_youtube_urls_from_text()`](utils/video_utils.py:394)**: Parses multiple YouTube URLs from a single text input.
- **[`extract_youtube_id()`](utils/video_utils.py:11)**: Extracts video ID from YouTube URLs.
- **[`generate_new_video_descriptions_sync()`](utils/video_utils.py:278)**: Synchronous wrapper for new video processing.
- **[`generate_new_video_descriptions_async()`](utils/video_utils.py:213)**: Asynchronous processing for parallel video analysis.
- **Video Storage**: In-memory storage with metadata tracking.
- **Duplicate Prevention**: Avoids re-uploading same videos and prevents reprocessing.
- **Smart Caching**: Tracks existing video IDs to optimize processing workflow.
- **Automatic Triggering**: Initiates video description generation immediately upon upload.

### 5. Video Description Module ([`utils/video_description.py`](utils/video_description.py:1))

**AI-Powered Video Analysis & XML Processing**
- **[`create_video_system_prompt()`](utils/video_description.py:35)**: Generates comprehensive system prompt for XML-based video analysis
- **[`get_video_description_chunk()`](utils/video_description.py:164)**: Processes individual video chunks using async Gemini API calls
- **[`parse_xml_to_json()`](utils/video_description.py:145)**: Robust XML parser that converts model output to structured JSON
- **[`extract_json_from_response()`](utils/video_description.py:217)**: Extracts and parses XML content from model responses
- **[`process_single_video()`](utils/video_description.py:372)**: Handles complete video processing workflow
- **[`generate_new_video_descriptions()`](utils/video_description.py:452)**: Parallel processing for multiple new videos
- **[`combine_video_parts()`](utils/video_description.py:346)**: Merges multi-part video analysis results
- **[`summarize_video_content()`](utils/video_description.py:298)**: Creates context summaries for long video processing
- **XML-to-JSON Conversion**: Eliminates JSON parsing errors through structured XML format
- **Chunking Support**: Automatic handling of videos longer than 50 minutes with context preservation
- **Async Processing**: True parallel processing using asyncio.gather() for multiple videos
- **Error Recovery**: Comprehensive error handling with graceful degradation

### 5. Audio Processing Module ([`utils/audio_utils.py`](utils/audio_utils.py:1))

**Speech Processing & Audio Generation**
- **[`transcribe_audio()`](utils/audio_utils.py:6)**: Groq Whisper speech-to-text
- **[`text_to_speech()`](utils/audio_utils.py:38)**: OpenAI TTS text-to-speech
- **[`process_audio_input()`](utils/audio_utils.py:72)**: Voice input processing
- **[`get_last_response_and_convert_to_speech()`](utils/audio_utils.py:94)**: TTS for AI responses

### 6. UI Components Module ([`utils/ui_utils.py`](utils/ui_utils.py:1))

**HTML Generation & Interface Components**
- **[`generate_document_buttons()`](utils/ui_utils.py:6)**: Creates document navigation HTML.
- **[`generate_media_viewer()`](utils/ui_utils.py:105)**: Unified document and video viewer with dual dropdown interface and removal buttons.
- **[`generate_youtube_url_manager()`](utils/ui_utils.py:449)**: Generates HTML interface for managing multiple YouTube URLs.
- **[`generate_video_description_json()`](utils/ui_utils.py:267)**: Generates video description display with status indicators.
- **[`create_syntax_highlighted_json()`](utils/ui_utils.py:344)**: Creates beautiful, colorful JSON syntax highlighting.
- **Responsive Design**: Mobile-friendly HTML components.
- **Interactive Elements**: Expandable content and video players.
- **Syntax Highlighting**: Professional code-like JSON display with color-coded elements.
- **Dual Interface**: Separate dropdowns for video playback and JSON descriptions.
- **Status Management**: Real-time indicators for processing state and availability.
- **Error Handling**: User-friendly error displays and fallback messages.

### 7. State Management Module ([`manage/state_manager.py`](manage/state_manager.py:1))

**Application State & Chat Management**
- **[`add_user_and_placeholder()`](manage/state_manager.py:49)**: Adds user message with placeholder
- **[`stream_assistant_reply()`](manage/state_manager.py:100)**: Handles streaming LLM responses
- **[`clear_chat()`](manage/state_manager.py:75)**: Clears chat while preserving documents
- **[`reset_all_state()`](manage/state_manager.py:7)**: Complete application state reset
- **Relative Imports**: Uses proper relative imports (`.data_manager` and `..utils.document_utils`)

### 8. Main Application ([`main.py`](main.py:1))

**Gradio UI & Global Coordination**
- **Global Variables**: Manages application-wide state.
- **Wrapper Functions**: Bridges modules with global state.
    - **[`process_video_upload_and_removal_wrapper()`](main.py:211)**: Handles both video uploads and removals from the file upload component.
    - **[`remove_video_wrapper()`](main.py:279)**: Handles video removal triggered by the cross buttons in the media viewer.
    - **[`process_multiple_youtube_urls_wrapper()`](main.py:301)**: Handles batch processing of multiple YouTube URLs.
- **UI Event Handlers**: Connects Gradio events to module functions.
- **Session Management**: Coordinates data flow between modules.

### Data Flow Architecture

1. **Document Processing Flow**:
   ```
   PDF Upload → utils/document_utils.py → Mistral OCR → manage/data_manager.py → JSON Storage
   ```

2. **Video Processing Flow**:
   ```
   Video Upload/YouTube → utils/video_utils.py → utils/video_description.py →
   Gemini API (XML) → XML Parser → JSON Conversion → manage/data_manager.py →
   utils/ui_utils.py → Syntax Highlighted Display
   ```

3. **Video Description Generation Flow**:
   ```
   New Video Detection → Parallel Async Processing → XML System Prompts →
   Gemini API Calls → XML Response → parse_xml_to_json() →
   Structured JSON → File Storage + Memory Cache → UI Updates
   ```

4. **Chat Processing Flow**:
   ```
   User Input → manage/state_manager.py → utils/document_utils.py → Gemini API → Streaming Response
   ```

5. **Audio Processing Flow**:
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

### Google GenAI SDK
- **Purpose**: Video analysis and description generation
- **Model**: `gemini-2.5-flash-preview-05-20`
- **Module**: [`utils/video_description.py`](utils/video_description.py:1)
- **Input**: Video files (local and YouTube), images, audio
- **Features**:
  - Async API calls for parallel processing
  - XML-structured prompting for reliable output parsing
  - Multi-modal analysis including visual and audio content
  - Chunking support for videos longer than 50 minutes
  - Context preservation across video segments

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
│   ├── video_structured_info.json     # Auto-generated video descriptions and transcripts
│   ├── doc_json_info_schema.json      # Document data schema (if present)
│   ├── video_json_info_schema.json    # Video data schema (if present)
│   └── video_structured_info_schema.xml # XML schema for video description generation
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
- **`json/video_structured_info.json`**: Complete video descriptions with timestamped transcripts and AI analysis
- **`json/video_structured_info_schema.xml`**: XML schema template for video description generation

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

4. **Video Description Generation Issues**
   - Ensure GEMINI_API_KEY is properly configured for GenAI client
   - Check video processing status in chat messages
   - Verify JSON file generation in `json/video_structured_info.json`
   - For XML parsing errors, check console output for detailed error messages
   - Large videos may take several minutes to process - be patient
   - If descriptions don't appear, try refreshing the media viewer

5. **Audio Not Working**
   - Ensure microphone permissions are granted
   - Check audio file formats and browser compatibility
   - Verify Groq and OpenAI API keys for ASR/TTS

6. **Streaming Issues**
   - Check internet connectivity
   - Verify Gemini API access and quotas
   - Monitor browser console for WebSocket errors

7. **Module Import Errors**
   - Ensure all module files are in their respective folders (`utils/` and `manage/`)
   - Check for syntax errors in individual modules
   - Verify Python path and module accessibility
   - Ensure `__init__.py` files exist in utils/ and manage/ folders

8. **JSON File Path Issues**
   - The data_manager.py uses absolute paths to ensure reliable JSON file access
   - If JSON files aren't being created, check file permissions in the json/ folder
   - Verify the json/ folder exists and is writable

9. **Video Description UI Issues**
   - If JSON descriptions don't display properly, check browser console for JavaScript errors
   - Syntax highlighting may not work in older browsers - use modern browsers
   - If dropdowns don't expand, refresh the page and try again
   - Color scheme issues may occur with certain browser themes

### Performance Tips

1. **Large Documents**: The application handles large PDFs but may be slower with very large files
2. **Memory Usage**: Multiple large documents and videos may consume significant memory
3. **API Limits**: Monitor your API usage across all services (especially Gemini for video processing)
4. **Browser Performance**: Use modern browsers for best streaming, video experience, and syntax highlighting
5. **Video Storage**: Videos are kept in memory during session - restart app to free memory
6. **Video Processing**:
   - Videos longer than 50 minutes are automatically chunked for better performance
   - Multiple videos process in parallel - consider API rate limits
   - Local videos consume more memory than YouTube videos
   - Large video files may take several minutes to analyze
7. **JSON Display**: Large video descriptions may slow down the UI - consider collapsing sections when not needed
8. **Modular Loading**: Individual modules can be debugged separately for faster development
9. **Async Processing**: Video descriptions use async processing for optimal performance
10. **Caching**: Smart caching prevents reprocessing of existing videos

### Debug Mode

Enable detailed logging by checking the console output when running `python main.py`. The application provides extensive logging for debugging purposes, including:
- Document processing status
- Video upload confirmations
- Video description generation progress
- XML parsing and JSON conversion details
- API call details and response handling
- Structured data generation logs
- Module loading and initialization status
- Async processing status and parallel execution logs
- Error handling and recovery attempts
- UI component generation and syntax highlighting status

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

- **Video Analysis Enhancements**:
  - Advanced video content analysis features
  - Support for additional video formats
  - Improved chunking algorithms for long videos
  - Enhanced XML parsing robustness
- **UI/UX improvements**:
  - Enhanced media viewer with better mobile support
  - Improved syntax highlighting themes
  - Better responsive design for video descriptions
  - Advanced search and filtering for video content
- **Performance optimization**:
  - Faster document processing and memory efficiency
  - Optimized async video processing
  - Better caching strategies
  - Reduced memory footprint for large videos
- **Additional formats**: Support for more document and video types
- **Export features**:
  - PDF generation with video descriptions
  - Conversation exports including media
  - Video description downloads
  - Structured data exports in multiple formats
- **Security enhancements**: Input validation, API key management, content sanitization
- **Testing**:
  - Unit tests for video processing modules
  - Integration tests for XML parsing
  - Performance benchmarks for parallel processing
  - UI testing for syntax highlighting
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
- **Async Development**: Use proper async/await patterns for video processing
- **XML Processing**: Follow established XML schema patterns for reliable parsing
- **UI Components**: Maintain consistent styling and responsive design principles
- **Performance**: Consider memory usage and processing time for video operations
- **Caching**: Implement smart caching to avoid duplicate processing

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

*Last updated: June 2025 - Enhanced with comprehensive video description generation, XML processing, parallel async operations, and advanced UI features*
