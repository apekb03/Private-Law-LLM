# Dockerfile for Streamlit RAG App

# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Use --no-cache-dir to reduce image size
# Install system dependencies that might be needed by some python packages (e.g., build-essential for compiling)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install python packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
    RUN pip install tqdm
    RUN pip install onnxruntime
    RUN pip install tokenizers
    RUN pip install unstructured


# Copy the rest of the application code into the container
COPY . .

# Make port 8501 available to the world outside this container (Streamlit default port)
EXPOSE 8501

# Define environment variable (optional, can be set in docker-compose)
# ENV OLLAMA_BASE_URL=http://ollama:11434
# ENV CHROMA_HOST=chromadb
# ENV CHROMA_PORT=8000

# Command to run the Streamlit application
# Use --server.address 0.0.0.0 to allow connections from outside the container
# Use --server.enableCORS false and --server.enableXsrfProtection false for easier embedding/proxying if needed (use with caution)
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]


