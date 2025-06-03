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

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
if not mistral_api_key:
    raise ValueError("MISTRAL_API_KEY is not set in the environment variables.")

# Initialize Mistral client
mistral_client = Mistral(api_key=mistral_api_key)

# Initialize OpenAI client for Gemini's OpenAI-compatible endpoint
openai_client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Initialize Gemini (keeping this for backward compatibility)
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

# Global variables to store the current document content
current_document_content = ""
current_document_text = ""  # Plain text version without images
current_ocr_response = None  # Store the full OCR response
file_name = ""
llm_chat_history = None
llm_chat_history_show = None

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

def upload_and_process(file, chat_history):
    """
    Process an uploaded PDF file and update the global document content.
    
    Args:
        file: Uploaded file object from Gradio
        chat_history: Current chat history
        
    Returns:
        Updated chat history and HTML content for the sidebar
    """
    global file_name, current_document_content, current_document_text, current_ocr_response
    
    if file is None:
        return chat_history, "<div style='padding: 20px; background-color: black; color: #e0e0e0; border-radius: 8px;'>Please upload a PDF file.</div>"
    
    try:
        pdf_file = Path(file.name)
        file_name = pdf_file.stem + ".pdf"

        print(f"\n\nProcessing PDF file: {file_name}\n")
        
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
        
        # Store the full OCR response
        current_ocr_response = pdf_response
        
        # Get combined markdown with images
        markdown_content = get_combined_markdown(pdf_response)
        current_document_content = markdown_content
        
        # Extract plain text for the LLM
        current_document_text = extract_text_from_ocr_response(pdf_response)
        
        # Convert markdown to HTML with styling for the sidebar
        html_content = markdown_to_html(markdown_content)
        
        # Add a system message to the chat history
        system_message = "PDF uploaded and processed successfully. You can now chat with its contents."
        if chat_history is None:
            chat_history = []
        chat_history = chat_history + [{"role": "assistant", "content": system_message}]
        
        return chat_history, html_content
        
    except Exception as e:
        error_message = f"Error processing PDF: {str(e)}"
        if chat_history is None:
            chat_history = []
        chat_history = chat_history + [{"role": "assistant", "content": error_message}]
        return chat_history, "<div style='padding: 20px; background-color: black; color: red; border-radius: 8px;'>Error processing PDF. Please try again.</div>"

def create_chat_messages_for_llm(messages=None):
    """
    Create a simplified representation of the document content for the LLM using OpenAI chat format.
    Reduces token usage by limiting the number of images and text chunks.
    
    Returns:
        A list of message objects with text and selected images
    """
    global current_ocr_response, file_name
    
    if not current_ocr_response:
        return [{"role": "user", "content":  "No document content available."}]
    
    if messages is None:
        # Start with a system message
        messages = [
            {"role": "system", "content": "You are an assistant that helps users understand document content. The document has been processed with OCR and contains both text and images."}
        ]
    
    # Create a user message with content array that will contain text and selected images
    user_content = []
    user_content_show = []
    
    # Add a text summary of the document structure
    page_count = len(current_ocr_response.pages)
    doc_info = {
        "type": "text",
        "text": f"Document name: {file_name}.\nThis document contains {page_count} pages with text and images."
    }
    user_content.append(doc_info)
    user_content_show.append(doc_info)

    for i, page in enumerate(current_ocr_response.pages):
        
        page_markdown_str = page.markdown
        image_data = {}

        user_content.append({
            "type": "text",
            "text": f"\n\n\n{'-'*20}\n## Page {i + 1}:-\n\n"
        })

        user_content_show.append({
            "type": "text",
            "text": f"\n\n\n{'-'*20}\n## Page {i + 1}:-\n\n"
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

            user_content.append({
                "type": "text",
                "text": f"Attaching an image in the page. Image name: {'page-'+str(i)+'-'+img_name}.\n\n"
            })

            user_content_show.append({
                "type": "text",
                "text": f"Attaching an image in the page. Image name: {'page-'+str(i)+'-'+img_name}.\n\n"
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
    
    messages_show = messages.copy()
    
    # Add the content array to the user message
    messages.append({"role": "user", "content": user_content})
    messages_show.append({"role": "user", "content": user_content_show})

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
    global current_document_text, current_ocr_response, llm_chat_history, llm_chat_history_show

    # If no document is uploaded, just replace the placeholder with an error message
    if not current_ocr_response:
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

        user_message = f"{'-'*10}DOCUMENT END{'-'*10}\n{'-'*20}\n\n\n# User question:\n"
        user_message += message if message is not None else "No message provided."

        # Append the user's new question to the context
        document_messages.append({"role": "user", "content": user_message})
        document_messages_show.append({"role": "user", "content": user_message[:500] + "..." 
                                      if len(user_message) > 500 else user_message})

        print(f"Sending {len(document_messages)} messages to Gemini\n")
        print(f"Message to Gemini:\n{json.dumps(document_messages_show, indent=4)}\n\n")

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

    except Exception as e:
        error_message = f"Error generating response: {str(e)}"
        print(f"Error details: {e}")
        # Overwrite placeholder with error
        chat_history[-1]["content"] = error_message
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

with gr.Blocks(title="PDF Chat Assistant", css=css) as demo:
    with gr.Column(elem_classes="container"):
        gr.Markdown("# PDF Chat Assistant", elem_classes="title")
        gr.Markdown("Upload a PDF file to chat with its contents and view the rendered markdown.")
        
        with gr.Row():
            # Left sidebar for PDF viewer
            with gr.Column(scale=2, elem_classes="sidebar"):
                gr.Markdown("### PDF Content Viewer")
                file_input = gr.File(label="Upload PDF", file_types=[".pdf"])
                pdf_viewer = gr.HTML(label="Document Content")
            
            # Right side for chat interface
            with gr.Column(scale=3, elem_classes="chatbox"):
                gr.Markdown("### Chat with PDF Content")
                chatbot = gr.Chatbot(height=500, type="messages")
                msg = gr.Textbox(
                    placeholder="Ask questions about the PDF content...",
                    show_label=False
                )
                
                with gr.Row():
                    submit_btn = gr.Button("Send", elem_classes="button")
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
            global llm_chat_history, llm_chat_history_show
            llm_chat_history = None
            llm_chat_history_show = None
            return []

        clear_btn.click(
            fn=clear_chat,
            outputs=[chatbot]
        )
        
        gr.Examples(
            examples=["AGV_Task_2023.pdf"],
            inputs=file_input,
        )

# Launch the app
if __name__ == "__main__":
    demo.launch(height=800)
