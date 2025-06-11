import dotenv
import os
import gradio as gr
import json
import markdown
import base64
import re
import shutil
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

def generate_docs_structured_info():
    """
    Generate structured document information according to the JSON schema.
    Only includes available documents (deleted documents are completely removed).
    
    Returns:
        List of document information dictionaries matching the schema
    """
    global documents, document_order
    
    structured_docs = []
    
    for doc_index, doc_id in enumerate(document_order):
        if doc_id in documents:
            # Document is available - add it to the structured info
            doc_data = documents[doc_id]
            ocr_response = doc_data["ocr_response"]
            
            # Build document content
            document_content = []
            
            for page_index, page in enumerate(ocr_response.pages):
                # Extract page markdown content and replace image references with XML tags
                page_markdown = page.markdown
                
                # Collect images for this page
                page_images = []
                image_data = {}
                
                for img in page.images:
                    image_data[img.id] = img.image_base64
                
                # Replace image references in markdown with XML tags and collect image info
                img_id_counter = 0
                for img_name, base64_str in image_data.items():
                    # Create XML tag format: <doc-{doc_index}-page-{page_index}-img-{img_id}>
                    xml_tag = f"<doc-{doc_index}-page-{page_index}-img-{img_id_counter}>"
                    
                    # Replace the markdown image reference with XML tag
                    page_markdown = page_markdown.replace(
                        f"![{img_name}]({img_name})", 
                        xml_tag
                    )
                    
                    # Add to page images
                    page_images.append({
                        "image_id": img_id_counter,
                        "image_tag": f"doc-{doc_index}-page-{page_index}-img-{img_id_counter}",
                        "image_base64_data": base64_str
                    })
                    
                    img_id_counter += 1
                
                # Build page structure
                page_info = {
                    "page_num": page_index,
                    "page_markdown_content": {
                        "content_type": "text",
                        "content": page_markdown
                    },
                    "page_image_content": page_images
                }
                
                document_content.append(page_info)
            
            # Build document structure
            doc_info = {
                "document_name": doc_data["file_name"],
                "document_id": doc_index,
                "document_info_available": 1,
                "document_content": document_content
            }
            
            structured_docs.append(doc_info)
        # Note: Deleted documents are completely skipped - not included in the schema
    
    return structured_docs

def save_docs_structured_info():
    """
    Save the structured document information to docs_structured_info.json file and update in-memory cache.
    """
    global structured_docs_cache
    
    try:
        structured_docs = generate_docs_structured_info()
        
        # Update in-memory cache
        structured_docs_cache = structured_docs.copy()
        
        # Save to file
        with open("docs_structured_info.json", "w", encoding="utf-8") as f:
            json.dump(structured_docs, f, indent=2, ensure_ascii=False)
        
        print(f"Saved structured document info to docs_structured_info.json and updated cache ({len(structured_docs)} documents)")
    except Exception as e:
        print(f"Error saving structured document info: {e}")

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

# Initialize empty JSON files at startup
def initialize_json_files():
    """Initialize all JSON files as empty at startup."""
    try:
        save_chat_history([])
        save_llm_call_payload([], [])
        save_docs_structured_info()  # Initialize the new structured docs file
        print("Initialized all JSON files as empty")
    except Exception as e:
        print(f"Error initializing JSON files: {e}")

# Initialize files at startup
initialize_json_files()

def reset_all_state():
    """Reset all internal state and JSON files when interface loads/reloads."""
    global documents, document_order, videos, video_order, llm_chat_history, llm_chat_history_show
    global document_positions, chat_position_counter, structured_docs_cache
    
    # Clear all internal state
    documents.clear()
    document_order.clear()
    videos.clear()
    video_order.clear()
    llm_chat_history = None
    llm_chat_history_show = None
    document_positions.clear()
    chat_position_counter = 0
    structured_docs_cache.clear()  # Clear the structured documents cache
    
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
    # Note: This function should only be called for existing documents
    # Deleted documents are handled by completely removing them from document_order
    if doc_id not in documents:
        # This should not happen in normal operation with the new deletion logic
        return [], []
    
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

# ---------------------------
# Video Processing Functions
# ---------------------------

def extract_youtube_id(url):
    """
    Extract YouTube video ID from various YouTube URL formats.
    
    Args:
        url: YouTube URL string
        
    Returns:
        Video ID string or None if not a valid YouTube URL
    """
    youtube_regex = re.compile(
        r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    )
    match = youtube_regex.search(url)
    return match.group(1) if match else None

def is_youtube_url(url):
    """Check if a URL is a YouTube URL."""
    return extract_youtube_id(url) is not None

def process_video_upload(files, youtube_url, chat_history):
    """
    Process video uploads (both file uploads and YouTube URLs).
    Keeps videos in memory without saving to disk.
    
    Args:
        files: List of uploaded video files
        youtube_url: YouTube URL string (if provided)
        chat_history: Current chat history
        
    Returns:
        Updated chat history and video viewer HTML
    """
    global videos, video_order
    
    processed_videos = []
    failed_videos = []
    
    # Get existing video names/urls to prevent duplicates
    existing_video_names = [videos[vid_id]["file_name"] for vid_id in video_order]
    existing_youtube_ids = [videos[vid_id].get("youtube_id") for vid_id in video_order if videos[vid_id]["video_type"] == "youtube"]
    
    # Handle video file uploads
    if files is not None:
        if not isinstance(files, list):
            files = [files]
        
        for file in files:
            if file is None:
                continue
                
            try:
                file_path = Path(file.name)
                file_name = file_path.name
                file_ext = file_path.suffix.lower()
                
                # Check if video already exists
                if file_name in existing_video_names:
                    print(f"Video {file_name} already exists, skipping...")
                    continue
                
                # Check if it's a supported video format
                supported_formats = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']
                if file_ext not in supported_formats:
                    failed_videos.append(f"{file_name} (unsupported format)")
                    continue
                
                print(f"\n\nProcessing video file: {file_name}\n")
                
                # Generate unique video ID
                video_id = f"video_{len(videos)}"
                while video_id in videos:
                    video_id = f"video_{len(videos) + len(processed_videos) + 1}"
                
                # Store video data with the original file path (Gradio will handle it)
                videos[video_id] = {
                    "file_name": file_name,
                    "file_path": file.name,  # Keep original temp file path
                    "video_type": "local",
                    "url": None
                }
                
                video_order.append(video_id)
                processed_videos.append(file_name)
                
            except Exception as e:
                print(f"Error processing video {file.name}: {str(e)}")
                failed_videos.append(file.name)
    
    # Handle YouTube URL
    if youtube_url and youtube_url.strip():
        try:
            youtube_url = youtube_url.strip()
            video_id_yt = extract_youtube_id(youtube_url)
            
            if video_id_yt:
                # Check if YouTube video already exists
                if video_id_yt in existing_youtube_ids:
                    print(f"YouTube video {video_id_yt} already exists, skipping...")
                else:
                    print(f"\n\nProcessing YouTube URL: {youtube_url}\n")
                    
                    # Generate unique video ID
                    video_id = f"video_{len(videos)}"
                    while video_id in videos:
                        video_id = f"video_{len(videos) + len(processed_videos) + 1}"
                    
                    # Store video data
                    videos[video_id] = {
                        "file_name": f"YouTube Video ({video_id_yt})",
                        "file_path": None,
                        "video_type": "youtube",
                        "url": youtube_url,
                        "youtube_id": video_id_yt
                    }
                    
                    video_order.append(video_id)
                    processed_videos.append(f"YouTube: {video_id_yt}")
            else:
                failed_videos.append("Invalid YouTube URL")
                
        except Exception as e:
            print(f"Error processing YouTube URL: {str(e)}")
            failed_videos.append("YouTube URL processing failed")
    
    # Create system message only if there are changes
    if chat_history is None:
        chat_history = []
    
    status_messages = []
    
    if processed_videos:
        if len(processed_videos) == 1:
            status_messages.append(f"🎥 Added video: '{processed_videos[0]}'")
        else:
            status_messages.append(f"🎥 Added {len(processed_videos)} videos: {', '.join(processed_videos)}")
    
    if failed_videos:
        status_messages.append(f"❌ Failed to process videos: {', '.join(failed_videos)}")
    
    if status_messages:
        system_message = "\n".join(status_messages) + f"\n\nTotal videos: {len(videos)}. Videos are for viewing only and not included in AI chat context yet."
        chat_history = chat_history + [{"role": "assistant", "content": system_message}]
    
    save_chat_history(chat_history)
    
    return chat_history, generate_media_viewer()

def generate_media_viewer():
    """
    Generate HTML interface showing all uploaded documents and videos.
    
    Returns:
        HTML string with media list and viewing interface
    """
    total_items = len(documents) + len(videos)
    
    if total_items == 0:
        return "<div style='padding: 20px; background-color: black; color: #e0e0e0; border-radius: 8px;'>No documents or videos uploaded yet.</div>"
    
    # Create media viewer interface
    viewer_html = f"""
    <div style="background-color: black; color: #e0e0e0; padding: 20px; border-radius: 8px; height: 600px; overflow-y: auto;">
        <h3 style="color: #3498db; margin-bottom: 15px;">Uploaded Media ({total_items} items):</h3>
    """
    
    # Show documents first
    if documents:
        viewer_html += f"""
        <h4 style="color: #2ecc71; margin: 15px 0 10px 0;">📄 Documents ({len(documents)}):</h4>
        """
        
        for i, doc_id in enumerate(document_order):
            doc_data = documents[doc_id]
            file_name = doc_data["file_name"]
            page_count = len(doc_data["ocr_response"].pages)
            
            # Create a preview of the content (first 150 characters)
            content_preview = doc_data["text"][:150] + "..." if len(doc_data["text"]) > 150 else doc_data["text"]
            
            viewer_html += f"""
            <div style="border: 1px solid #444; border-radius: 5px; margin-bottom: 10px; background-color: #1a1a1a;">
                <div style="padding: 12px; border-bottom: 1px solid #444;">
                    <h5 style="color: #3498db; margin: 0 0 3px 0;">📄 {file_name}</h5>
                    <p style="color: #888; margin: 0; font-size: 11px;">{page_count} pages • Preview: {content_preview}</p>
                </div>
                <div style="padding: 8px 12px;">
                    <details>
                        <summary style="color: #3498db; cursor: pointer; font-size: 12px;">View Full Content</summary>
                        <div style="margin-top: 8px; max-height: 300px; overflow-y: auto; background-color: #0a0a0a; padding: 8px; border-radius: 3px;">
                            {markdown_to_html(doc_data["content"]).replace('height: 600px;', 'height: auto;')}
                        </div>
                    </details>
                </div>
            </div>
            """
    
    # Show videos
    if videos:
        viewer_html += f"""
        <h4 style="color: #e74c3c; margin: 15px 0 10px 0;">🎥 Videos ({len(videos)}):</h4>
        """
        
        for i, video_id in enumerate(video_order):
            video_data = videos[video_id]
            file_name = video_data["file_name"]
            video_type = video_data["video_type"]
            
            if video_type == "youtube":
                youtube_id = video_data["youtube_id"]
                embed_url = f"https://www.youtube.com/embed/{youtube_id}"
                viewer_html += f"""
                <div style="border: 1px solid #444; border-radius: 5px; margin-bottom: 10px; background-color: #1a1a1a;">
                    <div style="padding: 12px; border-bottom: 1px solid #444;">
                        <h5 style="color: #e74c3c; margin: 0 0 3px 0;">🎥 {file_name}</h5>
                        <p style="color: #888; margin: 0; font-size: 11px;">YouTube Video • ID: {youtube_id}</p>
                    </div>
                    <div style="padding: 8px 12px;">
                        <details>
                            <summary style="color: #e74c3c; cursor: pointer; font-size: 12px;">Watch Video</summary>
                            <div style="margin-top: 8px;">
                                <iframe width="100%" height="200" src="{embed_url}" 
                                        frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                                        allowfullscreen style="border-radius: 5px;"></iframe>
                            </div>
                        </details>
                    </div>
                </div>
                """
            
            else:  # local video
                # embed the file bytes into a Data URI so the browser can play it directly
                video_path = video_data["file_path"]
                file_name  = video_data["file_name"]

                # read & encode
                with open(video_path, "rb") as vf:
                    b64 = base64.b64encode(vf.read()).decode("utf-8")
                data_uri = f"data:video/mp4;base64,{b64}"

                viewer_html += f"""
                <div style="border:1px solid #444; border-radius:5px; margin-bottom:10px; background:#1a1a1a;">
                <div style="padding:12px; border-bottom:1px solid #444;">
                    <h5 style="color:#e74c3c; margin:0 0 3px 0;">🎥 {file_name}</h5>
                    <p style="color:#888; margin:0; font-size:11px;">Local Video File</p>
                </div>
                <div style="padding:8px 12px;">
                    <details>
                    <summary style="color:#e74c3c; cursor:pointer; font-size:12px;">Watch Video</summary>
                    <div style="margin-top:8px;">
                        <video controls width="100%" preload="metadata" style="border-radius:5px; background:black;">
                        <source src="{data_uri}" type="video/mp4">
                        Your browser does not support HTML5 video.
                        </video>
                        <p style="color:#666; margin:5px 0 0 0; font-size:10px;">
                        Note: Video files are kept in memory and accessible during this session.
                        </p>
                    </div>
                    </details>
                </div>
                </div>
                """


    
    viewer_html += """
        <div style="border-top: 1px solid #444; padding-top: 15px; margin-top: 15px;">
            <p style="color: #888; font-size: 12px; margin: 0;">
                💡 Documents are automatically included in AI chat. Video content analysis coming soon!
            </p>
        </div>
    </div>
    """
    
    return viewer_html

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
    
    # Handle document removals (completely remove documents)
    for file_name_to_remove in files_to_remove:
        doc_ids_to_remove = [doc_id for doc_id in document_order 
                            if documents[doc_id]["file_name"] == file_name_to_remove]
        for doc_id in doc_ids_to_remove:
            # Completely remove the document from all data structures
            del documents[doc_id]
            document_order.remove(doc_id)
            
            # Remove from position tracking
            if doc_id in document_positions:
                del document_positions[doc_id]
            
            removed_files.append(file_name_to_remove)
            print(f"Completely removed document: {file_name_to_remove}")
    
    # If documents were removed, clear the LLM chat history to rebuild it fresh
    # This ensures no stale references to deleted documents
    if removed_files and llm_chat_history is not None:
        llm_chat_history = None
        llm_chat_history_show = None
        document_positions.clear()
        chat_position_counter = 0
        print("Cleared LLM chat history due to document removal")
    
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
    
    # Always save the structured document info when documents change
    save_docs_structured_info()
    
    return chat_history, generate_media_viewer()

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

with gr.Blocks(title="Multi-Media Chat Assistant", css=css) as demo:
    with gr.Column(elem_classes="container"):
        gr.Markdown("# Multi-Media Chat Assistant", elem_classes="title")
        gr.Markdown("Upload PDF documents and videos to interact with their contents. Documents are processed with OCR and videos are available for viewing.")
        
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
                with gr.Row():
                    youtube_input = gr.Textbox(label="YouTube URL", placeholder="https://youtube.com/watch?v=...", value="", scale=4)
                    youtube_btn = gr.Button("Add YouTube", elem_classes="button", scale=1, size="lg")
                
                # Combined media viewer
                media_viewer = gr.HTML(label="Media Content", value=generate_media_viewer())
            
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
            fn=process_video_upload,
            inputs=[video_input, youtube_input, chatbot],
            outputs=[chatbot, media_viewer]
        )
        
        youtube_input.submit(
            fn=process_video_upload,
            inputs=[video_input, youtube_input, chatbot],
            outputs=[chatbot, media_viewer]
        )
        
        youtube_btn.click(
            fn=process_video_upload,
            inputs=[video_input, youtube_input, chatbot],
            outputs=[chatbot, media_viewer]
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
            save_docs_structured_info()  # Also update structured document info
            
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
        fn=lambda: (reset_all_state() or [], generate_media_viewer()),
        outputs=[chatbot, media_viewer],
        queue=False
    )

# Launch the app
if __name__ == "__main__":
    demo.launch(height=800)
