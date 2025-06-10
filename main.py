import dotenv
import os
import gradio as gr
import json
import markdown
import base64
from pathlib import Path
from mistralai import Mistral
from mistralai import DocumentURLChunk, ImageURLChunk, TextChunk
from mistralai.models import OCRResponse
import google.generativeai as genai
from IPython.display import Markdown, display
from openai import OpenAI

def save_llm_call_payload(messages, messages_show):
    """
    Save the LLM call payload to JSON files.
    
    Args:
        messages: Full LLM messages payload
        messages_show: Truncated LLM messages payload for display
    """
    try:
        # Save full payload
        with open("llm_structured_call.json", "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
        
        # Save show payload
        with open("llm_structured_call_show.json", "w", encoding="utf-8") as f:
            json.dump(messages_show, f, indent=2, ensure_ascii=False)
        
        print(f"Saved LLM call payload to JSON files ({len(messages)} messages)")
    except Exception as e:
        print(f"Error saving LLM call payload: {e}")

def save_chat_history(chat_history):
    """
    Save the Gradio chat history to JSON file.
    
    Args:
        chat_history: Current Gradio chat history
    """
    try:
        if chat_history is None:
            chat_history = []
        
        with open("chat_history_gradio.json", "w", encoding="utf-8") as f:
            json.dump(chat_history, f, indent=2, ensure_ascii=False)
        
        print(f"Saved Gradio chat history ({len(chat_history)} messages)")
    except Exception as e:
        print(f"Error saving chat history: {e}")

def load_env(filename=".env"):
    dotenv.load_dotenv()
    env_file = os.getenv("ENV_FILE", filename)
    if os.path.exists(env_file):
        dotenv.load_dotenv(env_file)
    else:
        print(f"Warning: Environment file '{env_file}' not found. Using default environment variables.")

load_env()

gemini_api_key = os.getenv("GEMINI_API_KEY")
mistral_api_key = os.getenv("MISTRAL_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
if not mistral_api_key:
    raise ValueError("MISTRAL_API_KEY is not set in the environment variables.")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY is not set in the environment variables.")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables.")

# Initialize Mistral client
mistral_client = Mistral(api_key=mistral_api_key)

# Initialize OpenAI client for Gemini's OpenAI-compatible endpoint
openai_client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Initialize Groq client for ASR
groq_client = OpenAI(
    api_key=groq_api_key,
    base_url="https://api.groq.com/openai/v1"
)

# Initialize OpenAI client for TTS
openai_tts_client = OpenAI(api_key=openai_api_key)

# Initialize Gemini (keeping this for backward compatibility)
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

# Global variables to store multiple documents content
documents = {}  # Dictionary to store all document data: {doc_id: {content, text, ocr_response, file_name}}
document_order = []  # List to maintain order of uploaded documents
llm_chat_history = None
llm_chat_history_show = None
document_positions = {}  # Track position of each document in chat history: {doc_id: position_index}
chat_position_counter = 0  # Counter to track next position for new documents

# Initialize empty JSON files at startup
def initialize_json_files():
    """Initialize all JSON files as empty at startup."""
    try:
        save_chat_history([])
        save_llm_call_payload([], [])
        print("Initialized all JSON files as empty")
    except Exception as e:
        print(f"Error initializing JSON files: {e}")

# Initialize files at startup
initialize_json_files()

def reset_all_state():
    """Reset all internal state and JSON files when interface loads/reloads."""
    global documents, document_order, llm_chat_history, llm_chat_history_show
    global document_positions, chat_position_counter
    
    # Clear all internal state
    documents.clear()
    document_order.clear()
    llm_chat_history = None
    llm_chat_history_show = None
    document_positions.clear()
    chat_position_counter = 0
    
    # Clear all JSON files
    initialize_json_files()
    
    print("Reset all state and JSON files on interface reload")

def replace_images_in_markdown(markdown_str: str, images_dict: dict) -> str:
    """
    Replace image placeholders in markdown with base64-encoded images.

    Args:
        markdown_str: Markdown text containing image placeholders
        images_dict: Dictionary mapping image IDs to base64 strings

    Returns:
        Markdown text with images replaced by base64 data
    """
    for img_name, base64_str in images_dict.items():
        markdown_str = markdown_str.replace(
            f"![{img_name}]({img_name})", f"![{img_name}]({base64_str})"
        )
    return markdown_str

def get_combined_markdown(ocr_response: OCRResponse) -> str:
    """
    Combine OCR text and images into a single markdown document.

    Args:
        ocr_response: Response from OCR processing containing text and images

    Returns:
        Combined markdown string with embedded images
    """
    markdowns: list[str] = []
    # Extract images from page
    for page in ocr_response.pages:
        image_data = {}
        for img in page.images:
            image_data[img.id] = img.image_base64
        # Replace image placeholders with actual images
        markdowns.append(replace_images_in_markdown(page.markdown, image_data))

    return "\n\n".join(markdowns)

def markdown_to_html(md_text):
    """
    Convert markdown text to HTML.
    
    Args:
        md_text: Markdown text
        
    Returns:
        HTML representation of the markdown
    """
    # Convert markdown to HTML
    html = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
    
    # Wrap in a styled div for scrolling with black background
    styled_html = f"""
    <div style="
        height: 600px;
        overflow-y: auto;
        padding: 20px;
        border: 1px solid #444;
        border-radius: 8px;
        background-color: black;
        color: #e0e0e0;
        font-family: Arial, sans-serif;
        line-height: 1.6;
    ">
        <style>
            /* Additional styles for elements inside the black background */
            h1, h2, h3, h4, h5, h6 {{ color: #3498db; }}
            a {{ color: #2ecc71; }}
            code {{ background-color: #333; padding: 2px 4px; border-radius: 3px; }}
            pre {{ background-color: #222; padding: 10px; border-radius: 5px; overflow-x: auto; }}
            img {{ max-width: 100%; border: 1px solid #555; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #444; padding: 8px; text-align: left; }}
            th {{ background-color: #222; }}
        </style>
        {html}
    </div>
    """
    return styled_html

def extract_text_from_markdown(md_text):
    """
    Extract plain text from markdown, removing image references.
    
    Args:
        md_text: Markdown text
        
    Returns:
        Plain text without image references
    """
    import re
    # Remove image references (![alt](url) pattern)
    text = re.sub(r'!\[.*?\]\(.*?\)', '[IMAGE]', md_text)
    
    # Remove other markdown formatting if needed
    text = re.sub(r'#{1,6}\s+', '', text)  # Remove headings
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)  # Remove italic
    text = re.sub(r'`(.*?)`', r'\1', text)  # Remove inline code
    
    return text

def extract_text_from_ocr_response(ocr_response):
    """
    Extract plain text from OCR response, replacing images with [IMAGE] placeholders.
    
    Args:
        ocr_response: OCR response object
        
    Returns:
        Plain text with image placeholders
    """
    text_parts = []
    
    for page in ocr_response.pages:
        # Get the markdown without images
        page_text = extract_text_from_markdown(page.markdown)
        text_parts.append(page_text)
    
    return "\n\n".join(text_parts)

def generate_document_buttons():
    """
    Generate HTML interface showing all uploaded documents.
    
    Returns:
        HTML string with document list and viewing interface
    """
    if not documents:
        return "<div style='padding: 20px; background-color: black; color: #e0e0e0; border-radius: 8px;'>No documents uploaded yet. Please upload PDF files.</div>"
    
    # Create document selector interface
    buttons_html = f"""
    <div style="background-color: black; color: #e0e0e0; padding: 20px; border-radius: 8px; height: 600px; overflow-y: auto;">
        <h3 style="color: #3498db; margin-bottom: 15px;">Uploaded Documents ({len(documents)}):</h3>
    """
    
    for i, doc_id in enumerate(document_order):
        doc_data = documents[doc_id]
        file_name = doc_data["file_name"]
        page_count = len(doc_data["ocr_response"].pages)
        
        # Create a preview of the content (first 200 characters)
        content_preview = doc_data["text"][:200] + "..." if len(doc_data["text"]) > 200 else doc_data["text"]
        
        buttons_html += f"""
        <div style="border: 1px solid #444; border-radius: 5px; margin-bottom: 15px; background-color: #1a1a1a;">
            <div style="padding: 15px; border-bottom: 1px solid #444;">
                <h4 style="color: #3498db; margin: 0 0 5px 0;">📄 {file_name}</h4>
                <p style="color: #888; margin: 0; font-size: 12px;">Document {i} • {page_count} pages</p>
                <p style="color: #ccc; margin: 5px 0 0 0; font-size: 11px; font-style: italic;">Preview: {content_preview}</p>
            </div>
            <div style="padding: 10px 15px;">
                <details>
                    <summary style="color: #3498db; cursor: pointer; font-size: 13px;">View Full Content</summary>
                    <div style="margin-top: 10px; max-height: 400px; overflow-y: auto; background-color: #0a0a0a; padding: 10px; border-radius: 3px;">
                        {markdown_to_html(doc_data["content"]).replace('height: 600px;', 'height: auto;')}
                    </div>
                </details>
            </div>
        </div>
        """
    
    buttons_html += """
        <div style="border-top: 1px solid #444; padding-top: 15px; margin-top: 15px;">
            <p style="color: #888; font-size: 12px; margin: 0;">
                💡 All documents are automatically included when chatting with the AI.
            </p>
        </div>
    </div>
    """
    
    return buttons_html

def view_document(doc_id):
    """
    Display the content of a specific document.
    
    Args:
        doc_id: Document ID to display
        
    Returns:
        HTML content of the selected document
    """
    if doc_id not in documents:
        return "<div style='padding: 20px; background-color: black; color: red; border-radius: 8px;'>Document not found.</div>"
    
    doc_data = documents[doc_id]
    return markdown_to_html(doc_data["content"])

def create_document_content_block(doc_id, doc_index):
    """
    Create document content block for a specific document.
    
    Args:
        doc_id: Document ID
        doc_index: Document index for naming scheme
        
    Returns:
        Tuple of (user_content, user_content_show) for this document
    """
    if doc_id not in documents:
        # Document was deleted
        file_name = f"[DELETED DOCUMENT - was at position {doc_index}]"
        return [{
            "type": "text",
            "text": f"Deleted Document name: {file_name}.\nNote: User had initially uploaded this document but later removed (deleted) it from the your context manually. You may find some information about this document in the chat history, which is left unchanged, but you do not explicitly have context to this document now, since it is deleted."
        }], [{
            "type": "text", 
            "text": f"Deleted Document name: {file_name}.\nNote: User had initially uploaded this document but later removed (deleted) it from the your context manually. You may find some information about this document in the chat history, which is left unchanged, but you do not explicitly have context to this document now, since it is deleted."
        }]
    
    doc_data = documents[doc_id]
    ocr_response = doc_data["ocr_response"]
    file_name = doc_data["file_name"]
    
    user_content = []
    user_content_show = []
    
    # Add document info
    page_count = len(ocr_response.pages)
    doc_info = {
        "type": "text",
        "text": f"Document name: {file_name}.\nThis document contains {page_count} pages with text and images."
    }
    user_content.append(doc_info)
    user_content_show.append(doc_info)

    # Process each page
    for page_index, page in enumerate(ocr_response.pages):
        page_markdown_str = page.markdown
        image_data = {}

        user_content.append({
            "type": "text",
            "text": f"\n\n\n{'-'*20}\n## Document {doc_index} - Page {page_index + 1}:-\n\n"
        })

        user_content_show.append({
            "type": "text",
            "text": f"\n\n\n{'-'*20}\n## Document {doc_index} - Page {page_index + 1}:-\n\n"
        })

        for img in page.images:
            image_data[img.id] = img.image_base64
            
        for img_name, base64_str in image_data.items():
            pos = page_markdown_str.find(f"![{img_name}]({img_name})")
            txt = page_markdown_str[:pos]
            page_markdown_str = page_markdown_str[pos+len(f"![{img_name}]({img_name})"):]

            if len(txt) > 0:
                user_content.append({
                    "type": "text",
                    "text": txt + "\n\n"
                })

                user_content_show.append({
                    "type": "text",
                    "text": txt[:500] + "...\n\n" if len(txt) > 500 else txt + "\n\n"
                })

            # Use new naming scheme: doc-0-page-0-image-0
            new_img_name = f"doc-{doc_index}-page-{page_index}-{img_name}"
            
            user_content.append({
                "type": "text",
                "text": f"Attaching an image in the page. Image name: {new_img_name}.\n\n"
            })

            user_content_show.append({
                "type": "text",
                "text": f"Attaching an image in the page. Image name: {new_img_name}.\n\n"
            })

            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"{base64_str}"
                }
            })

            user_content_show.append({
                "type": "image_url",
                "image_url": {
                    "url": f"{base64_str[:50]}..."
                }
            })
        
        if len(page_markdown_str) > 0:
            user_content.append({
                "type": "text",
                "text": f"Remaining text in the page: {page_markdown_str}\n\n"
            })
            user_content_show.append({
                "type": "text",
                "text": f"Remaining text in the page: {page_markdown_str[:500]}\n\n" if len(page_markdown_str) > 500 else f"Remaining text in the page: {page_markdown_str}\n\n"
            })
    
    return user_content, user_content_show

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
    global document_positions, chat_position_counter
    
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
    
    # Handle document removals (mark as deleted but keep chronological position)
    for file_name_to_remove in files_to_remove:
        doc_ids_to_remove = [doc_id for doc_id in document_order 
                            if documents[doc_id]["file_name"] == file_name_to_remove]
        for doc_id in doc_ids_to_remove:
            # Update the document block in chat history to show it's deleted
            if llm_chat_history is not None and doc_id in document_positions:
                position = document_positions[doc_id]
                doc_index = document_order.index(doc_id)
                
                # Create deleted content block but keep the original filename for reference
                deleted_content = [{
                    "type": "text",
                    "text": f"Document name: {documents[doc_id]['file_name']}.\nNote: User had initially uploaded this document but later removed (deleted) it from the your context manually. You may find some information about this document in the chat history, which is left unchanged, but you do not explicitly have context to this document now, since it is deleted."
                }]
                deleted_content_show = deleted_content.copy()
                
                # Update the chat history at the stored position
                if position < len(llm_chat_history):
                    llm_chat_history[position]["content"] = deleted_content
                if position < len(llm_chat_history_show):
                    llm_chat_history_show[position]["content"] = deleted_content_show
            
            del documents[doc_id]
            document_order.remove(doc_id)
            removed_files.append(file_name_to_remove)
            print(f"Removed document: {file_name_to_remove}")
    
    # Process only new files
    for file in files_to_add:
        try:
            pdf_file = Path(file.name)
            file_name = pdf_file.name
            
            print(f"\n\nProcessing NEW PDF file: {file_name}\n")
            
            # Upload PDF file to Mistral's OCR service
            uploaded_file = mistral_client.files.upload(
                file={
                    "file_name": pdf_file.stem,
                    "content": pdf_file.read_bytes(),
                },
                purpose="ocr",
            )
            
            # Get URL for the uploaded file
            signed_url = mistral_client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)
            
            # Process PDF with OCR, including embedded images
            pdf_response = mistral_client.ocr.process(
                document=DocumentURLChunk(document_url=signed_url.url),
                model="mistral-ocr-latest",
                include_image_base64=True
            )
            
            # Generate unique document ID
            doc_id = f"doc_{len(documents)}"
            while doc_id in documents:
                doc_id = f"doc_{len(documents) + len(processed_files) + 1}"
            
            # Get combined markdown with images
            markdown_content = get_combined_markdown(pdf_response)
            
            # Extract plain text for the LLM
            plain_text = extract_text_from_ocr_response(pdf_response)
            
            # Store document data
            documents[doc_id] = {
                "file_name": file_name,
                "content": markdown_content,
                "text": plain_text,
                "ocr_response": pdf_response
            }
            
            # Add to order list
            document_order.append(doc_id)
            
            # If we have existing chat history, append new document at the END (chronological order)
            if llm_chat_history is not None:
                doc_index = len(document_order) - 1  # Current index
                new_doc_content, new_doc_content_show = create_document_content_block(doc_id, doc_index)
                
                # Simply append at the end to maintain chronological order
                llm_chat_history.append({"role": "user", "content": new_doc_content})
                llm_chat_history_show.append({"role": "user", "content": new_doc_content_show})
                
                # Store position for new document
                document_positions[doc_id] = len(llm_chat_history) - 1
            else:
                # Mark position for when chat history is created
                document_positions[doc_id] = chat_position_counter
                chat_position_counter += 1
            
            processed_files.append(file_name)
            
        except Exception as e:
            print(f"Error processing {file.name}: {str(e)}")
            failed_files.append(file.name)
    
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
        initial_messages, initial_messages_show = create_chat_messages_for_llm()
        llm_chat_history = initial_messages.copy()
        llm_chat_history_show = initial_messages_show.copy()
        save_llm_call_payload(llm_chat_history, llm_chat_history_show)
    elif llm_chat_history is not None:
        # Save existing LLM payload
        save_llm_call_payload(llm_chat_history, llm_chat_history_show)
    
    return chat_history, generate_document_buttons()

# ---------------------------
# ASR and TTS Functions
# ---------------------------

def transcribe_audio(audio_file):
    """
    Transcribe audio using Groq's Whisper-large-v3 model.
    
    Args:
        audio_file: Audio file path or file object
        
    Returns:
        Transcribed text string
    """
    try:
        if audio_file is None:
            return ""
        
        print(f"Transcribing audio file: {audio_file}")
        
        # Open the audio file
        with open(audio_file, "rb") as file:
            transcription = groq_client.audio.transcriptions.create(
                file=file,
                model="whisper-large-v3",
                response_format="text"
            )
        
        print(f"Transcription result: {transcription}")
        return transcription
        
    except Exception as e:
        print(f"Error in ASR: {e}")
        return f"Error transcribing audio: {str(e)}"

def text_to_speech(text):
    """
    Convert text to speech using OpenAI's gpt-4o-mini-tts model.
    
    Args:
        text: Text to convert to speech
        
    Returns:
        Audio bytes in memory or None if error
    """
    try:
        if not text or len(text.strip()) == 0:
            return None
            
        print(f"Converting text to speech: {text[:100]}...")
        
        # Create TTS request and store in memory
        response = openai_tts_client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",   # You can change this to nova, echo, fable, onyx, or shimmer
            input=text,
            response_format="mp3"
        )
        
        # Return the audio content as bytes
        audio_bytes = response.content
        print(f"TTS audio generated in memory ({len(audio_bytes)} bytes)")
        return audio_bytes
        
    except Exception as e:
        print(f"Error in TTS: {e}")
        return None

def process_audio_input(audio_file):
    """
    Process audio input through ASR and put text in input box.
    
    Args:
        audio_file: Recorded audio file
        
    Returns:
        Transcribed text for input box
    """
    if audio_file is None:
        return ""
    
    # Transcribe the audio
    transcribed_text = transcribe_audio(audio_file)
    
    if transcribed_text and not transcribed_text.startswith("Error"):
        return f"🎤 {transcribed_text}"
    else:
        return ""

def create_chat_messages_for_llm(messages=None):
    """
    Create initial chat messages with all document contents for the LLM.
    Only used when starting a new conversation - thereafter we use preserved history.
    
    Returns:
        A list of message objects with text and images from all documents
    """
    global documents, document_order, document_positions, chat_position_counter
    
    if not documents:
        return [{"role": "user", "content": "No document content available."}], [{"role": "user", "content": "No document content available."}]
    
    # Start with a system message
    messages = [
        {"role": "system", "content": "You are an assistant that helps users understand multiple document contents. The documents have been processed with OCR and contain both text and images."}
    ]
    messages_show = [
        {"role": "system", "content": "You are an assistant that helps users understand multiple document contents. The documents have been processed with OCR and contain both text and images."}
    ]
    
    # Add each document as a separate user message block
    for doc_index, doc_id in enumerate(document_order):
        doc_content, doc_content_show = create_document_content_block(doc_id, doc_index)
        
        messages.append({"role": "user", "content": doc_content})
        messages_show.append({"role": "user", "content": doc_content_show})
        
        # Store position for this document
        document_positions[doc_id] = len(messages) - 1
    
    # Add documents end marker
    end_marker = [{
        "type": "text",
        "text": f"{'-'*20}DOCUMENTS END{'-'*20}\n{'-'*50}\n\n\n"
    }]
    
    messages.append({"role": "user", "content": end_marker})
    messages_show.append({"role": "user", "content": end_marker})
    
    # Update position counter
    chat_position_counter = len(messages)

    return messages, messages_show

# ---------------------------
# NEW FUNCTION #1: Add user + placeholder (synchronous, no spinner)
# ---------------------------
def add_user_and_placeholder(message, chat_history):
    """
    Immediately append the user's message and a placeholder ('...') for the assistant,
    so the user sees their own prompt and an empty assistant bubble right away.
    """
    global llm_chat_history, llm_chat_history_show
    
    # If there's no chat_history, start a fresh list
    if chat_history is None:
        chat_history = []
    
    # Append user message
    chat_history.append({"role": "user", "content": message})
    # Append a placeholder assistant message (we'll replace '...' as we stream)
    chat_history.append({"role": "assistant", "content": "..."})

    # Save chat history after user query is added
    save_chat_history(chat_history)

    # We do NOT touch llm_chat_history here; that will be updated inside the streaming function.
    return chat_history

# ---------------------------
# EXISTING STREAMING FUNCTION, RENAMED for clarity:
#    It now assumes the last assistant bubble is already in place (i.e. '...')
#    and its job is just to replace that placeholder piece by piece.
# ---------------------------
def stream_assistant_reply(message, chat_history):
    """
    Streaming function that replaces the placeholder '...' with actual tokens from Gemini.
    Yields updated chat_history on each chunk. Keeps spinner until first chunk arrives.
    """
    global documents, llm_chat_history, llm_chat_history_show

    # If no documents are uploaded, just replace the placeholder with an error message
    if not documents:
        response_text = "Please upload a PDF document first."
        if chat_history is None:
            chat_history = []
        # We assume add_user_and_placeholder already put user+ '...' in chat_history
        # Overwrite that '...' with the error
        chat_history[-1]["content"] = response_text
        yield chat_history
        return

    try:
        # Build or retrieve the LLM context messages
        if llm_chat_history is None:
            document_messages, document_messages_show = create_chat_messages_for_llm(llm_chat_history)
        else:
            document_messages, document_messages_show = llm_chat_history, llm_chat_history_show

        user_message = f"# User question:\n"
        user_message += message if message is not None else "No message provided."

        # Append the user's new question to the context
        document_messages.append({"role": "user", "content": user_message})
        document_messages_show.append({"role": "user", "content": user_message[:500] + "..." 
                                      if len(user_message) > 500 else user_message})

        print(f"Sending {len(document_messages)} messages to Gemini\n")
        print(f"Message to Gemini:\n{json.dumps(document_messages_show, indent=4)}\n\n")
        # print(f"Message to Gemini:\n{json.dumps(document_messages, indent=4)}\n\n")

        # Prepare streaming call (this returns a generator-like object immediately)
        stream_response = openai_client.chat.completions.create(
            model="gemini-2.5-flash-preview-05-20",
            messages=document_messages,
            max_tokens=8192,
            temperature=1,
            stream=True
        )

        print("Streaming response from Gemini...\n\n")

        # At this point, we have already rendered the chat bubbles (thanks to add_user_and_placeholder),
        # so we do NOT append a new user/assistant. We only replace chat_history[-1] on each chunk.

        partial_response = ""
        first_chunk = True

        print("Gemini response:")
        for chunk in stream_response:
            if hasattr(chunk, "choices") and chunk.choices:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    partial_response += delta.content
                    print(delta.content, end='', flush=True)  # Print the chunk to console
                    # Replace the placeholder or previously appended text
                    chat_history[-1]["content"] = partial_response

                    if first_chunk:
                        # Now that we have the FIRST chunk, we yield to hide the spinner
                        yield chat_history
                        first_chunk = False
                    else:
                        # Subsequent chunks—just keep yielding updated chat
                        yield chat_history

        # Once streaming is complete, append the full assistant response into LLM context
        full_assistant_message = chat_history[-1]["content"]
        document_messages.append({"role": "assistant", "content": full_assistant_message})
        document_messages_show.append({
            "role": "assistant",
            "content": full_assistant_message[:500] + "..." 
                       if len(full_assistant_message) > 500 else full_assistant_message
        })

        # Persist chat context for next time
        llm_chat_history = document_messages.copy()
        llm_chat_history_show = document_messages_show.copy()
        
        # Save updated chat history and LLM payload after response
        save_chat_history(chat_history)
        save_llm_call_payload(llm_chat_history, llm_chat_history_show)

    except Exception as e:
        error_message = f"Error generating response: {str(e)}"
        print(f"Error details: {e}")
        # Overwrite placeholder with error
        chat_history[-1]["content"] = error_message
        
        # Save chat history even on error
        save_chat_history(chat_history)
        
        yield chat_history

# ---------------------------
# Rest of your Gradio UI wiring, unchanged except for event binding
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
"""

with gr.Blocks(title="Multi-Document PDF Chat Assistant", css=css) as demo:
    with gr.Column(elem_classes="container"):
        gr.Markdown("# Multi-Document PDF Chat Assistant", elem_classes="title")
        gr.Markdown("Upload multiple PDF files to chat with their contents. Each document will be processed and all content will be available for chatting.")
        
        with gr.Row():
            # Left sidebar for PDF viewer
            with gr.Column(scale=2, elem_classes="sidebar"):
                gr.Markdown("### PDF Content Viewer")
                file_input = gr.File(label="Upload PDF", file_types=[".pdf"], file_count="multiple")
                pdf_viewer = gr.HTML(label="Document Content", value=generate_document_buttons())
            
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
        
        # Set up event handlers
        file_input.change(
            fn=upload_and_process,
            inputs=[file_input, chatbot],
            outputs=[chatbot, pdf_viewer]
        )
        
        # Chain the “add placeholder” (no spinner) → then “stream reply” (spinner+stream)
        submit_btn.click(
            fn=add_user_and_placeholder,
            inputs=[msg, chatbot],
            outputs=[chatbot],
            queue=False
        ).then(
            fn=stream_assistant_reply,
            inputs=[msg, chatbot],
            outputs=[chatbot],
            queue=True
        ).then(
            fn=lambda: "",  # clear the textbox after the chain is done
            outputs=[msg]
        )
        
        # Same logic on pressing Enter
        msg.submit(
            fn=add_user_and_placeholder,
            inputs=[msg, chatbot],
            outputs=[chatbot],
            queue=False
        ).then(
            fn=stream_assistant_reply,
            inputs=[msg, chatbot],
            outputs=[chatbot],
            queue=True
        ).then(
            fn=lambda: "",
            outputs=[msg]
        )
        
        def clear_chat():
            global llm_chat_history, llm_chat_history_show, document_positions, chat_position_counter
            llm_chat_history = None
            llm_chat_history_show = None
            document_positions = {}
            chat_position_counter = 0
            
            # Save cleared state to JSON files
            save_chat_history([])
            save_llm_call_payload([], [])
            
            return []

        clear_btn.click(
            fn=clear_chat,
            outputs=[chatbot]
        )
        
        # ASR: Handle audio input - only put text in input box, don't auto-send
        audio_input.change(
            fn=process_audio_input,
            inputs=[audio_input],
            outputs=[msg],
            queue=False
        )
        
        # TTS: Handle text-to-speech for last response
        def get_last_response_and_convert_to_speech(chat_history):
            if chat_history and len(chat_history) > 0:
                # Get the last assistant message
                for msg in reversed(chat_history):
                    if msg["role"] == "assistant" and msg["content"] not in ["...", ""]:
                        # Convert to speech
                        audio_bytes = text_to_speech(msg["content"])
                        if audio_bytes:
                            # Create a temporary file for Gradio to display
                            import tempfile
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                                temp_file.write(audio_bytes)
                                temp_file_path = temp_file.name
                            return temp_file_path, gr.update(visible=True)
                        else:
                            return None, gr.update(visible=False)
            return None, gr.update(visible=False)
        
        tts_btn.click(
            fn=get_last_response_and_convert_to_speech,
            inputs=[chatbot],
            outputs=[audio_output, audio_output]
        )
        
        gr.Examples(
            examples=["AGV_Task_2023.pdf"],
            inputs=file_input,
        )
    
    # Reset state when interface loads/reloads
    demo.load(
        fn=lambda: (reset_all_state(), [], generate_document_buttons()),
        outputs=[chatbot, pdf_viewer],
        queue=False
    )

# Launch the app
if __name__ == "__main__":
    demo.launch(height=800)
