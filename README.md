# ⚖️ Private Law LLM with RAG Application(Private Deployment)

This is a private Retrieval-Augmented Generation (RAG) application designed to analyze legal documents using LLaMA 3.1 via Ollama, ChromaDB as the vector store, and Streamlit as the user interface. The entire stack is containerized with Docker and deployed on an AWS EC2 instance.


## 🚀 Quick Start (EC2 Deployment)

### 1. Launch EC2 Instance

- **Instance type:** `m6i.2xlarge` (CPU) or `g4dn.xlarge` (GPU)
- **AMI:** Amazon Linux 2 or Ubuntu Server
- **Storage:** At least 100GB `gp3`
- **Security group:**
  - SSH (port 22) from **your IP**
  - Streamlit (port 8501) from **your IP**
- **Key pair:** Use an existing `.pem` or create a new one


### 2. Connect to EC2

```bash
chmod 400 your-key.pem
ssh -i your-key.pem ec2-user@<EC2_PUBLIC_IP>```


#For Amazon Linux
```sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user
newgrp docker```

# Install Docker Compose 
VERSION=v2.27.0
```sudo curl -L "https://github.com/docker/compose/releases/download/${VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose```

Upload your legal documents (~5GB) to the source_data
.txt format supported

#ingest data
`docker-compose build streamlit_app`
`docker-compose run --rm streamlit_app python ingest.py`


