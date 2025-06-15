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
            <div style="border: 1px solid #444; border-radius: 5px; margin-bottom: 10px; background-color: #1a1a1a;" id="document-{doc_id}">
                <div style="padding: 12px; border-bottom: 1px solid #444; position: relative;">
                    <span style="position: absolute; top: 8px; right: 8px; background: #e74c3c; color: white; border: none; border-radius: 50%; width: 20px; height: 20px; font-size: 12px; cursor: pointer; display: flex; align-items: center; justify-content: center; text-align: center; line-height: 20px;"
                          onclick="removeDocumentClick('{doc_id}')"
                          class="remove-document-btn"
                          title="Remove document">×</span>
                    <h5 style="color: #3498db; margin: 0 0 3px 25px;">📄 {file_name}</h5>
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
                <div style="border: 1px solid #444; border-radius: 5px; margin-bottom: 10px; background-color: #1a1a1a;" id="video-{video_id}">
                    <div style="padding: 12px; border-bottom: 1px solid #444; position: relative;">
                        <span style="position: absolute; top: 8px; right: 8px; background: #e74c3c; color: white; border: none; border-radius: 50%; width: 20px; height: 20px; font-size: 12px; cursor: pointer; display: flex; align-items: center; justify-content: center; text-align: center; line-height: 20px;"
                              onclick="removeVideoClick('{video_id}')"
                              class="remove-video-btn"
                              title="Remove video">×</span>
                        <h5 style="color: #e74c3c; margin: 0 0 3px 25px;">🎥 {file_name}</h5>
                        <p style="color: #888; margin: 0; font-size: 11px;">YouTube Video • ID: {youtube_id}</p>
                    </div>
                    <div style="padding: 8px 12px;">
                        <details style="margin-bottom: 8px;">
                            <summary style="color: #e74c3c; cursor: pointer; font-size: 12px;">📺 Watch Video</summary>
                            <div style="margin-top: 8px;">
                                <iframe width="100%" height="200" src="{embed_url}"
                                        frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                        allowfullscreen style="border-radius: 5px;"></iframe>
                            </div>
                        </details>
                        <details>
                            <summary style="color: #f39c12; cursor: pointer; font-size: 12px;">📄 View AI Description (JSON)</summary>
                            <div style="margin-top: 8px;">
                                {generate_video_description_json(video_id, i)}
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
                <div style="border:1px solid #444; border-radius:5px; margin-bottom:10px; background:#1a1a1a;" id="video-{video_id}">
                <div style="padding:12px; border-bottom:1px solid #444; position: relative;">
                    <span style="position: absolute; top: 8px; right: 8px; background: #e74c3c; color: white; border: none; border-radius: 50%; width: 20px; height: 20px; font-size: 12px; cursor: pointer; display: flex; align-items: center; justify-content: center; text-align: center; line-height: 20px;"
                          onclick="removeVideoClick('{video_id}')"
                          class="remove-video-btn"
                          title="Remove video">×</span>
                    <h5 style="color:#e74c3c; margin:0 0 3px 25px;">🎥 {file_name}</h5>
                    <p style="color:#888; margin:0; font-size:11px;">Local Video File</p>
                </div>
                <div style="padding:8px 12px;">
                    <details style="margin-bottom: 8px;">
                    <summary style="color:#e74c3c; cursor:pointer; font-size:12px;">📺 Watch Video</summary>
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
                    <details>
                        <summary style="color: #f39c12; cursor: pointer; font-size: 12px;">📄 View AI Description (JSON)</summary>
                        <div style="margin-top: 8px;">
                            {generate_video_description_json(video_id, i)}
                        </div>
                    </details>
                </div>
                </div>
                """

    
    viewer_html += """
        <div style="border-top: 1px solid #444; padding-top: 15px; margin-top: 15px;">
            <p style="color: #888; font-size: 12px; margin: 0;">
                💡 Documents are automatically included in AI chat. Videos are analyzed with AI descriptions upon upload.
            </p>
        </div>
    </div>
    
    <style>
        .remove-video-btn:hover {
            background: #c0392b !important;
            transform: scale(1.1);
            transition: all 0.2s ease;
        }
        .remove-document-btn:hover {
            background: #c0392b !important;
            transform: scale(1.1);
            transition: all 0.2s ease;
        }
    </style>
    """
    
    return viewer_html

def generate_video_description_json(video_id, video_index):
    """
    Generate HTML display for video description JSON.
    
    Args:
        video_id: Video ID
        video_index: Video index for lookup
        
    Returns:
        HTML string with JSON description or placeholder
    """
    try:
        import json
        import os
        
        # Get the JSON folder path
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_file_path = os.path.join(current_dir, "json", "video_structured_info.json")
        
        if not os.path.exists(json_file_path):
            return """
            <div style="background-color: #2c2c2c; padding: 15px; border-radius: 5px; border-left: 4px solid #f39c12;">
                <p style="color: #f39c12; margin: 0; font-size: 12px;">⏳ Video description not yet generated</p>
                <p style="color: #888; margin: 5px 0 0 0; font-size: 11px;">Upload the video to automatically generate AI descriptions.</p>
            </div>
            """
        
        # Read and parse the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            video_descriptions = json.load(f)
        
        # Find the description for this video
        video_description = None
        for desc in video_descriptions:
            if desc.get('video_id') == video_index:
                video_description = desc
                break
        
        if not video_description:
            return """
            <div style="background-color: #2c2c2c; padding: 15px; border-radius: 5px; border-left: 4px solid #e74c3c;">
                <p style="color: #e74c3c; margin: 0; font-size: 12px;">❌ No description found</p>
                <p style="color: #888; margin: 5px 0 0 0; font-size: 11px;">Video description may still be processing.</p>
            </div>
            """
        
        # Count timestamps
        timestamp_count = len(video_description.get('video_content', []))
        
        # Create syntax-highlighted JSON
        highlighted_json = create_syntax_highlighted_json(video_description)
        
        return f"""
        <div style="background-color: #0a0a0a; padding: 15px; border-radius: 5px; border-left: 4px solid #2ecc71;">
            <div style="margin-bottom: 10px;">
                <p style="color: #2ecc71; margin: 0; font-size: 12px; font-weight: bold;">✅ AI Description Available</p>
                <p style="color: #888; margin: 2px 0 0 0; font-size: 11px;">
                    Generated {timestamp_count} timestamped segments with transcripts and descriptions
                </p>
            </div>
            <details>
                <summary style="color: #3498db; cursor: pointer; font-size: 11px; margin-bottom: 8px;">Show JSON Data</summary>
                <div style="margin-top: 8px; max-height: 400px; overflow-y: auto; background-color: #1a1a1a; padding: 15px; border-radius: 5px; border: 1px solid #333;">
                    {highlighted_json}
                </div>
            </details>
        </div>
        """
        
    except Exception as e:
        return f"""
        <div style="background-color: #2c2c2c; padding: 15px; border-radius: 5px; border-left: 4px solid #e74c3c;">
            <p style="color: #e74c3c; margin: 0; font-size: 12px;">❌ Error loading description</p>
            <p style="color: #888; margin: 5px 0 0 0; font-size: 11px;">Error: {str(e)}</p>
        </div>
        """

def create_syntax_highlighted_json(json_data, indent=0):
    """
    Pretty-print Python data as coloured JSON HTML.
    • Keys           → .json-key
    • String values  → .json-string
    • Escapes (e.g. \n, \t, \", \\) → .json-esc
    """
    import json, html, re
    IND = "  "
    # matches a backslash + any single character
    ESC_RE = re.compile(r'\\.')

    def build_string(raw, inner_cls):
        # 1) literalize control chars
        s = raw.replace('\r', '\\r') \
               .replace('\n', '\\n') \
               .replace('\t', '\\t')
        # 2) backslash-escape any embedded quotes
        s = s.replace('"', '\\"')
        # 3) split on any backslash+char
        parts, last = [], 0
        for m in ESC_RE.finditer(s):
            start, end = m.span()
            # plain text chunk
            if start > last:
                chunk = s[last:start]
                parts.append(
                    f'<span class="{inner_cls}">{html.escape(chunk)}</span>'
                )
            # the escape sequence itself
            esc = m.group(0)
            parts.append(
                f'<span class="json-esc">{html.escape(esc, quote=False)}</span>'
            )
            last = end
        # tail
        if last < len(s):
            chunk = s[last:]
            parts.append(
                f'<span class="{inner_cls}">{html.escape(chunk)}</span>'
            )
        # wrap in quotes
        return (
            '<span class="json-quote">"</span>'
            + "".join(parts) +
            '<span class="json-quote">"</span>'
        )

    q_key = lambda k: build_string(k, "json-key")
    q_val = lambda v: build_string(v, "json-string")
    punct = lambda ch, cls="json-punct": f'<span class="{cls}">{ch}</span>'

    def render(obj, lvl):
        sp = IND * lvl
        if isinstance(obj, dict):
            out = [punct("{", "json-brace")]
            if obj:
                out.append("\n")
                for i, (k, v) in enumerate(obj.items()):
                    out += [
                        sp + IND,
                        q_key(k),
                        punct(":", "json-colon"), " ",
                        render(v, lvl + 1)
                    ]
                    if i < len(obj) - 1:
                        out.append(punct(",", "json-comma"))
                    out.append("\n")
                out.append(sp)
            out.append(punct("}", "json-brace"))
            return "".join(out)

        if isinstance(obj, list):
            out = [punct("[", "json-bracket")]
            if obj:
                out.append("\n")
                for i, v in enumerate(obj):
                    out += [sp + IND, render(v, lvl + 1)]
                    if i < len(obj) - 1:
                        out.append(punct(",", "json-comma"))
                    out.append("\n")
                out.append(sp)
            out.append(punct("]", "json-bracket"))
            return "".join(out)

        if isinstance(obj, str):
            return q_val(obj)

        if isinstance(obj, bool):
            return f'<span class="json-bool">{str(obj).lower()}</span>'

        if obj is None:
            return '<span class="json-null">null</span>'

        return f'<span class="json-num">{obj}</span>'

    body = render(json_data, indent)
    return (
        '<div class="json-box"><pre style="margin:0;font-size:11px;'
        'line-height:1.4;color:#e0e0e0;white-space:pre-wrap;'
        'word-break:break-all;">'
        + body +
        '</pre></div>'
    )

def generate_youtube_url_manager():
    """
    Generate HTML interface for managing multiple YouTube URLs.
    
    Returns:
        HTML string with YouTube URL management interface
    """
    return """
    <div id="youtube-manager" style="background-color: #1a1a1a; border: 1px solid #444; border-radius: 5px; padding: 15px; margin-bottom: 10px;">
        <h4 style="color: #e74c3c; margin: 0 0 10px 0;">🎥 YouTube URLs</h4>
        <div id="youtube-urls-list" style="margin-bottom: 10px;">
            <div class="youtube-url-item" style="display: flex; margin-bottom: 5px; align-items: center;">
                <input type="text" class="youtube-url-input" placeholder="https://youtube.com/watch?v=..."
                       style="flex: 1; padding: 8px; border: 1px solid #666; border-radius: 3px; background: #2a2a2a; color: #e0e0e0; margin-right: 8px;">
                <button onclick="addYouTubeUrlField()"
                        style="background: #2ecc71; color: white; border: none; border-radius: 3px; width: 30px; height: 30px; cursor: pointer; display: flex; align-items: center; justify-content: center;"
                        title="Add another URL field">+</button>
            </div>
        </div>
        <button onclick="processAllYouTubeUrls()"
                style="background: #3498db; color: white; border: none; border-radius: 3px; padding: 8px 16px; cursor: pointer; font-size: 12px;">
            Add All YouTube Videos
        </button>
        <p style="color: #888; font-size: 10px; margin: 8px 0 0 0;">
            💡 Add multiple YouTube URLs and process them all at once
        </p>
    </div>
    
    <script>
        function addYouTubeUrlField() {
            const container = document.getElementById('youtube-urls-list');
            const newItem = document.createElement('div');
            newItem.className = 'youtube-url-item';
            newItem.style.cssText = 'display: flex; margin-bottom: 5px; align-items: center;';
            newItem.innerHTML = `
                <input type="text" class="youtube-url-input" placeholder="https://youtube.com/watch?v=..."
                       style="flex: 1; padding: 8px; border: 1px solid #666; border-radius: 3px; background: #2a2a2a; color: #e0e0e0; margin-right: 8px;">
                <button onclick="removeYouTubeUrlField(this)"
                        style="background: #e74c3c; color: white; border: none; border-radius: 3px; width: 30px; height: 30px; cursor: pointer; display: flex; align-items: center; justify-content: center;"
                        title="Remove this URL field">×</button>
            `;
            container.appendChild(newItem);
        }
        
        function removeYouTubeUrlField(button) {
            const container = document.getElementById('youtube-urls-list');
            if (container.children.length > 1) {
                button.parentElement.remove();
            }
        }
        
        function processAllYouTubeUrls() {
            const inputs = document.querySelectorAll('.youtube-url-input');
            const urls = Array.from(inputs).map(input => input.value.trim()).filter(url => url);
            
            if (urls.length === 0) {
                alert('Please enter at least one YouTube URL');
                return;
            }
            
            // Clear the input fields
            inputs.forEach(input => input.value = '');
            
            // Trigger the upload process with multiple URLs
            // This would need to be connected to the Gradio backend
            console.log('Processing YouTube URLs:', urls);
            
            // For now, we'll join them with newlines and put in a hidden field
            const hiddenInput = document.querySelector('#youtube_urls_hidden');
            if (hiddenInput) {
                hiddenInput.value = urls.join('\\n');
                // Trigger change event
                hiddenInput.dispatchEvent(new Event('change'));
            }
        }
        
        function removeVideo(videoId) {
            if (confirm('Are you sure you want to remove this video?')) {
                // Trigger video removal
                const hiddenInput = document.querySelector('#remove_video_hidden');
                if (hiddenInput) {
                    hiddenInput.value = videoId;
                    // Trigger change event
                    hiddenInput.dispatchEvent(new Event('change'));
                }
            }
        }
    </script>
    """