# AWS Deployment Guide

This guide shows how to deploy Multi-Agent Research Assistant to AWS using:

- Amazon ECR for container image storage
- AWS ECS Fargate for the service runtime
- Amazon RDS PostgreSQL for persistent data storage
- Optional Amazon S3 for artifact persistence

## Prerequisites

- AWS account with IAM permissions for ECR, ECS, RDS, Secrets Manager, and CloudWatch
- AWS CLI installed and configured
- Docker installed locally for image build
- `aws` and `docker` available on your path

## 1. Build and push the Docker image

1. Authenticate to ECR:

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <your_account_id>.dkr.ecr.us-east-1.amazonaws.com
```

2. Create an ECR repository:

```bash
aws ecr create-repository --repository-name multi-agent-research-assistant --region us-east-1
```

3. Build the Docker image:

```bash
docker build -t multi-agent-research-assistant:latest .
```

4. Tag and push the image:

```bash
docker tag multi-agent-research-assistant:latest <your_account_id>.dkr.ecr.us-east-1.amazonaws.com/multi-agent-research-assistant:latest
docker push <your_account_id>.dkr.ecr.us-east-1.amazonaws.com/multi-agent-research-assistant:latest
```

## 2. Provision PostgreSQL using Amazon RDS

Use Amazon RDS for PostgreSQL as the production database.

```bash
aws rds create-db-instance \
  --db-instance-identifier researchos-db \
  --engine postgres \
  --db-instance-class db.t4g.micro \
  --allocated-storage 20 \
  --master-username researchos \
  --master-user-password "<strong_password>" \
  --backup-retention-period 7 \
  --vpc-security-group-ids <sg_id> \
  --availability-zone us-east-1a \
  --engine-version 16 \
  --publicly-accessible false
```

Wait until the DB instance is `available`.

## 3. Store secrets in AWS Secrets Manager

Create secrets for provider keys and JWT secret.

```bash
aws secretsmanager create-secret --name researchos/OPENROUTER_API_KEY --secret-string "{\"OPENROUTER_API_KEY\": \"<value>\"}"
aws secretsmanager create-secret --name researchos/SERPER_API_KEY --secret-string "{\"SERPER_API_KEY\": \"<value>\"}"
aws secretsmanager create-secret --name researchos/JWT_SECRET --secret-string "{\"JWT_SECRET\": \"<32+ byte secret>\"}"
```

## 4. Create an ECS task definition

Create a task definition using Fargate and the ECR image.

```json
{
  "family": "researchos-service",
  "executionRoleArn": "arn:aws:iam::<your_account_id>:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "researchos-api",
      "image": "<your_account_id>.dkr.ecr.us-east-1.amazonaws.com/multi-agent-research-assistant:latest",
      "portMappings": [
        {"containerPort": 8000, "hostPort": 8000, "protocol": "tcp"}
      ],
      "environment": [
        {"name": "APP_ENV", "value": "production"},
        {"name": "AUTH_REQUIRED", "value": "false"},
        {"name": "PORT", "value": "8000"},
        {"name": "DEFAULT_LLM", "value": "openrouter/meta-llama/llama-3.3-70b-instruct"}
      ],
      "secrets": [
        {"name": "OPENROUTER_API_KEY", "valueFrom": "arn:aws:secretsmanager:us-east-1:<your_account_id>:secret:researchos/OPENROUTER_API_KEY"},
        {"name": "SERPER_API_KEY", "valueFrom": "arn:aws:secretsmanager:us-east-1:<your_account_id>:secret:researchos/SERPER_API_KEY"},
        {"name": "JWT_SECRET", "valueFrom": "arn:aws:secretsmanager:us-east-1:<your_account_id>:secret:researchos/JWT_SECRET"}
      ],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/researchos",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## 5. Create an ECS service

Create a service using the task definition and attach it to a VPC and subnets.

```bash
aws ecs create-service \
  --cluster researchos-cluster \
  --service-name researchos-service \
  --task-definition researchos-service \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<subnet-id-1>,<subnet-id-2>],securityGroups=[<sg-id>],assignPublicIp=DISABLED}"
```

## 6. Configure an Application Load Balancer

Use an ALB with a target group that points to the ECS service on port 8000.
Set the health check path to `/health`.

## 7. Set `DATABASE_URL`

Use your RDS endpoint to configure the database URL:

```text
DATABASE_URL=postgresql+psycopg://researchos:<strong_password>@<rds_endpoint>:5432/researchos
```

If you use AWS Secrets/SSM, inject this value into the task definition as a secret instead of hardcoding it.

## 8. Optional: persist output artifacts

The application writes files under `/app/outputs`. In ECS/Fargate this path is ephemeral unless you attach an EFS volume or copy artifacts to S3.

- Use EFS for persistent `/app/outputs` storage
- Or export generated `report_path` values from the database and generate artifacts on demand

## Notes

- The Docker image supports `PORT`, so ECS can map any inbound port to container port 8000.
- `JWT_SECRET` must not be the default development value in production.
- For a fully managed AWS deployment, monitor CloudWatch logs and configure task auto-scaling.
