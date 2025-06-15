"""
Multi-Media Chat Assistant - Main Application

This application is a sophisticated multi-media chat assistant that combines advanced OCR,
AI language models, video processing, and audio capabilities. Built with Gradio, it provides
an intuitive interface for uploading, processing, and conversing with multiple PDF documents
and videos simultaneously.
"""
import json
import gradio as gr
import os
from pathlib import Path

# Import custom modules
from config import load_env, initialize_api_clients
from manage.data_manager import (save_llm_call_payload, save_chat_history,
                                save_docs_structured_info, save_video_structured_info, initialize_json_files)
from utils.document_utils import (create_document_content_block, upload_and_process_document,
                                 view_document, create_chat_messages_for_llm)
from utils.video_utils import process_video_upload, remove_video, parse_youtube_urls_from_text
from utils.audio_utils import process_audio_input, get_last_response_and_convert_to_speech
from utils.ui_utils import generate_document_buttons, generate_media_viewer, generate_youtube_url_manager
from manage.state_manager import (reset_all_state, add_user_and_placeholder,
                                 clear_chat, stream_assistant_reply)

# Initialize API clients
mistral_client, openai_client, groq_client, openai_tts_client, model, genai_client = initialize_api_clients()

# Global variables to store multiple documents and videos content
documents = {}  # Dictionary to store all document data: {doc_id: {content, text, ocr_response, file_name}}
document_order = []  # List to maintain order of uploaded documents
videos = {}  # Dictionary to store video data: {video_id: {file_path, file_name, video_type, url}}
video_order = []  # List to maintain order of uploaded videos
llm_chat_history = None
llm_chat_history_show = None
document_positions = {}  # Track position of each document in chat history: {doc_id: position_index}
chat_position_counter = 0  # Counter to track next position for new documents
structured_docs_cache = []  # In-memory cache for structured document information
structured_videos_cache = []  # In-memory cache for structured video information

# Initialize empty JSON files at startup
initialize_json_files()

def upload_and_process(files, chat_history):
    """
    Smart document management with preserved chronological chat history.
    
    Args:
        files: List of uploaded file objects from Gradio (or single file)
        chat_history: Current chat history
        
    Returns:
        Updated chat history and HTML buttons for document selection
    """
    global documents, document_order, llm_chat_history, llm_chat_history_show
    global document_positions, chat_position_counter, structured_docs_cache
    
    # Handle empty uploads
    if files is None:
        files = []
    elif not isinstance(files, list):
        files = [files]
    
    # Filter out None values and get current file names
    current_files = [f for f in files if f is not None]
    current_file_names = [Path(f.name).name for f in current_files]
    
    # Get existing file names
    existing_file_names = [documents[doc_id]["file_name"] for doc_id in document_order]
    
    # Find files to remove (existing files not in current upload)
    files_to_remove = [name for name in existing_file_names if name not in current_file_names]
    
    # Find files to add (current files not in existing)
    files_to_add = [f for f in current_files if Path(f.name).name not in existing_file_names]
    
    processed_files = []
    failed_files = []
    removed_files = []
    removed_positions = {}
    
    # Handle document removals (completely remove documents), track positions
    for file_name_to_remove in files_to_remove:
        doc_ids_to_remove = [
            doc_id for doc_id in document_order 
            if documents[doc_id]["file_name"] == file_name_to_remove
        ]
        for doc_id in doc_ids_to_remove:
            # record position before removal
            if doc_id in document_positions:
                removed_positions[file_name_to_remove] = document_positions[doc_id]
            # remove document
            del documents[doc_id]
            document_order.remove(doc_id)
            # remove from position tracking
            if doc_id in document_positions:
                del document_positions[doc_id]
            removed_files.append(file_name_to_remove)
            print(f"Completely removed document: {file_name_to_remove}")
    
    # If documents were removed, update LLM chat history
    if removed_files and llm_chat_history is not None:
        for removed in removed_files:
            # build deletion info array for replacement
            deletion_block = [
                {
                    "type": "text",
                    "text": f"Document name: {removed}.\nThis document contains unknown pages with text and images.\nThis document was deleted manually by the user and you no longer have access to its contents. It was earlier uploaded by the user but now it is removed and no longer available. You no longer have access to this document's information. However it may be the case that the document was referenced in the chat history, which information has not been removed. The only information about this document that you have is that mentioned in the chat history in its reference. Rest no information is available, you do not have access to its content. User has also notified about at which point this information was deleted in the chat history."
                }
            ]
            internal_notification = {
                "role": "user",
                "content": f"The document: {removed} was deleted at this point in the chat history, you may find references about the document before this in the chathistory, but not after this since it was deleted. You also wont have the document's content in your context now, that was manually removed by me."
            }
            # replace original content block at stored position
            pos = removed_positions.get(removed)
            if pos is not None and pos < len(llm_chat_history):
                llm_chat_history[pos] = {"role": "user", "content": deletion_block}
                llm_chat_history_show[pos] = {"role": "user", "content": deletion_block}
            # append internal notification
            llm_chat_history.append(internal_notification)
            llm_chat_history_show.append(internal_notification)
        print(f"Replaced and appended deletion info for removed documents: {removed_files}")
    
    # Process only new files
    for file in files_to_add:
        doc_id, file_name, success = upload_and_process_document(
            file, mistral_client, documents, document_order, 
            document_positions, chat_position_counter, 
            llm_chat_history, llm_chat_history_show
        )
        
        if success:
            processed_files.append(file_name)
        else:
            failed_files.append(file_name)
    
    # Create system message
    if chat_history is None:
        chat_history = []
    
    status_messages = []
    
    if processed_files:
        if len(processed_files) == 1:
            status_messages.append(f"✅ Added: '{processed_files[0]}'")
        else:
            status_messages.append(f"✅ Added {len(processed_files)} files: {', '.join(processed_files)}")
    
    if removed_files:
        if len(removed_files) == 1:
            status_messages.append(f"🗑️ Removed: '{removed_files[0]}'")
        else:
            status_messages.append(f"🗑️ Removed {len(removed_files)} files: {', '.join(removed_files)}")
    
    if failed_files:
        status_messages.append(f"❌ Failed to process: {', '.join(failed_files)}")
    
    if status_messages:
        system_message = "\n".join(status_messages) + f"\n\nTotal documents: {len(documents)}. Chat history preserved."
        chat_history = chat_history + [{"role": "assistant", "content": system_message}]
    
    # Save updated chat history and create/save LLM payload if documents exist
    save_chat_history(chat_history)
    
    # If we have documents but no LLM chat history yet, create it and save
    if documents and llm_chat_history is None:
        # Create initial LLM payload with all documents
        initial_messages, initial_messages_show, document_positions, chat_position_counter = create_chat_messages_for_llm(
            documents, document_order, document_positions, chat_position_counter
        )
        llm_chat_history = initial_messages.copy()
        llm_chat_history_show = initial_messages_show.copy()
        save_llm_call_payload(llm_chat_history, llm_chat_history_show)
    elif llm_chat_history is not None:
        # Save existing LLM payload
        save_llm_call_payload(llm_chat_history, llm_chat_history_show)
    
    # Always save the structured document info when documents change
    structured_docs_cache = save_docs_structured_info(documents, document_order, structured_docs_cache)
    
    return chat_history, generate_media_viewer(documents, document_order, videos, video_order)

def process_video_upload_wrapper(files, youtube_urls_text, chat_history):
    """
    Wrapper for process_video_upload to handle global variables.
    Automatically generates video descriptions upon upload.
    Now supports multiple YouTube URLs.
    
    Args:
        files: List of uploaded video files
        youtube_urls_text: Text containing YouTube URLs (multiple, separated by newlines)
        chat_history: Current chat history
        
    Returns:
        Updated chat history and video viewer HTML
    """
    global videos, video_order, structured_videos_cache
    
    # Parse multiple YouTube URLs from text
    youtube_urls = parse_youtube_urls_from_text(youtube_urls_text) if youtube_urls_text else []
    
    chat_history, processed_videos, failed_videos, structured_videos_cache = process_video_upload(
        files, youtube_urls, chat_history, videos, video_order, genai_client, structured_videos_cache
    )
    
    save_chat_history(chat_history)
    
    return chat_history, generate_media_viewer(documents, document_order, videos, video_order)

def process_video_upload_and_removal_wrapper(files, youtube_urls_text, chat_history):
    """
    Enhanced wrapper that handles both video uploads and removals.
    Detects when videos are removed from the file upload component and processes accordingly.
    
    Args:
        files: List of uploaded video files (can be None or reduced list)
        youtube_urls_text: Text containing YouTube URLs
        chat_history: Current chat history
        
    Returns:
        Updated chat history and video viewer HTML
    """
    global videos, video_order, structured_videos_cache
    
    # Get current file names from the upload component
    current_files = files if files else []
    current_file_names = set()
    
    for file in current_files:
        if file is not None:
            file_name = os.path.basename(file.name)
            current_file_names.add(file_name)
    
    # Get existing local video files (non-YouTube)
    existing_local_videos = {}
    for video_id in list(video_order):
        if video_id in videos:
            video_data = videos[video_id]
            if video_data["video_type"] == "local":
                existing_local_videos[video_data["file_name"]] = video_id
    
    # Find videos to remove (existing local videos not in current upload)
    videos_to_remove = []
    for existing_file_name, video_id in existing_local_videos.items():
        if existing_file_name not in current_file_names:
            videos_to_remove.append((video_id, existing_file_name))
    
    # Remove videos that are no longer in the upload component
    if videos_to_remove:
        print(f"🗑️ Detected {len(videos_to_remove)} video(s) removed from upload component")
        for video_id, file_name in videos_to_remove:
            print(f"🗑️ Removing video: {file_name} (ID: {video_id})")
            chat_history, videos, video_order, structured_videos_cache = remove_video(
                video_id, chat_history, videos, video_order, structured_videos_cache
            )
        
        # Save after removals
        save_chat_history(chat_history)
        
        # If only removals happened (no new files or YouTube URLs), return early
        if not current_files and not youtube_urls_text:
            return chat_history, generate_media_viewer(documents, document_order, videos, video_order)
    
    # Only process uploads if there are actually new files or YouTube URLs
    if current_files or youtube_urls_text:
        # Parse multiple YouTube URLs from text
        youtube_urls = parse_youtube_urls_from_text(youtube_urls_text) if youtube_urls_text else []
        
        # Only call process_video_upload if we have new content to process
        if current_files or youtube_urls:
            chat_history, processed_videos, failed_videos, structured_videos_cache = process_video_upload(
                files, youtube_urls, chat_history, videos, video_order, genai_client, structured_videos_cache
            )
            save_chat_history(chat_history)
    
    return chat_history, generate_media_viewer(documents, document_order, videos, video_order)

def remove_video_wrapper(video_id, chat_history):
    """
    Wrapper for remove_video to handle global variables.
    
    Args:
        video_id: ID of the video to remove
        chat_history: Current chat history
        
    Returns:
        Updated chat history and video viewer HTML
    """
    global videos, video_order, structured_videos_cache
    
    if video_id and video_id.strip():
        chat_history, videos, video_order, structured_videos_cache = remove_video(
            video_id.strip(), chat_history, videos, video_order, structured_videos_cache
        )
        
        save_chat_history(chat_history)
    
    return chat_history, generate_media_viewer(documents, document_order, videos, video_order)

def process_multiple_youtube_urls_wrapper(urls_text, chat_history):
    """
    Wrapper for processing multiple YouTube URLs at once.
    
    Args:
        urls_text: Text containing multiple YouTube URLs
        chat_history: Current chat history
        
    Returns:
        Updated chat history and video viewer HTML
    """
    return process_video_upload_wrapper(None, urls_text, chat_history)

def update_video_removal_dropdown():
    """
    Update the video removal dropdown with current videos.
    
    Returns:
        Updated dropdown choices
    """
    global videos, video_order
    
    if not videos or not video_order:
        return gr.Dropdown(choices=["No videos to remove"], value="No videos to remove")
    
    choices = ["Select video to remove..."]
    for video_id in video_order:
        if video_id in videos:
            video_data = videos[video_id]
            file_name = video_data["file_name"]
            choices.append(f"{video_id}: {file_name}")
    
    return gr.Dropdown(choices=choices, value="Select video to remove...")

def remove_selected_video_wrapper(selected_video, chat_history):
    """
    Remove the selected video from the dropdown.
    
    Args:
        selected_video: Selected video from dropdown (format: "video_id: filename")
        chat_history: Current chat history
        
    Returns:
        Updated chat history, video viewer HTML, and updated dropdown
    """
    global videos, video_order, structured_videos_cache
    
    if not selected_video or selected_video in ["No videos to remove", "Select video to remove..."]:
        return chat_history, generate_media_viewer(documents, document_order, videos, video_order), update_video_removal_dropdown()
    
    # Extract video_id from the selection (format: "video_id: filename")
    try:
        video_id = selected_video.split(": ")[0]
        
        chat_history, videos, video_order, structured_videos_cache = remove_video(
            video_id, chat_history, videos, video_order, structured_videos_cache
        )
        
        save_chat_history(chat_history)
        
    except Exception as e:
        if chat_history is None:
            chat_history = []
        error_message = f"❌ Error removing video: {str(e)}"
        chat_history = chat_history + [{"role": "assistant", "content": error_message}]
        save_chat_history(chat_history)
    
    # Return updated components
    return (
        chat_history,
        generate_media_viewer(documents, document_order, videos, video_order),
        update_video_removal_dropdown()
    )

def process_audio_input_wrapper(audio_file):
    """
    Wrapper for process_audio_input to handle global variables.
    
    Args:
        audio_file: Recorded audio file
        
    Returns:
        Transcribed text for input box
    """
    return process_audio_input(audio_file, groq_client)

def get_last_response_and_convert_to_speech_wrapper(chat_history):
    """
    Wrapper for get_last_response_and_convert_to_speech to handle global variables.
    
    Args:
        chat_history: Current chat history
        
    Returns:
        Audio file path for Gradio audio component
    """
    return get_last_response_and_convert_to_speech(chat_history, openai_tts_client)

def add_user_and_placeholder_wrapper(message, chat_history):
    """
    Wrapper for add_user_and_placeholder to handle global variables.
    
    Args:
        message: User message
        chat_history: Current chat history
        
    Returns:
        Updated chat history
    """
    return add_user_and_placeholder(message, chat_history)

def stream_assistant_reply_wrapper(message, chat_history):
    """
    Wrapper for stream_assistant_reply to handle global variables.
    
    Args:
        message: User message
        chat_history: Current chat history
        
    Yields:
        Updated chat history
    """
    global llm_chat_history, llm_chat_history_show, document_positions, chat_position_counter
    
    # Create a generator that yields chat history updates
    stream_gen = stream_assistant_reply(
        message, chat_history, documents, document_order, llm_chat_history,
        llm_chat_history_show, document_positions, chat_position_counter, openai_client
    )
    
    # Yield all chat history updates from the generator and capture final result
    final_result = None
    try:
        # Yield all intermediate updates
        while True:
            updated_chat = next(stream_gen)
            yield updated_chat
    except StopIteration as e:
        # When the generator is exhausted, capture the final return value
        final_result = e.value
    
    # Update global variables with the final result
    if final_result:
        final_chat_history, final_llm_chat_history, final_llm_chat_history_show, final_document_positions, final_chat_position_counter = final_result
        
        # Update global variables
        llm_chat_history = final_llm_chat_history
        llm_chat_history_show = final_llm_chat_history_show
        document_positions = final_document_positions
        chat_position_counter = final_chat_position_counter

def clear_chat_wrapper():
    """
    Wrapper for clear_chat to handle global variables.
    
    Returns:
        Empty chat history
    """
    global llm_chat_history, llm_chat_history_show, document_positions, chat_position_counter, structured_docs_cache
    
    chat_history, llm_chat_history, llm_chat_history_show, document_positions, chat_position_counter = clear_chat(
        llm_chat_history, llm_chat_history_show, document_positions, chat_position_counter
    )
    
    # Also update structured document info
    structured_docs_cache = save_docs_structured_info(documents, document_order, structured_docs_cache)
    
    return chat_history

def reset_all_state_wrapper():
    """
    Wrapper for reset_all_state to handle global variables.
    
    Returns:
        Tuple of (empty chat history, empty media viewer)
    """
    global documents, document_order, videos, video_order, llm_chat_history, llm_chat_history_show
    global document_positions, chat_position_counter, structured_docs_cache, structured_videos_cache
    
    documents, document_order, videos, video_order, llm_chat_history, llm_chat_history_show, document_positions, chat_position_counter, structured_docs_cache = reset_all_state(
        documents, document_order, videos, video_order, llm_chat_history, llm_chat_history_show,
        document_positions, chat_position_counter, structured_docs_cache
    )
    
    # Reset video cache as well
    structured_videos_cache = []
    
    return [], generate_media_viewer(documents, document_order, videos, video_order)

# ---------------------------
# Gradio UI Setup
# ---------------------------

css = """
.container {
    max-width: 1400px !important;
    margin: auto;
}
.sidebar {
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    margin-top: 10px;
}
.chatbox {
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    margin-top: 10px;
}
.title {
    text-align: center;
    margin-bottom: 20px;
    color: #2c3e50;
}
.button {
    background-color: #3498db !important;
    color: white !important;
}

/* ── existing JSON classes (unchanged) ─────────────────────────────── */
.json-box   {background:#454545;padding:12px;border-radius:4px;
             font-family:'Fira Code','Consolas',monospace;}
.json-key   {color:#37a3f0;}
.json-string{color:#e98659;}
.json-num   {color:#97e76c;}
.json-bool  {color:#3a73e5;}
.json-null  {color:#db4e49;}
.json-punct {color:#a5d7ea;}

/* ── NEW granular punctuation classes ─────────────────────────────── */
.json-brace      {color:#f1c947;}   /* { } */
.json-bracket    {color:#c49703;}   /* [ ] */
.json-comma      {color:#a5d7ea;}   /* ,   */
.json-colon      {color:#82aae5;}   /* :   */
.json-quote      {color:#7ee7b4;}   /* "   */
.json-esc   {color:#e4e829;}   /* \n  \"  \\  \\uXXXX */

/* Hide the video removal trigger textbox */
.video-removal-trigger {
    display: none !important;
}
"""

# JavaScript for handling video removal
video_removal_js = """
async () => {
    // Set the video removal function on globalThis so HTML onclick can access it
    globalThis.removeVideoClick = (videoId) => {
        if (confirm('Are you sure you want to remove this video?')) {
            // Find the hidden textbox by placeholder
            const hiddenInputs = document.querySelectorAll('textarea[placeholder="remove_video_trigger"], input[placeholder="remove_video_trigger"]');
            
            if (hiddenInputs.length > 0) {
                const input = hiddenInputs[0];
                input.value = videoId;
                
                // Fire events to trigger Gradio
                ['input', 'change', 'blur'].forEach(eventType => {
                    const event = new Event(eventType, { bubbles: true, cancelable: true });
                    input.dispatchEvent(event);
                });
                
                // Focus and blur to simulate interaction
                input.focus();
                setTimeout(() => input.blur(), 10);
                
            } else {
                // Fallback: try to find by class
                const classInputs = document.querySelectorAll('.video-removal-trigger textarea, .video-removal-trigger input');
                if (classInputs.length > 0) {
                    const input = classInputs[0];
                    input.value = videoId;
                    
                    ['input', 'change', 'blur'].forEach(eventType => {
                        const event = new Event(eventType, { bubbles: true, cancelable: true });
                        input.dispatchEvent(event);
                    });
                }
            }
        }
    };
}
"""

with gr.Blocks(title="Multi-Media Chat Assistant", css=css) as demo:
    with gr.Column(elem_classes="container"):
        gr.Markdown("# Multi-Media Chat Assistant", elem_classes="title")
        gr.Markdown("Upload PDF documents and videos to interact with their contents. Documents are processed with OCR and videos are automatically analyzed with AI descriptions.")
        
        with gr.Row():
            # Left sidebar for Media viewer
            with gr.Column(scale=2, elem_classes="sidebar"):
                gr.Markdown("### 📄📹 Media Content Viewer")
                
                # Document uploads
                gr.Markdown("#### Documents")
                file_input = gr.File(label="Upload PDFs", file_types=[".pdf"], file_count="multiple", height=120)
                
                # Video uploads
                gr.Markdown("#### Videos")
                video_input = gr.File(label="Upload Videos", file_types=[".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mkv"], file_count="multiple", height=120)
                
                # Multiple YouTube URLs interface
                gr.Markdown("#### YouTube Videos")
                youtube_urls_input = gr.Textbox(
                    label="YouTube URLs (Multiple)",
                    placeholder="Enter YouTube URLs (one per line):\nhttps://youtube.com/watch?v=...\nhttps://youtube.com/watch?v=...",
                    lines=3,
                    value=""
                )
                with gr.Row():
                    youtube_batch_btn = gr.Button("🎥 Add YouTube Videos", elem_classes="button", scale=1, size="lg")
                
                # Hidden textbox for JavaScript communication (cross buttons)
                remove_video_hidden = gr.Textbox(
                    visible=False,
                    placeholder="remove_video_trigger",
                    elem_id="remove_video_hidden",
                    elem_classes=["video-removal-trigger"],
                    interactive=True
                )

                media_viewer = gr.HTML(label="Media Content", value=generate_media_viewer(documents, document_order, videos, video_order), elem_id="media_viewer")
                
            # Right side for chat interface
            with gr.Column(scale=3, elem_classes="chatbox"):
                gr.Markdown("### Chat with PDF Content")
                chatbot = gr.Chatbot(height=400, type="messages")
                
                # Audio input section
                with gr.Row():
                    with gr.Column(scale=3):
                        msg = gr.Textbox(
                            placeholder="Ask questions about the PDF content...",
                            show_label=False
                        )
                    with gr.Column(scale=1, min_width=120):
                        audio_input = gr.Audio(
                            sources=["microphone"],
                            type="filepath",
                            label="🎤 Voice Input",
                            show_label=False,
                            container=False
                        )
                
                # Audio output section
                audio_output = gr.Audio(
                    label="🔊 AI Response Audio",
                    visible=True,
                    autoplay=True,
                    value=None
                )
                
                with gr.Row():
                    submit_btn = gr.Button("Send", elem_classes="button")
                    tts_btn = gr.Button("🔊 Listen to Last Response", elem_classes="button")
                    clear_btn = gr.Button("Clear Chat", elem_classes="button")
        
        # Set up event handlers for documents
        file_input.change(
            fn=upload_and_process,
            inputs=[file_input, chatbot],
            outputs=[chatbot, media_viewer]
        )
        
        # Set up event handlers for videos
        video_input.change(
            fn=process_video_upload_and_removal_wrapper,
            inputs=[video_input, youtube_urls_input, chatbot],
            outputs=[chatbot, media_viewer]
        )
        
        # Handle multiple YouTube URLs
        youtube_batch_btn.click(
            fn=process_multiple_youtube_urls_wrapper,
            inputs=[youtube_urls_input, chatbot],
            outputs=[chatbot, media_viewer]
        ).then(
            fn=lambda: "",  # Clear the textbox after processing
            outputs=[youtube_urls_input]
        )
        
        # Handle YouTube URLs on Enter
        youtube_urls_input.submit(
            fn=process_multiple_youtube_urls_wrapper,
            inputs=[youtube_urls_input, chatbot],
            outputs=[chatbot, media_viewer]
        ).then(
            fn=lambda: "",  # Clear the textbox after processing
            outputs=[youtube_urls_input]
        )
        
        # Handle video removal from HTML cross buttons (JavaScript triggered)
        remove_video_hidden.change(
            fn=remove_video_wrapper,
            inputs=[remove_video_hidden, chatbot],
            outputs=[chatbot, media_viewer]
        ).then(
            fn=lambda: "",  # Clear the hidden field
            outputs=[remove_video_hidden]
        )
        
        # Chain the "add placeholder" (no spinner) → then "stream reply" (spinner+stream)
        submit_btn.click(
            fn=add_user_and_placeholder_wrapper,
            inputs=[msg, chatbot],
            outputs=[chatbot],
            queue=False
        ).then(
            fn=stream_assistant_reply_wrapper,
            inputs=[msg, chatbot],
            outputs=[chatbot],
            queue=True
        ).then(
            fn=lambda: "",  # clear the textbox after the chain is done
            outputs=[msg]
        )
        
        # Same logic on pressing Enter
        msg.submit(
            fn=add_user_and_placeholder_wrapper,
            inputs=[msg, chatbot],
            outputs=[chatbot],
            queue=False
        ).then(
            fn=stream_assistant_reply_wrapper,
            inputs=[msg, chatbot],
            outputs=[chatbot],
            queue=True
        ).then(
            fn=lambda: "",
            outputs=[msg]
        )
        
        clear_btn.click(
            fn=clear_chat_wrapper,
            outputs=[chatbot]
        )
        
        # ASR: Handle audio input - only put text in input box, don't auto-send
        audio_input.change(
            fn=process_audio_input_wrapper,
            inputs=[audio_input],
            outputs=[msg],
            queue=False
        )
        
        # TTS: Handle text-to-speech for last response
        tts_btn.click(
            fn=get_last_response_and_convert_to_speech_wrapper,
            inputs=[chatbot],
            outputs=[audio_output]
        )
        
        gr.Examples(
            examples=["material/AGV_Task_2023.pdf"],
            inputs=file_input,
        )
    
    # Reset state when interface loads/reloads and initialize JavaScript
    demo.load(
        fn=reset_all_state_wrapper,
        outputs=[chatbot, media_viewer],
        queue=False,
        js=video_removal_js
    )

# Launch the app
if __name__ == "__main__":
    demo.launch(height=800)
