"""
Video utilities module for processing video files and YouTube URLs.
"""
import re
import base64
import asyncio
from pathlib import Path
from utils.video_description import generate_new_video_descriptions
from manage.data_manager import save_video_structured_info

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

def process_video_upload(files, youtube_url, chat_history, videos, video_order, genai_client=None, structured_videos_cache=None):
    """
    Process video uploads (both file uploads and YouTube URLs).
    Keeps videos in memory without saving to disk.
    Automatically generates video descriptions upon upload.
    
    Args:
        files: List of uploaded video files
        youtube_url: YouTube URL string (if provided)
        chat_history: Current chat history
        videos: Dictionary of video data
        video_order: List of video IDs in order
        genai_client: Google GenAI client for description generation
        structured_videos_cache: In-memory cache for structured video information
        
    Returns:
        Tuple of (updated chat history, processed_videos, failed_videos, updated_structured_videos_cache)
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
        system_message = "\n".join(status_messages) + f"\n\nTotal videos: {len(videos)}."
        chat_history = chat_history + [{"role": "assistant", "content": system_message}]
    
    # Automatically generate descriptions for newly uploaded videos only
    updated_structured_videos_cache = structured_videos_cache if structured_videos_cache is not None else []
    
    if processed_videos and genai_client is not None:
        try:
            # Add a status message about description generation
            description_message = "🤖 Generating AI descriptions for new videos... This may take a few minutes."
            chat_history = chat_history + [{"role": "assistant", "content": description_message}]
            
            print("🤖 Starting automatic video description generation for new videos...")
            
            # Get existing video IDs from cache
            existing_video_ids = set()
            for cached_video in updated_structured_videos_cache:
                if 'video_id' in cached_video:
                    existing_video_ids.add(f"video_{cached_video['video_id']}")
            
            # Generate descriptions only for new videos using sync wrapper
            new_descriptions = generate_new_video_descriptions_sync(
                genai_client, videos, video_order, existing_video_ids
            )
            
            if new_descriptions:
                # Combine with existing cache
                updated_structured_videos_cache.extend(new_descriptions)
                # Save to file
                updated_structured_videos_cache = save_video_structured_info(updated_structured_videos_cache, updated_structured_videos_cache)
                
                # Update status with completion
                completion_message = f"✅ Video descriptions generated successfully! Processed {len(new_descriptions)} new videos with AI analysis."
                chat_history = chat_history + [{"role": "assistant", "content": completion_message}]
            else:
                info_message = "ℹ️ No new videos to process for descriptions."
                chat_history = chat_history + [{"role": "assistant", "content": info_message}]
            
        except Exception as e:
            error_message = f"❌ Error generating video descriptions: {str(e)}"
            print(error_message)
            chat_history = chat_history + [{"role": "assistant", "content": error_message}]
    
    return chat_history, processed_videos, failed_videos, updated_structured_videos_cache

async def generate_new_video_descriptions_async(genai_client, videos, video_order, existing_video_ids):
    """
    Generate video descriptions asynchronously for new videos only.
    
    Args:
        genai_client: The Google GenAI client
        videos: Dictionary of video data
        video_order: List of video IDs in order
        existing_video_ids: Set of video IDs that already have descriptions
        
    Returns:
        List of new video descriptions
    """
    try:
        if not videos or not video_order:
            print("No videos to process for descriptions")
            return []
        
        print(f"Starting video description generation for new videos...")
        
        # Import the function from video_description module
        from utils.video_description import generate_new_video_descriptions
        
        # Generate descriptions for new videos only
        video_descriptions = await generate_new_video_descriptions(genai_client, videos, video_order, existing_video_ids)
        
        return video_descriptions
        
    except Exception as e:
        print(f"Error generating video descriptions: {e}")
        return []

async def generate_video_descriptions_async(genai_client, videos, video_order, structured_videos_cache):
    """
    Generate video descriptions asynchronously for all videos.
    
    Args:
        genai_client: The Google GenAI client
        videos: Dictionary of video data
        video_order: List of video IDs in order
        structured_videos_cache: In-memory cache for structured video information
        
    Returns:
        Updated structured_videos_cache
    """
    try:
        if not videos or not video_order:
            print("No videos to process for descriptions")
            return structured_videos_cache
        
        print(f"Starting video description generation for {len(video_order)} videos...")
        
        # Generate descriptions for all videos
        from utils.video_description import generate_all_video_descriptions
        video_descriptions = await generate_all_video_descriptions(genai_client, videos, video_order)
        
        # Save to file and update cache
        structured_videos_cache = save_video_structured_info(video_descriptions, structured_videos_cache)
        
        return structured_videos_cache
        
    except Exception as e:
        print(f"Error generating video descriptions: {e}")
        return structured_videos_cache

def generate_new_video_descriptions_sync(genai_client, videos, video_order, existing_video_ids):
    """
    Synchronous wrapper for generating descriptions for new videos only.
    
    Args:
        genai_client: The Google GenAI client
        videos: Dictionary of video data
        video_order: List of video IDs in order
        existing_video_ids: Set of video IDs that already have descriptions
        
    Returns:
        List of new video descriptions
    """
    try:
        # Create new event loop if one doesn't exist
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async function
        return loop.run_until_complete(
            generate_new_video_descriptions_async(genai_client, videos, video_order, existing_video_ids)
        )
        
    except Exception as e:
        print(f"Error in synchronous video description generation: {e}")
        return []

def generate_video_descriptions_sync(genai_client, videos, video_order, structured_videos_cache):
    """
    Synchronous wrapper for generating video descriptions.
    
    Args:
        genai_client: The Google GenAI client
        videos: Dictionary of video data
        video_order: List of video IDs in order
        structured_videos_cache: In-memory cache for structured video information
        
    Returns:
        Updated structured_videos_cache
    """
    try:
        # Create new event loop if one doesn't exist
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async function
        return loop.run_until_complete(
            generate_video_descriptions_async(genai_client, videos, video_order, structured_videos_cache)
        )
        
    except Exception as e:
        print(f"Error in synchronous video description generation: {e}")
        return structured_videos_cache