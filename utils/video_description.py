"""
Video description module for generating detailed video descriptions using Google's Gemini API.
"""
import os
import base64
import json
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from google.genai import types
from pathlib import Path


def format_time_seconds_to_hms(seconds):
    """Convert seconds to HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def convert_hms_to_seconds(hms_string):
    """Convert HH:MM:SS format to seconds."""
    time_parts = hms_string.split(':')
    if len(time_parts) == 3:
        hours, minutes, seconds = map(int, time_parts)
        return hours * 3600 + minutes * 60 + seconds
    elif len(time_parts) == 2:
        minutes, seconds = map(int, time_parts)
        return minutes * 60 + seconds
    else:
        return int(time_parts[0])


def create_video_system_prompt():
    """Create the system prompt for video description."""
    return """You are an expert video analyser. You have the role of transcribing a video (audio to text, with timestamps) and then creating a detailed description of the video. Note: This will likely be an educational/informative video, so approach the task accordingly.

Your tasks are as follows:
A) You should first create a transcription of the video audio.
B) You should then create its description

Do this timestamp by timestamp.

Follow the XML format below:
<video_desc_doc>
    <video>
        "video_name": "$name_of_the_video", // name of the video
        "video_id": 0, // video id is 0 indexed
        "video_info_available": 1, // this video is in context and not deleted, so it is available
        <video_content>
            <timestamp>
                "video_timestamp_num": 0, // timestamp number
                "timestamp_start": "00:00:00", // start time of the timestamp in HH:MM:SS format
                "timestamp_end": "00:01:23", // end time of the timestamp in HH:MM:SS format
                <timestamp_transcript_content>
                    "content_type": "text", // content type is text
                    "content": "$transcript_in_markdown_format_for_timestamp" // transcript content in markdown format, with expressions like (laughs), (applause), (excited), (background noise), and then ## for headings, or ** for importance etc.
                </timestamp_transcript_content>
                <timestamp_description_content>
                    "content_type": "text", // content type is text
                    "content": "$description_in_markdown_format_for_timestamp" // description content in markdown format, this describes the video content, and the audio content in the timestamp, influenced by the context of the video and the previous scenes/timestamps
                    // the description should include references to the transcript content, like "the speaker says X, as mentioned in the transcript."
                    // the description should also include references to the video content, like "speaker shows a diagram of Y in the video."
                    // the description should also talk about the visuals, the speaker's expressions or body language (if relevant), the background, and any other relevant details that can help the user understand the video content better
                    // it should talk about the tone of voice, the mood, the background noise or music, etc.
                    // it should also talk about the context of timestamp being discussed and how it relates to the overall video content
                    // it should be detailed and comprehensive, and explain the content of the timestamp in high details
                    // ideally the videos will be lectures, tutorials, or educational content, so the description should be informative and helpful
                    // it should capture all the information that is provided in the video for the topic being discussed
                </timestamp_description_content>
            </timestamp>
            <timestamp>
                "video_timestamp_num": 1,
                "timestamp_start": "00:01:23",
                "timestamp_end": "00:04:07",
                <timestamp_transcript_content>
                    "content_type": "text",
                    "content": "$transcript_in_markdown_format_for_timestamp"
                </timestamp_transcript_content>
                <timestamp_description_content>
                    "content_type": "text",
                    "content": "$description_in_markdown_format_for_timestamp"
                </timestamp_description_content>
            </timestamp>
            // add more timestamps as needed
        </video_content>
    </video>
</video_desc_doc>

Kindly use logical segmentation that aligns with how a viewer would naturally process the information. Dont keep the timestamps too small. Make the descriptions rich, detailed, and capture the full context, tone, and visual elements of the video. Successfully fulfill the core objective required: to create a helpful and informative guide to the video's content.

Make sure to also obey the format and the HH:MM:SS part specifically. Think hard and a lot about the video, its contents, its transcripts and how you plane to describe it, before actually describing it.

Certain factors to help you:
1) **Comprehensiveness**: make them incredibly detailed, providing a thorough summary of each segment.
2) **Context and Flow**: Each description must expertly connect its segment to the overall narrative of the video.
3) **Visuals and Tone**: The descriptions must meticulously detail the on-screen visuals and accurately describe the speaker's tone and the content being spoken about.
4) **Objective Alignment**: The descriptions must perfectly fulfill every requirement of the objective, explaining the technical concepts, the tone/mood of the video, and how the visuals support the narration/information provided.
5) **Capture information**: The description should capture detailed information about the content in general, the topic being taught, equations, code, formulaes, facts, dates, important points, questions, diagrams, and all other important things that were discussed. Everything should be exhaustively present, nothing should be missed out on.
6) **Take large timestamp segments**: You do NOT need to be granular, be free flowing, take larger, logical scenes and logical cuts and describe the whole thing together, like large chunks relating to a large overall context, kind of like chapters in a youtube video. Do not make it like 5 second, 10 second, 20 second cuts, unless the scene is only like that, generally try for capturing a lot of context into a single timestamp description to make better sense of the video content there and how it connects with other chunks, just like we as humans do while seeing a video. Larger chunks will always help in capturing context effectively and making the descriptions rich and informative, instead of slim, narrow, granular and limited to transcript based singular (non-contextualised) knowledge.

Think hard on how you plan to structure your response and describe them according to the video, in a very natural human like interpretation."""


def create_initial_user_prompt():
    """Create the initial user prompt for first video chunk."""
    return "Please give the video's transcript and description here in XML format. Remember to follow all instructions and return rich and detailed video description using the specified XML structure:"


def create_subsequent_user_prompt(part_num, total_previous_context, start_timestamp, end_timestamp):
    """Create the user prompt for subsequent video chunks."""
    return f"""The following part is part: {part_num} of the video. The video had to be broken down into 50 minute chunks, since it could not fit at once into your context, we have thus provided you with the context of the previous video parts here:
{total_previous_context}

You have to now work on the transcript and description for this video part provided, referencing previous context if required.

**Note:** Since you are part {part_num} of the video, your timestamps will not start from 00:00:00, but will start from: {start_timestamp} and end at {end_timestamp}, since timestamps are being considered with reference to original video and not with respect to the individual parts. Also remember that the timestamp is in HH:MM:SS and not MM:SS.

Please give the video's transcript and description here in XML format. Remember to follow all instructions and return rich and detailed video description using the specified XML structure:"""


def create_summarization_system_prompt():
    """Create system prompt for summarizing previous context."""
    return """You are tasked with summarizing the content of video parts to provide context for processing subsequent video parts. 

Your goal is to create a concise but comprehensive summary that captures:
1. The main topics covered
2. Key concepts and information presented
3. The overall flow and structure of the content
4. Important details that would be relevant for understanding future parts

Keep the summary informative but concise (aim for about 5000 tokens or less). Focus on content that would help understand the continuation of the video."""


def create_summarization_user_prompt(video_content):
    """Create user prompt for summarizing video content."""
    return f"""Please summarize the following video content to provide context for processing the next part of the video:

{video_content}

Provide a concise but comprehensive summary that captures the main topics, key concepts, and important details that would be relevant for understanding the continuation of the video."""


def parse_xml_to_json(xml_content):
    """Parse XML content to JSON format."""
    try:
        import re
        
        # Extract video information
        video_name_match = re.search(r'"video_name":\s*"([^"]*)"', xml_content)
        video_id_match = re.search(r'"video_id":\s*(\d+)', xml_content)
        video_available_match = re.search(r'"video_info_available":\s*(\d+)', xml_content)
        
        video_name = video_name_match.group(1) if video_name_match else "Unknown Video"
        video_id = int(video_id_match.group(1)) if video_id_match else 0
        video_available = int(video_available_match.group(1)) if video_available_match else 1
        
        # Extract all timestamps
        timestamp_pattern = r'<timestamp>(.*?)</timestamp>'
        timestamps = re.findall(timestamp_pattern, xml_content, re.DOTALL)
        
        video_content = []
        
        for i, timestamp_content in enumerate(timestamps):
            # Extract timestamp metadata
            timestamp_num_match = re.search(r'"video_timestamp_num":\s*(\d+)', timestamp_content)
            start_match = re.search(r'"timestamp_start":\s*"([^"]*)"', timestamp_content)
            end_match = re.search(r'"timestamp_end":\s*"([^"]*)"', timestamp_content)
            
            timestamp_num = int(timestamp_num_match.group(1)) if timestamp_num_match else i
            start_time = start_match.group(1) if start_match else "00:00:00"
            end_time = end_match.group(1) if end_match else "00:00:00"
            
            # Extract transcript content
            transcript_match = re.search(r'<timestamp_transcript_content>(.*?)</timestamp_transcript_content>', timestamp_content, re.DOTALL)
            transcript_content_match = re.search(r'"content":\s*"((?:[^"\\]|\\.)*)"', transcript_match.group(1)) if transcript_match else None
            transcript_content = transcript_content_match.group(1).replace('\\"', '"') if transcript_content_match else ""
            
            # Extract description content
            description_match = re.search(r'<timestamp_description_content>(.*?)</timestamp_description_content>', timestamp_content, re.DOTALL)
            description_content_match = re.search(r'"content":\s*"((?:[^"\\]|\\.)*)"', description_match.group(1), re.DOTALL) if description_match else None
            description_content = description_content_match.group(1).replace('\\"', '"') if description_content_match else ""
            
            timestamp_obj = {
                "video_timestamp_num": timestamp_num,
                "timestamp_start": start_time,
                "timestamp_end": end_time,
                "timestamp_transcript_content": {
                    "content_type": "text",
                    "content": transcript_content
                },
                "timestamp_description_content": {
                    "content_type": "text",
                    "content": description_content
                }
            }
            
            video_content.append(timestamp_obj)
        
        # Create final JSON structure
        result = [{
            "video_name": video_name,
            "video_id": video_id,
            "video_info_available": video_available,
            "video_content": video_content
        }]
        
        return result
        
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return None

def extract_json_from_response(response_text):
    """Extract XML from the response text and convert to JSON."""
    print(f"Extracting XML from response:\n{response_text}\n\n")
    
    # Look for <video_desc_doc> tags
    pattern = r'<video_desc_doc>(.*?)</video_desc_doc>'
    match = re.search(pattern, response_text, re.DOTALL)
    
    if match:
        xml_content = match.group(1).strip()
        try:
            return parse_xml_to_json(xml_content)
        except Exception as e:
            print(f"Error parsing XML to JSON: {e}")
            return None
    else:
        print("No XML block found in response")
        return None


async def get_video_description_chunk(genai_client, video_data, video_name, part_num=1, previous_context="", start_offset_seconds=0, end_offset_seconds=None):
    """
    Get video description for a single chunk using async API.
    
    Args:
        genai_client: The Google GenAI client
        video_data: Dictionary containing video information
        video_name: Name of the video
        part_num: Part number (1-indexed)
        previous_context: Context from previous parts
        start_offset_seconds: Start offset in seconds
        end_offset_seconds: End offset in seconds (None for full video)
    
    Returns:
        Tuple of (json_response, raw_response_text)
    """
    try:
        model = "gemini-2.5-flash-preview-05-20"
        
        # Create content parts
        content_parts = []
        
        # Add video content
        if video_data["video_type"] == "youtube":
            # For YouTube videos
            if end_offset_seconds is not None:
                # For chunked processing
                content_parts.append(
                    types.Part(
                        file_data=types.FileData(file_uri=video_data["url"]),
                        video_metadata=types.VideoMetadata(
                            start_offset=f'{start_offset_seconds}s',
                            end_offset=f'{end_offset_seconds}s'
                        )
                    )
                )
            else:
                # For full video
                content_parts.append(
                    types.Part(
                        file_data=types.FileData(file_uri=video_data["url"])
                    )
                )
        else:
            # For local video files
            with open(video_data["file_path"], "rb") as video_file:
                video_bytes = video_file.read()
                base64_data = base64.b64encode(video_bytes).decode()
            
            if end_offset_seconds is not None:
                # For chunked processing
                content_parts.append(
                    types.Part.from_bytes(
                        mime_type="video/mp4",
                        data=base64.b64decode(base64_data),
                        video_metadata=types.VideoMetadata(
                            start_offset=f'{start_offset_seconds}s',
                            end_offset=f'{end_offset_seconds}s'
                        )
                    )
                )
            else:
                # For full video
                content_parts.append(
                    types.Part.from_bytes(
                        mime_type="video/mp4",
                        data=base64.b64decode(base64_data)
                    )
                )
        
        # Add user prompt
        if part_num == 1:
            user_prompt = create_initial_user_prompt()
        else:
            start_timestamp = format_time_seconds_to_hms(start_offset_seconds)
            end_timestamp = format_time_seconds_to_hms(end_offset_seconds) if end_offset_seconds else "end"
            user_prompt = create_subsequent_user_prompt(part_num, previous_context, start_timestamp, end_timestamp)
        
        content_parts.append(types.Part.from_text(text=user_prompt))
        
        # Create contents
        contents = [types.Content(role="user", parts=content_parts)]
        
        # Generate content config
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=24576),
            response_mime_type="text/plain",
            system_instruction=[types.Part.from_text(text=create_video_system_prompt())],
        )
        
        print(f"Generating description for {video_name} part {part_num}...")
        
        # Use async API call
        response = await genai_client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )
        
        full_response = response.text if response.text else ""
        
        print(f"Completed description for {video_name} part {part_num}")
        
        # Extract JSON from response
        json_response = extract_json_from_response(full_response)
        
        return json_response, full_response
        
    except Exception as e:
        print(f"Error generating video description for {video_name} part {part_num}: {e}")
        return None, None


async def summarize_video_content(genai_client, video_content_text):
    """
    Summarize video content for context in subsequent parts.
    
    Args:
        genai_client: The Google GenAI client
        video_content_text: Text content to summarize
    
    Returns:
        Summarized text
    """
    try:
        model = "gemini-2.5-flash-preview-05-20"
        
        # Create contents
        contents = [
            types.Content(
                role="user", 
                parts=[types.Part.from_text(text=create_summarization_user_prompt(video_content_text))]
            )
        ]
        
        # Generate content config
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="text/plain",
            system_instruction=[types.Part.from_text(text=create_summarization_system_prompt())],
        )
        
        print("Summarizing previous video content...")
        
        # Generate content
        full_response = ""
        for chunk in genai_client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                full_response += chunk.text
        
        print("Completed summarization")
        return full_response.strip()
        
    except Exception as e:
        print(f"Error summarizing video content: {e}")
        return video_content_text  # Return original if summarization fails


def combine_video_parts(video_parts_json):
    """
    Combine multiple video part JSONs into a single JSON.
    
    Args:
        video_parts_json: List of JSON responses from different parts
    
    Returns:
        Combined JSON
    """
    if not video_parts_json:
        return []
    
    # Take the first part as base
    combined_json = video_parts_json[0].copy()
    
    # If there are multiple parts, combine their video_content
    if len(video_parts_json) > 1:
        for part_json in video_parts_json[1:]:
            if part_json and len(part_json) > 0:
                # Extend the video_content from subsequent parts
                combined_json[0]["video_content"].extend(part_json[0]["video_content"])
    
    return combined_json


async def process_single_video(genai_client, video_id, video_data, video_name):
    """
    Process a single video and generate its description.
    Handles chunking for videos longer than 50 minutes.
    
    Args:
        genai_client: The Google GenAI client
        video_id: Video ID
        video_data: Video data dictionary
        video_name: Name of the video
    
    Returns:
        JSON response for the video
    """
    try:
        # For now, we'll assume videos are less than 50 minutes
        # In a real implementation, you would need to determine video duration
        # and split accordingly
        
        # Process as single chunk
        json_response, raw_response = await get_video_description_chunk(
            genai_client, video_data, video_name, part_num=1
        )
        
        if json_response:
            # Update video_id and video_name in the response
            if len(json_response) > 0:
                json_response[0]["video_name"] = video_name
                json_response[0]["video_id"] = video_id
                json_response[0]["video_info_available"] = 1
        
        return json_response
        
    except Exception as e:
        print(f"Error processing video {video_name}: {e}")
        return None


async def generate_all_video_descriptions(genai_client, videos, video_order):
    """
    Generate descriptions for all videos in parallel.
    
    Args:
        genai_client: The Google GenAI client
        videos: Dictionary of video data
        video_order: List of video IDs in order
    
    Returns:
        Combined JSON response for all videos
    """
    try:
        # Create tasks for all videos
        tasks = []
        for i, video_id in enumerate(video_order):
            if video_id in videos:
                video_data = videos[video_id]
                video_name = video_data["file_name"]
                task = process_single_video(genai_client, i, video_data, video_name)
                tasks.append(task)
        
        # Process all videos in parallel
        print(f"Processing {len(tasks)} videos in parallel...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        combined_results = []
        for result in results:
            if isinstance(result, Exception):
                print(f"Error in video processing: {result}")
                continue
            if result and isinstance(result, list) and len(result) > 0:
                combined_results.extend(result)
        
        print(f"Successfully processed {len(combined_results)} videos")
        return combined_results
        
    except Exception as e:
        print(f"Error generating video descriptions: {e}")
        return []


async def generate_new_video_descriptions(genai_client, videos, video_order, existing_video_ids):
    """
    Generate descriptions for new videos only (not already processed) in parallel.
    
    Args:
        genai_client: The Google GenAI client
        videos: Dictionary of video data
        video_order: List of video IDs in order
        existing_video_ids: Set of video IDs that already have descriptions
    
    Returns:
        Combined JSON response for new videos only
    """
    try:
        # Create tasks only for new videos
        tasks = []
        new_video_ids = []
        
        for i, video_id in enumerate(video_order):
            if video_id in videos and video_id not in existing_video_ids:
                video_data = videos[video_id]
                video_name = video_data["file_name"]
                task = process_single_video(genai_client, i, video_data, video_name)
                tasks.append(task)
                new_video_ids.append(video_id)
        
        if not tasks:
            print("No new videos to process")
            return []
        
        # Process all new videos in parallel using async gather
        print(f"Processing {len(tasks)} new videos in parallel...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        combined_results = []
        for result in results:
            if isinstance(result, Exception):
                print(f"Error in video processing: {result}")
                continue
            if result and isinstance(result, list) and len(result) > 0:
                combined_results.extend(result)
        
        print(f"Successfully processed {len(combined_results)} new videos")
        return combined_results
        
    except Exception as e:
        print(f"Error generating video descriptions: {e}")
        return []


def save_video_descriptions_to_file(video_descriptions, json_folder):
    """
    Save video descriptions to JSON file.
    
    Args:
        video_descriptions: List of video description dictionaries
        json_folder: Path to JSON folder
    """
    try:
        video_file_path = os.path.join(json_folder, "video_structured_info.json")
        with open(video_file_path, "w", encoding="utf-8") as f:
            json.dump(video_descriptions, f, indent=2, ensure_ascii=False)
        print(f"Saved video descriptions to {video_file_path}")
    except Exception as e:
        print(f"Error saving video descriptions: {e}")