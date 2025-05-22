# app.py
import streamlit as st
import chromadb
import requests
import os
import json
import time

# --- Configuration ---
# Get connection details from environment variables set in docker-compose
OLLAMA_BASE_URL = os.getenv( "OLLAMA_BASE_URL", "http://localhost:11434")
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.1:8b-instruct-q4_K_M") # Default model
# DATA_DIR = "/app/data" # Directory where source data is mounted (used by ingest.py)
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "rag_collection")
print("THIS is CHROMA_COLLECTION_NAME",CHROMA_COLLECTION_NAME,"\n")

# --- Helper Functions ---

@st.cache_resource(ttl=3600) # Cache the ChromaDB client connection for 1 hour
def get_chroma_client():
    """Initializes and returns a ChromaDB client."""
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        # Perform a heartbeat check - increases robustness
        for _ in range(3): # Retry connection
            try:
                client.heartbeat() #checks if the system is running correctly
                st.success(f"Connected to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}")
                return client
            except Exception as e:
                print(f"ChromaDB connection attempt failed: {e}")
                time.sleep(2)
        st.error(f"Failed to connect to ChromaDB after retries at {CHROMA_HOST}:{CHROMA_PORT}")
        return None
    except Exception as e:
        st.error(f"Error initializing ChromaDB client: {e}")
        return None

@st.cache_resource(ttl=3600) # Cache the collection object for 1 hour
def get_chroma_collection(_client: chromadb.Client, collection_name: str):
    """Gets or creates a ChromaDB collection."""
    if not _client:
        st.warning("ChromaDB client not available, cannot get collection.")
        return None
    try:
        # Get the collection. Assumes it was created by ingest.py
        # If using Chroma's auto-embedding, the embedding function is implicitly handled.
        collection = _client.get_collection(name=collection_name)
        st.info(f"Successfully accessed ChromaDB collection: '{collection_name}'")
        return collection
    except Exception as e:
        # Handle case where collection might not exist yet
        st.error(f"Failed to get ChromaDB collection '{collection_name}'. Was the ingestion script run successfully? Error: {e}")
        # Optionally try to create it, but better to rely on ingest script
        # try:
        #     st.warning(f"Collection '{collection_name}' not found. Attempting to create...")
        #     # Specify embedding function if Chroma handles embedding
        #     # from chromadb.utils import embedding_functions
        #     # default_ef = embedding_functions.DefaultEmbeddingFunction()
        #     collection = _client.get_or_create_collection(
        #           name=collection_name,
        #           # embedding_function=default_ef # Uncomment if needed
        #           )
        #     st.info(f"Created collection '{collection_name}'. It might be empty.")
        #     return collection
        # except Exception as create_e:
        #     st.error(f"Failed to create collection '{collection_name}': {create_e}")
        #     return None
        return None # Explicitly return None if get fails

def query_chromadb(collection, query_text: str, n_results: int = 5):
    """Queries the ChromaDB collection."""
    if not collection:
        st.warning("ChromaDB collection not available for querying.")
        return []
    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            include=['documents'] # Only fetch documents needed for context
        )
        # Extract relevant documents, handle potential empty results
        docs = results.get('documents', [[]])[0]
        return docs if docs else [] # Return list of document strings
    except Exception as e:
        st.error(f"Error querying ChromaDB: {e}")
        return []

def ollama_generate(model: str, prompt: str, context_docs: list = None):
    """Sends a request to the Ollama API and streams the response."""
    full_prompt = prompt
    if context_docs:
        context_str = "\n\n".join(context_docs)
        # Basic RAG prompt structure - IMPROVE THIS BASED ON YOUR NEEDS
        full_prompt = f"""Use the following pieces of context to answer the question at the end. If you don't know the answer from the context provided, just say that you don't know, don't try to make up an answer. Keep the answer concise.

Context:
{context_str}

Question: {prompt}

Answer:"""
    else:
         # Add instruction if no context is provided
         full_prompt = f"Question: {prompt}\n\nAnswer:"


   # api_url = f"{OLLAMA_BASE_URL}/api/generate"
    api_url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": True, # Use streaming for better UX
        "options": { # Add some Ollama options if desired
            "num_ctx": 4096, # Example context window size
            "temperature": 0.7 # Example temperature
        }
    }
    try:
        response = requests.post(api_url, json=payload, stream=True, timeout=180) # Longer timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        buffer = ""
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line.decode('utf-8'))
                    if 'response' in chunk:
                        buffer += chunk['response']
                        yield buffer # Yield the accumulated response so far
                    if chunk.get('done', False):
                        if chunk.get('error'): # Check for errors reported by Ollama
                            st.error(f"Ollama generation error: {chunk['error']}")
                        break # Exit loop when Ollama signals completion
                except json.JSONDecodeError:
                    st.warning(f"Received non-JSON response chunk: {line.decode('utf-8')}")
                except Exception as e:
                    st.error(f"Error processing Ollama stream chunk: {e}")
                    break # Stop processing on error

    except requests.exceptions.Timeout:
         st.error(f"Ollama API request timed out after 180 seconds. The model might be taking too long to respond.")
         yield "Error: Ollama request timed out."
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to Ollama API at {api_url}: {e}")
        st.error("Ensure the Ollama service is running and the model is available/downloaded.")
        yield f"Error: Could not connect to Ollama. {e}" # Yield error message
    except Exception as e:
        st.error(f"An unexpected error occurred during Ollama generation: {e}")
        yield f"Error: An unexpected error occurred. {e}" # Yield error message


# --- Streamlit App UI ---
st.set_page_config(layout="wide", page_title="RAG App")
st.title("Private Law LLM with RAG App")

st.markdown(f"Using Ollama model: **{MODEL_NAME}** | ChromaDB: `{CHROMA_HOST}:{CHROMA_PORT}` | Collection: `{CHROMA_COLLECTION_NAME}`")

# Initialize clients and collection
chroma_client = get_chroma_client()
chroma_collection = get_chroma_collection(chroma_client, CHROMA_COLLECTION_NAME)

# Check collection status (simple count)
collection_status = "Not connected"
if chroma_collection:
    try:
        count = chroma_collection.count()
        collection_status = f"'{CHROMA_COLLECTION_NAME}' contains {count} documents."
        if count == 0:
             st.warning(f"Collection '{CHROMA_COLLECTION_NAME}' is empty. Please run the ingestion script (`docker-compose run --rm streamlit_app python ingest.py`).")
    except Exception as e:
        collection_status = f"Error checking collection status: {e}"
        st.error(collection_status)
elif not chroma_client:
    collection_status = "ChromaDB client connection failed."
    st.error(collection_status)
else:
     collection_status = f"Collection '{CHROMA_COLLECTION_NAME}' not found or inaccessible."
     st.error(collection_status)

st.sidebar.info(f"**Status:**\n{collection_status}")

st.sidebar.header("Options")
n_results = st.sidebar.slider("Number of relevant chunks to fetch:", 1, 10, 3, key="n_results_slider")
use_rag = st.sidebar.toggle("Use RAG (fetch context from ChromaDB)", value=True, key="use_rag_toggle")



# -----------add knowledgebase section------------------
from langchain.text_splitter import RecursiveCharacterTextSplitter
# … inside your Streamlit code, e.g. after defining n_results/use_rag …
st.sidebar.header(":heavy_plus_sign: Add to Knowledge Base")
new_doc = st.sidebar.text_area("Paste or type new document text here:")
if st.sidebar.button("Save & Ingest"):
    if new_doc.strip():
        # 1. Write it to a file in /app/data
        ts = int(time.time())
        fname = f"/app/data/user_doc_{ts}.txt"
        try:
            with open(fname, "w") as f:
                f.write(new_doc)
            st.sidebar.success(f"Saved document as `{fname}`")
        except Exception as e:
            st.sidebar.error(f"Failed to write file: {e}")
            fname = None
        # 2. Chunk & ingest into existing Chroma collection
        if fname and chroma_collection:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=150
            )
            chunks = splitter.split_text(new_doc)
            ids = [f"user_{ts}_{i}" for i in range(len(chunks))]
            metas = [{"source": fname} for _ in chunks]
            try:
                chroma_collection.add(
                    ids=ids,
                    documents=chunks,
                    metadatas=metas
                )
                st.sidebar.success(f"Ingested {len(chunks)} new chunks.")
            except Exception as e:
                st.sidebar.error(f"Ingestion error: {e}")
    else:
        st.sidebar.warning("Please enter some text first.")


        
st.header("Ask a Question")
# Use session state to keep track of query
if 'user_query' not in st.session_state:
    st.session_state.user_query = ""

user_query = st.text_input("Enter your question:", value=st.session_state.user_query, key="query_input")

# Button to trigger generation
submit_button = st.button("Generate Response")

if submit_button and user_query:
    st.session_state.user_query = user_query # Store query
    retrieved_docs = []
    if use_rag and chroma_collection:
        with st.spinner("Searching relevant documents in ChromaDB..."):
            retrieved_docs = query_chromadb(chroma_collection, user_query, n_results=n_results)

        # Display retrieved context only if RAG was used and docs were found
        if retrieved_docs:
            st.subheader("Retrieved Context:")
            with st.expander("Show Context Documents", expanded=False):
                for i, doc in enumerate(retrieved_docs):
                    st.markdown(f"**Document {i+1}:**")
                    st.caption(doc[:500] + "..." if len(doc) > 500 else doc) # Show snippet
        elif use_rag:
            st.warning("Could not retrieve relevant documents from ChromaDB for this query.")

    elif use_rag and not chroma_collection:
         st.warning("RAG enabled, but ChromaDB connection failed or collection is inaccessible.")

    st.subheader("LLM Response:")
    # Prepare arguments for Ollama
    ollama_args = {"model": MODEL_NAME, "prompt": user_query}
    if use_rag:
        ollama_args["context_docs"] = retrieved_docs # Pass context if RAG is used

    # Use a placeholder for streaming output
    response_placeholder = st.empty()
    full_response = ""
    try:
        with st.spinner(f"Generating response with {MODEL_NAME}..."):
            # Stream the response from Ollama
            for partial_response in ollama_generate(**ollama_args):
                full_response = partial_response
                response_placeholder.markdown(full_response) # Update placeholder with streamed content
            # Ensure the final complete response is displayed (optional, usually covered by last yield)
            # response_placeholder.markdown(full_response)
    except Exception as e:
        st.error(f"An error occurred during response generation: {e}")

elif not user_query and submit_button:
    st.warning("Please enter a question.")

# Keep the input field populated if needed
# st.text_input("Enter your question:", value=st.session_state.user_query, key="query_input_redisplay")



