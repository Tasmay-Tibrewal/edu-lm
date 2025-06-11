"""
Document utilities module for processing PDF documents and OCR results.
"""
import markdown
import base64
import re
from pathlib import Path
from mistralai import DocumentURLChunk, ImageURLChunk, TextChunk

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

def get_combined_markdown(ocr_response) -> str:
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

def create_document_content_block(doc_id, doc_index, documents):
    """
    Create document content block for a specific document.
    
    Args:
        doc_id: Document ID
        doc_index: Document index for naming scheme
        documents: Dictionary of document data
        
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

def upload_and_process_document(file, mistral_client, documents, document_order, document_positions, 
                               chat_position_counter, llm_chat_history, llm_chat_history_show):
    """
    Process a single document upload.
    
    Args:
        file: File object to process
        mistral_client: Mistral API client
        documents: Dictionary of document data
        document_order: List of document IDs in order
        document_positions: Dictionary mapping document IDs to positions
        chat_position_counter: Counter for chat positions
        llm_chat_history: LLM chat history
        llm_chat_history_show: Truncated LLM chat history
        
    Returns:
        Tuple of (doc_id, file_name, success)
    """
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
            doc_id = f"doc_{len(documents) + 1}"
        
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
            new_doc_content, new_doc_content_show = create_document_content_block(doc_id, doc_index, documents)
            
            # Simply append at the end to maintain chronological order
            llm_chat_history.append({"role": "user", "content": new_doc_content})
            llm_chat_history_show.append({"role": "user", "content": new_doc_content_show})
            
            # Store position for new document
            document_positions[doc_id] = len(llm_chat_history) - 1
        else:
            # Mark position for when chat history is created
            document_positions[doc_id] = chat_position_counter
            chat_position_counter += 1
        
        return doc_id, file_name, True
        
    except Exception as e:
        print(f"Error processing {file.name}: {str(e)}")
        return None, file.name, False

def view_document(doc_id, documents):
    """
    Display the content of a specific document.
    
    Args:
        doc_id: Document ID to display
        documents: Dictionary of document data
        
    Returns:
        HTML content of the selected document
    """
    if doc_id not in documents:
        return "<div style='padding: 20px; background-color: black; color: red; border-radius: 8px;'>Document not found.</div>"
    
    doc_data = documents[doc_id]
    return markdown_to_html(doc_data["content"])

def create_chat_messages_for_llm(documents, document_order, document_positions, chat_position_counter):
    """
    Create initial chat messages with all document contents for the LLM.
    Only used when starting a new conversation - thereafter we use preserved history.
    
    Args:
        documents: Dictionary of document data
        document_order: List of document IDs in order
        document_positions: Dictionary mapping document IDs to positions
        chat_position_counter: Counter for chat positions
        
    Returns:
        Tuple of (messages, messages_show, document_positions, chat_position_counter)
    """
    if not documents:
        return [{"role": "user", "content": "No document content available."}], [{"role": "user", "content": "No document content available."}], document_positions, chat_position_counter
    
    # Start with a system message
    messages = [
        {"role": "system", "content": "You are an assistant that helps users understand multiple document contents. The documents have been processed with OCR and contain both text and images."}
    ]
    messages_show = [
        {"role": "system", "content": "You are an assistant that helps users understand multiple document contents. The documents have been processed with OCR and contain both text and images."}
    ]
    
    # Add each document as a separate user message block
    for doc_index, doc_id in enumerate(document_order):
        doc_content, doc_content_show = create_document_content_block(doc_id, doc_index, documents)
        
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

    return messages, messages_show, document_positions, chat_position_counter