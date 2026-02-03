# Architecture Overview

The following diagram represents the high-level architecture of the application
deployed using AWS CDK and ECS.

```mermaid
graph TD
    User((Users)) -->|HTTPS 443| ALB[Application Load Balancer]

    subgraph "Public DNS"
        DNS[Route53 DNS] -->|CNAME| ALB
    end

    subgraph "AWS VPC (Private Network)"
        ALB -->|Forward Traffic| TG[Target Group]

        subgraph "ECS Cluster"
            ASG[Auto Scaling Group] -->|Launches| EC2[EC2 Instances]
            EC2 -->|Hosts| Container[ECS Task / Application Container]
        end
    end

    Container -->|Logs| CW[CloudWatch Logs]
    ECR[Amazon ECR] -->|Pull Image| EC2
