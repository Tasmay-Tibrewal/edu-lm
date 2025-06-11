"""
Audio utilities module for speech-to-text and text-to-speech functionality.
"""
import tempfile

def transcribe_audio(audio_file, groq_client):
    """
    Transcribe audio using Groq's Whisper-large-v3 model.
    
    Args:
        audio_file: Audio file path or file object
        groq_client: Groq API client
        
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

def text_to_speech(text, openai_tts_client):
    """
    Convert text to speech using OpenAI's gpt-4o-mini-tts model.
    
    Args:
        text: Text to convert to speech
        openai_tts_client: OpenAI API client for TTS
        
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

def process_audio_input(audio_file, groq_client):
    """
    Process audio input through ASR and put text in input box.
    
    Args:
        audio_file: Recorded audio file
        groq_client: Groq API client
        
    Returns:
        Transcribed text for input box
    """
    if audio_file is None:
        return ""
    
    # Transcribe the audio
    transcribed_text = transcribe_audio(audio_file, groq_client)
    
    if transcribed_text and not transcribed_text.startswith("Error"):
        return f"🎤 {transcribed_text}"
    else:
        return ""

def get_last_response_and_convert_to_speech(chat_history, openai_tts_client):
    """
    Get the last assistant response and convert it to speech.
    
    Args:
        chat_history: Current chat history
        openai_tts_client: OpenAI API client for TTS
        
    Returns:
        Audio file path or None
    """
    if chat_history and len(chat_history) > 0:
        # Get the last assistant message
        for msg in reversed(chat_history):
            if msg["role"] == "assistant" and msg["content"] not in ["...", ""]:
                # Convert to speech
                audio_bytes = text_to_speech(msg["content"], openai_tts_client)
                if audio_bytes:
                    # Create a temporary file for Gradio to display
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                        temp_file.write(audio_bytes)
                        temp_file_path = temp_file.name
                    return temp_file_path
                else:
                    return None
    return None