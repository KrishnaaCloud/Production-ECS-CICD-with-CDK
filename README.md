# AWS ECS CI/CD using CDK

This project demonstrates a production-grade CI/CD pipeline for deploying
a containerized application to Amazon ECS using AWS CDK.

## Architecture
- ECS (EC2 launch type)
- Application Load Balancer
- Auto Scaling Group with capacity provider
- ECR for container images

## CI Pipeline
- Runs on GitHub-hosted runners
- Builds Docker image
- Tags image with GitHub run number
- Pushes image to ECR using OIDC authentication

## CD Pipeline
- Runs on self-hosted runner inside AWS
- Deploys ECS service using AWS CDK
- Uses ECS deployment circuit breaker with automatic rollback

## Deployment Safety
- Versioned Docker images
- ECS circuit breaker enabled
- Rolling deployments via ECS

This setup reflects real-world DevOps practices used in production systems.
