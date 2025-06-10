import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# Load environment variables from .env file
load_dotenv()

# --- High-Level Controls ---
# Set to False to skip all data processing and use the existing database
PERFORM_DATA_PROCESSING = True

# List of document files to be processed and embedded.
FILE_PATHS = ["geology.txt"] # Add more files like ["geology.txt", "physics.txt"]

# --- Logging ---
LOG_FILE = "rag_query_log.txt"

# --- Chunking and Context Parameters ---
CHUNK_SIZE = 200  # Target words per chunk
CHUNK_OVERLAP = 50 # Target words for overlap
# Word count limits for the LLM-generated contextual summary
MIN_CONTEXT_WORDS = 150
MAX_CONTEXT_WORDS = 250

# --- Database Path ---
VECTOR_DB_PATH = "./chroma_db_"

def configure_api_keys():
    """Validates that the Google API key is set in the environment."""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY is not set. Please create a .env file and add your key.")
    return google_api_key

# --- Language Model for Generation and Summarization ---
def get_gemini_flash():
    """Initializes and returns the Gemini 1.5 Flash model for generation."""
    google_api_key = configure_api_keys()
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=google_api_key,
        temperature=0.1,
        convert_system_message_to_human=True
    )

# --- Embedding Model (API-based) ---
def get_gemini_embeddings():
    """Initializes and returns the Google Generative AI embedding model."""
    google_api_key = configure_api_keys()
    return GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=google_api_key
    )