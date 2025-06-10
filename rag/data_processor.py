import re
from tqdm import tqdm
import time
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import (
    get_gemini_flash, CHUNK_SIZE, CHUNK_OVERLAP, 
    MIN_CONTEXT_WORDS, MAX_CONTEXT_WORDS
)

def parse_document(file_path):
    """Parses the document into a dictionary of pages."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Split by page tags like <1>, <2>, etc.
    pages_content = re.split(r'<\d+>', content)
    pages = {i: text.strip() for i, text in enumerate(pages_content) if text.strip()}
    print(f"Parsed {len(pages)} pages from the document.")
    return pages

def create_mini_documents(pages):
    """Groups pages into mini-documents of 3."""
    mini_docs = []
    page_keys = sorted(pages.keys())
    for i in range(0, len(page_keys), 3):
        mini_doc_pages = [pages[key] for key in page_keys[i:i+3]]
        start_page = page_keys[i]
        end_page = page_keys[min(i + 2, len(page_keys) - 1)]
        mini_docs.append({
            "content": "\n\n---\n\n".join(mini_doc_pages),
            "start_page": start_page,
            "end_page": end_page
        })
    print(f"Created {len(mini_docs)} mini-documents.")
    return mini_docs

def generate_enriched_contexts(mini_docs):
    llm = get_gemini_flash()
    enriched_contexts = {}
    preceding_text_summary = "This is the beginning of the document."

    print("Generating enriched contexts for each mini-document...")
    for i, doc in enumerate(tqdm(mini_docs, desc="Context Generation")):
        # ADDED: Strict word count constraint in the prompt
        prompt = f"""
        You are an expert at creating contextual summaries for document chunks.

        **Rules:**
        1. Start with the exact phrase: "This context is for pages {doc['start_page']} to {doc['end_page']}."
        2. Briefly summarize what these specific pages talk about.
        3. Briefly summarize all content that came before these pages, based on the 'Summary of Preceding Pages'.
        4. Briefly summarize the key visual elements described (e.g., images, diagrams, maps).
        5. Briefly summarize the key textual elements (e.g., geological concepts, definitions, methods).

        Your entire summary MUST be between {MIN_CONTEXT_WORDS} and {MAX_CONTEXT_WORDS} words.

        **Summary of Preceding Pages:**
        {preceding_text_summary}

        **Text from pages {doc['start_page']} to {doc['end_page']} to analyze:**
        ---
        {doc['content']}
        ---
        """
        response = llm.invoke(prompt)
        time.sleep(3)  # Rate limiting to avoid hitting API limits
        context = response.content
        enriched_contexts[i] = context
        preceding_text_summary += f"\n\nPages {doc['start_page']}-{doc['end_page']} discussed: {context}"

    return enriched_contexts

def chunk_the_document(pages, enriched_contexts, source_file_name):
    full_text = "\n\n".join(pages.values())
    char_chunk_size = CHUNK_SIZE * 6
    char_chunk_overlap = CHUNK_OVERLAP * 6

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=char_chunk_size,
        chunk_overlap=char_chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.create_documents([full_text])
    
    for chunk in chunks:
        first_part_of_chunk = chunk.page_content[:100].lower()
        chunk_page = 1
        for page_num, page_content in pages.items():
            if first_part_of_chunk in page_content.lower():
                chunk_page = page_num
                break
        
        mini_doc_index = (chunk_page - 1) // 3
        chunk.metadata['mini_doc_index'] = mini_doc_index
        chunk.metadata['enriched_context'] = enriched_contexts.get(mini_doc_index, "No context available.")
        chunk.metadata['source_page'] = chunk_page
        # ADDED: source_file metadata for tracking
        chunk.metadata['source_file'] = source_file_name

    print(f"Created {len(chunks)} chunks for '{source_file_name}' and enriched them with context.")
    return chunks

def process_single_file(file_path):
    """The main data processing pipeline for a single file."""
    pages = parse_document(file_path)
    if not pages:
        return []
    mini_docs = create_mini_documents(pages)
    enriched_contexts = generate_enriched_contexts(mini_docs)
    all_chunks = chunk_the_document(pages, enriched_contexts, file_path)
    return all_chunks