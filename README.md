# AWS ECS ML Inference API - Iris Classification (Free Tier)

Containerized FastAPI + XGBoost inference API deployed on **AWS ECS (EC2 t3.micro Free Tier)** with ECR, ALB, and auto-scaling.

### Architecture Diagram
<img width="950" height="854" alt="image" src="https://github.com/user-attachments/assets/dfcf589e-f43a-42bc-ae58-76219c78a646" />
### Key AWS Services (Free Tier)

EC2 t3.micro (750 hours/month free)
ECR (private registry)
ECS (EC2 launch type)
Application Load Balancer (ALB)
CloudWatch monitoring
### Screenshots
<img width="1518" height="245" alt="image" src="https://github.com/user-attachments/assets/7705dce2-c572-431f-a8f1-f44d9d887272" />
<img width="1541" height="518" alt="image" src="https://github.com/user-attachments/assets/8167c675-299f-4068-96cb-e1a1d0d8e911" />
Service page - deployment in progres

### Local Run
Bash
python train.py
docker build -t iris-ml-api .
docker run -p 8000:8000 iris-ml-api

