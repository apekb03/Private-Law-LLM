# ⚖️ Private Law LLM with RAG Application (Private Deployment)

This is a private Retrieval-Augmented Generation (RAG) application designed to analyze legal documents using **LLaMA 3.1** via **Ollama**, **ChromaDB** as the vector store, and **Streamlit** as the user interface. The entire stack is containerized with Docker and deployed on an AWS EC2 instance.

---

## 🚀 Quick Start (EC2 Deployment)

### 1. Launch EC2 Instance

- **Instance Type:** `m6i.2xlarge` (CPU) or `g4dn.xlarge` (GPU)
- **AMI:** Amazon Linux 2 or Ubuntu Server
- **Storage:** At least 100GB `gp3`
- **Security Group:**
  - **SSH** (port 22) — from your IP
  - **Streamlit** (port 8501) — from your IP
- **Key Pair:** Use an existing `.pem` file or create a new one

---

### 2. Connect to EC2 and Set Up Docker

```bash
chmod 400 your-key.pem
ssh -i your-key.pem ec2-user@<EC2_PUBLIC_IP>
For Amazon Linux:
bash
Copy
Edit
# Update system
sudo yum update -y

# Install Docker
sudo amazon-linux-extras install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user
newgrp docker

#Install Docker Compose:
VERSION=v2.27.0
sudo curl -L "https://github.com/docker/compose/releases/download/${VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
3. Upload Legal Documents
Upload your .txt files (totaling ~5GB) to the source_data/ directory on the EC2 instance:

scp -i your-key.pem -r /path/to/your/txt/files/* ec2-user@<EC2_PUBLIC_IP>:~/rag-app/source_data/
✅ Only .txt format is currently supported.

4. Ingest Data
From the EC2 instance:
cd ~/rag-app
docker-compose build streamlit_app
docker-compose run --rm streamlit_app python ingest.py

5. Run the Application
docker-compose up --build -d

Open your browser and go to:
http://<EC2_PUBLIC_IP>:8501

📁 Project Structure

rag-app/
├── app.py
├── ingest.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── source_data/

🔁 Development Notes
Use VSCode Remote - SSH for easy code edits

Restart the app after code changes:
docker-compose restart streamlit_app

Rebuild the app after updating dependencies:

docker-compose up --build -d
Use logs to debug:

bash

docker-compose logs -f
📌 Notes
Ollama will automatically download llama3.1:8b-instruct-q4_K_M on first run


