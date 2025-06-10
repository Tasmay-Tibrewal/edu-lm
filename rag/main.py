import logging
import config
from data_processor import process_single_file
from hybrid_rag import HybridRAG

def main():
    """Main function to run the entire RAG pipeline."""
    # Setup logging
    logging.basicConfig(
        filename=config.LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        filemode='w' # Overwrite log file on each run
    )
    logging.info("--- RAG System Initialized ---")
    
    # Initialize the RAG system, which connects to the DB
    rag_system = HybridRAG()
    
    # Conditionally process and embed data
    if config.PERFORM_DATA_PROCESSING:
        print("\n--- Starting Data Processing Phase ---")
        for file_path in config.FILE_PATHS:
            try:
                if not rag_system.is_file_processed(file_path):
                    new_chunks = process_single_file(file_path)
                    rag_system.add_documents(new_chunks)
                else:
                    # If you wanted to force reprocessing, you would add logic here
                    pass 
            except FileNotFoundError:
                print(f"Error: The file '{file_path}' was not found. Skipping.")
        print("--- Data Processing Phase Complete ---")
    else:
        print("\n--- Skipping Data Processing as per configuration ---")

    # Build the retrievers from all documents now in the database
    rag_system.build_retrievers()

    # Start the question-answering session
    print("\n--- Ready to Answer Questions ---")
    
    questions = [
        "What is the Darwinian method in science?",
        "Explain the difference between a normal fault and a reverse fault, including the stress regimes.",
        "What are the three structural levels of deformation in the continental crust?",
        "What is the difference between pure shear and simple shear?",
    ]
    
    for question in questions:
        print(f"\n🤔 Query: {question}")
        answer = rag_system.query(question)
        print(f"\n✅ Answer:\n{answer}")
        print("-" * 50)

if __name__ == "__main__":
    main()