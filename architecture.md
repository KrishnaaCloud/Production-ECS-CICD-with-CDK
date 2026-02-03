graph TD
    User((Users)) -->|HTTPS/443| ALB[Application LoadBalancer]
    
    subgraph "Sadhguru.org Domain"
        DNS[Route53 / DNS] -->|CNAME| ALB
    end
    subgraph "AWS VPC (Private Network)"
        ALB -->|Forward Traffic| TG[Target Group]
        
        subgraph "ECS Cluster"
            ASG[Auto Scaling Group] -->|Launches| EC2[EC2 Instance (t3a.medium)]
            EC2 -->|Hosts| Container[GlobalPRS API Container]
        end
    end
    
    Container -->|Logs| CW[CloudWatch Logs]
    ECR[Amazon ECR] -->|Pulls Image| EC2