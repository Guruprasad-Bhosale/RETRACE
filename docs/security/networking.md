# RETRACE Network Architecture & Security Boundaries

## 1. Network Topology

```text
[Internet]
    │
    ▼ (Ports 80 / 443)
[Public Subnets (AZ-1, AZ-2)]
    ├── AWS Application Load Balancer (ALB)
    └── NAT Gateway (Outbound Egress for Workers)
    │
    ▼ (Internal Traffic Only)
[Private Application Subnets (AZ-1, AZ-2)]
    ├── ECS Tasks: API Service (Port 8000 from ALB only)
    ├── ECS Tasks: Frontend Web Server (Port 80 from ALB only)
    └── ECS Tasks: Background Analysis Worker (No Inbound)
    │
    ▼ (Internal Traffic Only)
[Private Data Subnets (AZ-1, AZ-2)]
    ├── Amazon RDS PostgreSQL (Port 5432 from API & Worker SGs only)
    └── Amazon ElastiCache Redis (Port 6379 from API & Worker SGs only)
```

## 2. Ingress & Egress Rules

- **ALB Security Group**: Allows inbound HTTP/HTTPS (80/443) from `0.0.0.0/0`.
- **API Security Group**: Accepts port 8000 strictly from the ALB Security Group ID.
- **Worker Security Group**: Zero inbound ports open. Outbound egress allowed through NAT Gateway for fetching target web application trajectories and S3 uploads.
- **RDS Security Group**: Inbound port 5432 accepted only from the API and Worker Security Group IDs.
- **Redis Security Group**: Inbound port 6379 accepted only from the API and Worker Security Group IDs.
