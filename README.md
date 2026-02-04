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

## Design Decisions & Trade-offs

- ECS EC2 launch type was chosen instead of Fargate to allow more control over instance sizing and cost.
- CI and CD pipelines are separated to minimize blast radius and improve security.
- Self-hosted runner is used for deployments to avoid exposing high-privilege AWS roles.
- Manual CD trigger is used to maintain deployment control in non-production environments.

## Limitations & Future Improvements

- Blue/green deployments can be added for zero-downtime releases.
- Multi-environment (dev/prod) support can be implemented.
- Additional monitoring and alerting can be integrated.
