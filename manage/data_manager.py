"""
Data management module for saving and loading data to/from JSON files.
"""
import json
import os

# Define JSON folder path (absolute path based on current file location)
# Get the directory of this file (manage/), then go up one level and into json/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
JSON_FOLDER = os.path.join(PROJECT_ROOT, "json")

# Ensure json folder exists
if not os.path.exists(JSON_FOLDER):
    os.makedirs(JSON_FOLDER)

def save_llm_call_payload(messages, messages_show):
    """
    Save the LLM call payload to JSON files.
    
    Args:
        messages: Full LLM messages payload
        messages_show: Truncated LLM messages payload for display
    """
    try:
        # Save full payload
        with open(os.path.join(JSON_FOLDER, "llm_structured_call.json"), "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
        
        # Save show payload
        with open(os.path.join(JSON_FOLDER, "llm_structured_call_show.json"), "w", encoding="utf-8") as f:
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
        
        with open(os.path.join(JSON_FOLDER, "chat_history_gradio.json"), "w", encoding="utf-8") as f:
            json.dump(chat_history, f, indent=2, ensure_ascii=False)
        
        print(f"Saved Gradio chat history ({len(chat_history)} messages)")
    except Exception as e:
        print(f"Error saving chat history: {e}")

def generate_docs_structured_info(documents, document_order):
    """
    Generate structured document information according to the JSON schema.
    Only includes available documents (deleted documents are completely removed).
    
    Args:
        documents: Dictionary of document data
        document_order: List of document IDs in order
        
    Returns:
        List of document information dictionaries matching the schema
    """
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

def save_docs_structured_info(documents, document_order, structured_docs_cache):
    """
    Save the structured document information to docs_structured_info.json file and update in-memory cache.
    
    Args:
        documents: Dictionary of document data
        document_order: List of document IDs in order
        structured_docs_cache: In-memory cache for structured document information
        
    Returns:
        Updated structured_docs_cache
    """
    try:
        structured_docs = generate_docs_structured_info(documents, document_order)
        
        # Update in-memory cache
        structured_docs_cache = structured_docs.copy()
        
        # Save to file
        with open(os.path.join(JSON_FOLDER, "docs_structured_info.json"), "w", encoding="utf-8") as f:
            json.dump(structured_docs, f, indent=2, ensure_ascii=False)
        
        print(f"Saved structured document info to docs_structured_info.json and updated cache ({len(structured_docs)} documents)")
        return structured_docs_cache
    except Exception as e:
        print(f"Error saving structured document info: {e}")
        return structured_docs_cache

def save_video_structured_info(video_descriptions, structured_videos_cache):
    """
    Save the structured video information to video_structured_info.json file and update in-memory cache.
    
    Args:
        video_descriptions: List of video description dictionaries
        structured_videos_cache: In-memory cache for structured video information
        
    Returns:
        Updated structured_videos_cache
    """
    try:
        # Update in-memory cache
        structured_videos_cache = video_descriptions.copy() if video_descriptions else []
        
        # Save to file
        with open(os.path.join(JSON_FOLDER, "video_structured_info.json"), "w", encoding="utf-8") as f:
            json.dump(video_descriptions, f, indent=2, ensure_ascii=False)
        
        print(f"Saved structured video info to video_structured_info.json and updated cache ({len(video_descriptions)} videos)")
        return structured_videos_cache
    except Exception as e:
        print(f"Error saving structured video info: {e}")
        return structured_videos_cache

def initialize_json_files():
    """Initialize all JSON files as empty at startup."""
    try:
        save_chat_history([])
        save_llm_call_payload([], [])
        
        # Initialize the new structured docs file
        with open(os.path.join(JSON_FOLDER, "docs_structured_info.json"), "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)
        
        # Initialize the structured video info file
        with open(os.path.join(JSON_FOLDER, "video_structured_info.json"), "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)
            
        print("Initialized all JSON files as empty")
    except Exception as e:
        print(f"Error initializing JSON files: {e}")