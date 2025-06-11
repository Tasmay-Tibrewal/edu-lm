"""
UI utilities module for generating HTML interfaces and UI components.
"""
import markdown

def generate_document_buttons(documents, document_order):
    """
    Generate HTML interface showing all uploaded documents.
    
    Args:
        documents: Dictionary of document data
        document_order: List of document IDs in order
        
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

def generate_media_viewer(documents, document_order, videos, video_order):
    """
    Generate HTML interface showing all uploaded documents and videos.
    
    Args:
        documents: Dictionary of document data
        document_order: List of document IDs in order
        videos: Dictionary of video data
        video_order: List of video IDs in order
        
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
                file_name = video_data["file_name"]

                # read & encode
                import base64
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