# ⚖️ Private Law LLM with RAG Application (Private Deployment)

This is a private **Retrieval-Augmented Generation (RAG) application** designed to analyze legal documents. It leverages **LLaMA 3.1** via **Ollama**, **ChromaDB** as the vector store, and **Streamlit** for the user interface. The entire stack is **containerized with Docker** and deployed on an **AWS EC2 instance**.

---

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
Locally from your terminal instance:
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
#You might need to run ingest.py inside the container
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
#Error Connecting to Ollama on EC2 
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









