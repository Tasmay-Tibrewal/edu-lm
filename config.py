"""
Configuration module for loading environment variables and initializing API clients.
"""
import dotenv
import os
from mistralai import Mistral
from openai import OpenAI
import google.generativeai as genai
from google import genai as google_genai
from google.genai import types

def load_env(filename=".env"):
    """
    Load environment variables from .env file.
    
    Args:
        filename: Path to the .env file
    """
    dotenv.load_dotenv()
    env_file = os.getenv("ENV_FILE", filename)
    if os.path.exists(env_file):
        dotenv.load_dotenv(env_file)
    else:
        print(f"Warning: Environment file '{env_file}' not found. Using default environment variables.")

def initialize_api_clients():
    """
    Initialize API clients for various services.
    
    Returns:
        Tuple of (mistral_client, openai_client, groq_client, openai_tts_client, model, genai_client)
    """
    # Load environment variables
    load_env()
    
    # Get API keys
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Validate API keys
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
    
    # Initialize Google Genai client for video processing
    genai_client = google_genai.Client(api_key=gemini_api_key)
    
    return mistral_client, openai_client, groq_client, openai_tts_client, model, genai_client