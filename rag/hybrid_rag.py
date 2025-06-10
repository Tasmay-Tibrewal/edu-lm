import logging
from rank_bm25 import BM25Okapi
from langchain_chroma import Chroma
from langchain_core.documents import Document
from config import get_gemini_embeddings, get_gemini_flash, VECTOR_DB_PATH

class HybridRAG:
    def __init__(self):
        self.llm = get_gemini_flash()
        self.embedding_function = get_gemini_embeddings()
        self.bm25 = None
        self.chunks_from_db = []
        
        print("Connecting to persistent VectorDB...")
        self.vector_store = Chroma(
            persist_directory=VECTOR_DB_PATH,
            embedding_function=self.embedding_function
        )
        print(f"Connected. DB contains {self.vector_store._collection.count()} documents.")

    def is_file_processed(self, file_path):
        """Checks if a file has already been processed and embedded in the DB."""
        results = self.vector_store.get(where={"source_file": file_path})
        is_processed = len(results.get("ids", [])) > 0
        if is_processed:
            print(f"File '{file_path}' has already been processed. Skipping.")
        return is_processed

    def add_documents(self, new_chunks):
        """Adds a list of new documents (chunks) to the vector store."""
        if not new_chunks:
            return
        print(f"Adding {len(new_chunks)} new chunks to the vector store...")
        self.vector_store.add_documents(new_chunks)
        print("Addition complete.")

    def build_retrievers(self):
        """Builds the lexical (BM25) retriever from all documents in the DB."""
        print("Building retrievers from all documents in the database...")
        self.chunks_from_db = self.vector_store.get(include=["metadatas", "documents"])
        
        # Reconstruct Document objects for BM25
        all_docs = [
            Document(page_content=doc, metadata=meta)
            for doc, meta in zip(self.chunks_from_db['documents'], self.chunks_from_db['metadatas'])
        ]
        
        if not all_docs:
            print("No documents in DB to build retrievers from. The RAG will not work.")
            return

        self.raw_texts = self.chunks_from_db['documents']
        tokenized_corpus = [doc.split(" ") for doc in self.raw_texts]
        self.bm25 = BM25Okapi(tokenized_corpus)
        print(f"BM25 retriever built on {len(self.raw_texts)} documents.")
    

    def _rerank_results(self, query, docs):
        """Reranks documents using the LLM based on relevance to the query."""
        if not docs:
            return []
            
        prompt = f"""
        You are a highly intelligent relevance-ranking assistant.
        I have a user query and a list of text snippets. Your task is to reorder the snippets based on how relevant they are to answering the query.
        The most relevant snippet should be first. Do not add any explanation or commentary, just output the reordered snippets separated by '---'.

        **User Query:** {query}

        **Snippets to rank:**
        """
        for i, doc in enumerate(docs):
            prompt += f"\n--- Snippet {i+1} ---\n{doc.page_content}\n"
        
        response = self.llm.invoke(prompt)
        
        ranked_content = response.content.split('---')
        doc_map = {doc.page_content.strip(): doc for doc in docs}
        
        reranked_docs = []
        for content in ranked_content:
            cleaned_content = content.strip()
            if cleaned_content in doc_map:
                reranked_docs.append(doc_map[cleaned_content])

        return reranked_docs if reranked_docs else docs

    def query(self, user_query, top_k=10):
        if not self.bm25:
            return "Retriever has not been built. Please process data first."
httio to http
        # 1. Vector Search
        vector_results = self.vector_store.similarity_search(user_query, k=top_k)
        
        # 2. BM25 Lexical Search
        tokenized_query = user_query.split(" ")
        bm25_scores = self.bm25.get_scores(tokenized_query)
        top_bm25_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k]
        
        # Reconstruct Document objects from the indices
        all_docs = [
            Document(page_content=doc, metadata=meta)
            for doc, meta in zip(self.chunks_from_db['documents'], self.chunks_from_db['metadatas'])
        ]
        bm25_results = [all_docs[i] for i in top_bm25_indices]
        
        # 3. Combine and Deduplicate
        combined_results = {doc.page_content: doc for doc in vector_results + bm25_results}.values()
        
        # 4. Rerank
        reranked_docs = self._rerank_results(user_query, list(combined_results))
        top_reranked = reranked_docs[:top_k]
        
        # 5. Log retrieved chunks
        logging.info(f"Query: {user_query}")
        print(f"\n--- Top {len(top_reranked)} Retrieved Chunks ---")
        for i, doc in enumerate(top_reranked):
            log_message = f"  Chunk {i+1} (Source: {doc.metadata.get('source_file', 'N/A')}, Page: {doc.metadata.get('source_page', 'N/A')}):\n{doc.page_content}\n"
            logging.info(log_message)
            print(log_message)
        
        # 6. Generate Final Answer
        if not top_reranked:
            return "I could not find any relevant information to answer your question."
            
        final_context = top_reranked[0].metadata.get('enriched_context', '')
        retrieved_snippets = "\n\n---\n\n".join([doc.page_content for doc in top_reranked])

        final_prompt = f"""
        You are a helpful and knowledgeable assistant specializing in geology.
        Please answer the user's query based ONLY AND ONLY from the provided context and retrieved snippets.
        Be concise and directly address the question.

        **Enriched Context for the retrieved information:**
        {final_context}

        **Retrieved Snippets:**
        {retrieved_snippets}

        **User Query:**
        {user_query}

        **Your Answer:**
        """
        
        final_answer = self.llm.invoke(final_prompt)
        return final_answer.content