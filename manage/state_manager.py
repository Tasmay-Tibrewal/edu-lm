"""
State management module for handling application state.
"""
import json
from .data_manager import save_chat_history, save_llm_call_payload, save_docs_structured_info, initialize_json_files

def reset_all_state(documents, document_order, videos, video_order, 
                   llm_chat_history, llm_chat_history_show,
                   document_positions, chat_position_counter, structured_docs_cache):
    """
    Reset all internal state and JSON files when interface loads/reloads.
    
    Args:
        documents: Dictionary of document data
        document_order: List of document IDs in order
        videos: Dictionary of video data
        video_order: List of video IDs in order
        llm_chat_history: LLM chat history
        llm_chat_history_show: Truncated LLM chat history
        document_positions: Dictionary mapping document IDs to positions
        chat_position_counter: Counter for chat positions
        structured_docs_cache: In-memory cache for structured document information
        
    Returns:
        Tuple of (documents, document_order, videos, video_order, llm_chat_history, 
                 llm_chat_history_show, document_positions, chat_position_counter, 
                 structured_docs_cache)
    """
    # Clear all internal state
    documents.clear()
    document_order.clear()
    videos.clear()
    video_order.clear()
    llm_chat_history = None
    llm_chat_history_show = None
    document_positions.clear()
    chat_position_counter = 0
    structured_docs_cache = []  # Clear the structured documents cache
    
    # Clear all JSON files
    initialize_json_files()
    
    print("Reset all state and JSON files on interface reload")
    
    return (documents, document_order, videos, video_order, llm_chat_history, 
            llm_chat_history_show, document_positions, chat_position_counter, 
            structured_docs_cache)

def add_user_and_placeholder(message, chat_history):
    """
    Immediately append the user's message and a placeholder ('...') for the assistant,
    so the user sees their own prompt and an empty assistant bubble right away.
    
    Args:
        message: User message
        chat_history: Current chat history
        
    Returns:
        Updated chat history
    """
    # If there's no chat_history, start a fresh list
    if chat_history is None:
        chat_history = []
    
    # Append user message
    chat_history.append({"role": "user", "content": message})
    # Append a placeholder assistant message (we'll replace '...' as we stream)
    chat_history.append({"role": "assistant", "content": "..."})

    # Save chat history after user query is added
    save_chat_history(chat_history)

    return chat_history

def clear_chat(llm_chat_history, llm_chat_history_show, document_positions, chat_position_counter):
    """
    Clear chat history and reset chat state.
    
    Args:
        llm_chat_history: LLM chat history
        llm_chat_history_show: Truncated LLM chat history
        document_positions: Dictionary mapping document IDs to positions
        chat_position_counter: Counter for chat positions
        
    Returns:
        Tuple of (empty chat history, llm_chat_history, llm_chat_history_show, 
                 document_positions, chat_position_counter)
    """
    llm_chat_history = None
    llm_chat_history_show = None
    document_positions = {}
    chat_position_counter = 0
    
    # Save cleared state to JSON files
    save_chat_history([])
    save_llm_call_payload([], [])
    
    return [], llm_chat_history, llm_chat_history_show, document_positions, chat_position_counter

def stream_assistant_reply(message, chat_history, documents, document_order, llm_chat_history, llm_chat_history_show, document_positions, chat_position_counter, openai_client):
    """
    Streaming function that replaces the placeholder '...' with actual tokens from Gemini.
    Yields updated chat_history on each chunk. Keeps spinner until first chunk arrives.
    
    Args:
        message: User message
        chat_history: Current chat history
        documents: Dictionary of document data
        document_order: List of document IDs in order
        llm_chat_history: LLM chat history
        llm_chat_history_show: Truncated LLM chat history
        document_positions: Dictionary mapping document IDs to positions
        chat_position_counter: Counter for chat positions
        openai_client: OpenAI API client
        
    Yields:
        Updated chat history
        
    Returns:
        Tuple of (chat_history, llm_chat_history, llm_chat_history_show, document_positions, chat_position_counter)
    """
    # If no documents are uploaded, just replace the placeholder with an error message
    if not documents:
        response_text = "Please upload a PDF document first."
        if chat_history is None:
            chat_history = []
        # We assume add_user_and_placeholder already put user+ '...' in chat_history
        # Overwrite that '...' with the error
        chat_history[-1]["content"] = response_text
        yield chat_history
        return chat_history, llm_chat_history, llm_chat_history_show, document_positions, chat_position_counter

    try:
        # Build or retrieve the LLM context messages
        if llm_chat_history is None:
            from ..utils.document_utils import create_chat_messages_for_llm
            document_messages, document_messages_show, document_positions, chat_position_counter = create_chat_messages_for_llm(
                documents, document_order, document_positions, chat_position_counter
            )
        else:
            document_messages, document_messages_show = llm_chat_history, llm_chat_history_show

        user_message = f"# User question:\n"
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
        
        # Save updated chat history and LLM payload after response
        save_chat_history(chat_history)
        save_llm_call_payload(llm_chat_history, llm_chat_history_show)

        return chat_history, llm_chat_history, llm_chat_history_show, document_positions, chat_position_counter

    except Exception as e:
        error_message = f"Error generating response: {str(e)}"
        print(f"Error details: {e}")
        # Overwrite placeholder with error
        chat_history[-1]["content"] = error_message
        
        # Save chat history even on error
        save_chat_history(chat_history)
        
        yield chat_history
        return chat_history, llm_chat_history, llm_chat_history_show, document_positions, chat_position_counter