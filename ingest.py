# ingest.py
import os
import chromadb
import time
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader # Example loaders
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from chromadb.utils import embedding_functions # Use if providing embeddings explicitly

# --- Configuration ---
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
DATA_DIR = "/app/data"  # Directory where source data is mounted inside the container
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "rag_collection")
# Embedding model details (if ChromaDB handles embedding, this is informational)
# EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2" # Chroma's default if available

# Chunking parameters (adjust as needed)
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# --- ChromaDB Client Initialization ---
def get_chroma_client_ingest():
    """Initializes and returns a ChromaDB client for ingestion."""
    print(f"Attempting to connect to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}...")
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        # Retry connection
        for i in range(5): # Retry up to 5 times
            try:
                client.heartbeat()
                print("Successfully connected to ChromaDB.")
                return client
            except Exception as e:
                print(f"Connection attempt {i+1} failed: {e}. Retrying in 5 seconds...")
                time.sleep(5)
        print("Failed to connect to ChromaDB after multiple retries.")
        return None
    except Exception as e:
        print(f"Error initializing ChromaDB client: {e}")
        return None

# --- Main Ingestion Logic ---
def main():
    print("--- Starting Data Ingestion ---")

    chroma_client = get_chroma_client_ingest()
    if not chroma_client:
        print("Exiting: Could not establish connection to ChromaDB.")
        return

    # --- Get or Create Collection ---
    # If using Chroma's auto-embedding (default behavior usually), specify embedding function here
    # Or ensure the embedding model is available to the ChromaDB server instance.
    # default_ef = embedding_functions.DefaultEmbeddingFunction() # Example
    try:
        print(f"Getting or creating collection: '{CHROMA_COLLECTION_NAME}'")
        # collection = chroma_client.get_or_create_collection(
        #     name=CHROMA_COLLECTION_NAME,
        #     # embedding_function=default_ef # Uncomment if Chroma handles embeddings
        #     metadata={"hnsw:space": "cosine"} # Example: using cosine distance
        # )
        # If embeddings are generated *before* adding, don't specify embedding_function here
        collection = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)
        print(f"Using collection '{collection.name}'")
    except Exception as e:
        print(f"Error getting/creating collection: {e}")
        return

    # Check if data already exists (simple check, might need refinement)
    # existing_count = collection.count()
    # if existing_count > 0:
    #     print(f"Collection already contains {existing_count} documents. Skipping ingestion.")
    #     # Decide if you want to exit or maybe clear and re-ingest
    #     # To clear: chroma_client.delete_collection(name=CHROMA_COLLECTION_NAME)
    #     #          collection = chroma_client.create_collection(name=CHROMA_COLLECTION_NAME, ...)
    #     # return # Exit if already populated

    # --- Load Documents ---
    # Customize loaders based on your data. This example handles .txt and .pdf
    print(f"Loading documents from: {DATA_DIR}")
    # Check if directory exists
    if not os.path.isdir(DATA_DIR):
        print(f"Error: Data directory '{DATA_DIR}' not found or is not a directory.") #####################
        return

    try:
        # Using DirectoryLoader to handle multiple file types based on glob patterns
        # You might need to install specific loaders (e.g., 'pip install unstructured[pdf]')
        loader = DirectoryLoader(
            DATA_DIR,
            glob="**/*.*", # Load all files initially
            use_multithreading=True,
            show_progress=True,
            # Example: Define specific loaders per file type if needed
            # loader_cls={'*.txt': TextLoader, '*.pdf': PyPDFLoader}
        )
        documents = loader.load()
        if not documents:
            print(f"No documents found in '{DATA_DIR}'. Please ensure data is present.")
            return
        print(f"Loaded {len(documents)} documents.")

    except Exception as e:
        print(f"Error loading documents: {e}")
        return

    # --- Split Documents ---
    print("Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split documents into {len(chunks)} chunks.")

    if not chunks:
        print("No chunks generated. Exiting.")
        return

    # --- Prepare Data for ChromaDB ---
    # Extract text content, generate IDs, and prepare metadata
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    texts = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks] # Langchain loaders often add source metadata

    # --- Add to ChromaDB ---
    print(f"Adding {len(chunks)} chunks to ChromaDB collection '{collection.name}'...")
    batch_size = 100 # Add documents in batches
    for i in range(0, len(chunks), batch_size):
        batch_ids = ids[i:i+batch_size]
        batch_texts = texts[i:i+batch_size]
        batch_metadatas = metadatas[i:i+batch_size]

        try:
            # If Chroma handles embeddings (embedding_function set at collection creation):
            collection.add(
                 ids=batch_ids,
                 documents=batch_texts,
                 metadatas=batch_metadatas
            )
            # If providing embeddings yourself (e.g., using sentence-transformers):
            # batch_embeddings = your_embedding_function(batch_texts)
            # collection.add(
            #     ids=batch_ids,
            #     embeddings=batch_embeddings,
            #     documents=batch_texts,
            #     metadatas=batch_metadatas
            # )
            print(f"Added batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
        except Exception as e:
            print(f"Error adding batch starting at index {i} to ChromaDB: {e}")
            # Optional: Add retry logic or skip the batch

    print(f"--- Ingestion Complete ---")
    final_count = collection.count()
    print(f"Collection '{collection.name}' now contains {final_count} documents.")

if __name__ == "__main__":
    main()

