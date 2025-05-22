# Private Law LLM with RAG Application (Private Deployment)

## Project Description

One of the biggest challenges facing businesses today—especially in fields like law, healthcare, and finance—is **data privacy** when using Large Language Models (LLMs). Most commercial LLM solutions pose serious concerns around **data breaches** and **cloud-based data exposure**, making them unsuitable for handling sensitive or client-owned data.

### Problem

Imagine a law firm wanting to access historical case files from as far back as 1980. Traditionally, this involves paralegals manually retrieving and reviewing documents—a process that is time-consuming, error-prone, and expensive.

While LLMs can automate this work, **clients are understandably concerned** about sending confidential data to third-party servers owned by tech giants.

---

### Our Solution

This RAG-powered legal assistant solves that.

- **Local Deployment**: This bot runs **entirely on your machine or private server**. No data leaves your environment.
- **Privacy-First**: All document processing and embedding are performed locally. Nothing is uploaded to the cloud.
- **Retrieval-Augmented Generation (RAG)**: A technique that improves LLM responses by pulling context directly from your provided documents before answering.
- **Modular Architecture**: Easily updatable document base—new cases or data can be added anytime and ingested without retraining the model.

---

### Tech Stack

- **Frontend**: `rag_streamlit_app` — A clean Streamlit interface to interact with your private legal assistant.
- **Vector Store**: `ChromaDB` — Stores embeddings and enables fast, semantic retrieval.
- **LLM Backend**: `rag_ollama` — Uses the Ollama runtime to run LLaMA 3.1 locally (offline or online).
- **Ingestion Pipeline**: `ingest.py` — Preprocesses and chunks your `.txt` legal documents and stores them in ChromaDB.
- 
---

### Demo Images
#### Initial Screen  
The landing interface of the Streamlit-based legal assistant. 
![1](https://github.com/user-attachments/assets/ee757bdf-6e6f-44fd-bdf2-4ab2f71cee91)

### Document-Based Answering  
Ollama uses the `.txt` files you provide to generate answers based on your custom legal documents.  
![2](https://github.com/user-attachments/assets/a7d2585c-e810-4ed7-bc63-8f00af37e7b3)

### Context Retrieval Display  
The app shows the exact retrieved context used by the LLM to formulate its response, ensuring transparency.  
![3](https://github.com/user-attachments/assets/4e928da9-a72a-4744-8507-0d7b09b48048)

### Toggle RAG On/Off  
You can disable retrieval to confirm privacy — when off, the model cannot answer questions based on your data, proving it’s not uploading anything externally.  
![4](https://github.com/user-attachments/assets/7a7d5871-6430-4186-a201-fbd0e88e36df)



## Quick Start (EC2 Deployment)

### 1. Launch EC2 Instance

* **Instance Type:** `m6i.2xlarge` (CPU) or `g4dn.xlarge` (GPU)
* **AMI:**  Ubuntu Server or Amazon Linux 2 
* **Storage:** At least **100GB gp3**
* **Security Group:**
    * **SSH** (port 22) — from your IP
    * **Streamlit** (port 8501) — from your IP
* **Key Pair:** Use an existing `.pem` file or create a new one.

### 2. Connect to EC2 and Set Up Docker
```
chmod 400 your-key.pem
ssh -i your-key.pem ec2-user@<EC2_PUBLIC_IP>
```
*#For help with setting up key-pair on EC2 instance visit:*
https://www.youtube.com/watch?v=eFA7Kd8Oqok&t=3s


### 3. Use terminal to access the EC2 instance 
https://www.youtube.com/watch?v=eFA7Kd8Oqok&t=3s

### 4. Upload your .txt files (totaling ~5GB) to the source_data/ directory on the EC2 instance:
   *#You can also create a .txt file inside the source_data folder*
```
# Example: Uploading a directory named 'my_local_data'
scp -i /path/to/your-key-pair.pem -r /path/to/my_local_data/* ec2-user@<your_ec2_public_ip>:~/rag-app/source_data/
```


### 5. Ingest Data
In EC2 instance:
```
cd ~/rag-app
docker-compose build streamlit_app
docker-compose run --rm streamlit_app python ingest.py
```

### 6. Run the Application

```
docker-compose up --build -d
```
Open your browser and go to: 
```
http://<EC2_PUBLIC_IP>:8501
```

### Project Structure
```
rag-app/
├── app.py
├── ingest.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── source_data/
└── documentation/ (optional)
```

### Development Notes

Restart the app after code changes:
```
docker-compose restart streamlit_app
```
Rebuild the app after updating dependencies:
```
docker-compose up --build -d
```
Use logs to debug:
```
docker-compose logs -f
```
### Other Notes 
Ollama will automatically download llama3.1:8b-instruct-q4_K_M on the first run.

### Possible Errors:
# You might need to run ingest.py inside the container
```
docker exec -it rag_streamlit_app bash
```
then 
```
python ingest.py
```
then 
```
exit
```
# Error Connecting to Ollama on EC2 
Need to manually pull ollama model within ollama container
```
docker-compose exec ollama ollama list
```
then 
```
ollama pull llama3.1:8b-instruct-q4_K_M
```
then 
```
exit
```









