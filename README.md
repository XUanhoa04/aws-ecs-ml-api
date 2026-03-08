# AWS ECS ML Inference API (Iris Classification with XGBoost)

End-to-end MLOps project: Deploy containerized FastAPI + XGBoost model on **AWS ECS (EC2 Free Tier)** with ECR, ALB, auto-scaling, and GitHub Actions CI/CD.

## Architecture Overview
- Model: XGBoost on Iris dataset (scikit-learn)
- App: FastAPI inference API (/predict endpoint)
- Container: Dockerized
- Registry: AWS ECR
- Orchestration: AWS ECS (EC2 launch type - t3.micro Free Tier)
- Load Balancing: Application Load Balancer (public endpoint)
- Monitoring: CloudWatch Logs
- Auto Scaling: CPU-based

![Architecture Diagram](https://i.imgur.com/your-diagram-link.png)  <!-- Nếu bạn vẽ diagram bằng draw.io và upload lên GitHub hoặc Imgur -->

## Public Endpoint (Demo)
- ALB DNS: http://iris-ml-alb-xxxxxx.ap-southeast-1.elb.amazonaws.com
- Swagger UI: http://iris-ml-alb-xxxxxx.ap-southeast-1.elb.amazonaws.com/docs
- Example predict:
  ```json
  POST /predict
  {
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2
  }