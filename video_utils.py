"""
Video utilities module for processing video files and YouTube URLs.
"""
import re
import base64
from pathlib import Path

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
    """
    Check if a URL is a YouTube URL.
    
    Args:
        url: URL to check
        
    Returns:
        Boolean indicating if the URL is a YouTube URL
    """
    return extract_youtube_id(url) is not None

def process_video_upload(files, youtube_url, chat_history, videos, video_order):
    """
    Process video uploads (both file uploads and YouTube URLs).
    Keeps videos in memory without saving to disk.
    
    Args:
        files: List of uploaded video files
        youtube_url: YouTube URL string (if provided)
        chat_history: Current chat history
        videos: Dictionary of video data
        video_order: List of video IDs in order
        
    Returns:
        Tuple of (updated chat history, processed_videos, failed_videos)
    """
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
    
    return chat_history, processed_videos, failed_videos