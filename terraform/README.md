# Sample Terraform — Web App on AWS

Sample infrastructure used **as test data only**. It is syntactically valid
(`terraform validate` passes) but is not intended to be applied to a real account.

## Architecture

```
            Internet
               │
        ┌──────▼───────┐
        │ API Gateway  │  (HTTP API, public entrypoint)
        └──────┬───────┘
               │ VPC Link
        ┌──────▼───────┐
        │ Internal ALB │  /  → SPA   /api/* → API
        └───┬──────┬───┘
            │      │
   ┌────────▼─┐  ┌─▼─────────┐
   │ SPA      │  │ API       │  ECS Fargate (private subnets)
   │ (Fargate)│  │ (Fargate) │
   └──────────┘  └────┬──────┘
                      │
        ┌─────────────┼───────────────┐
        │             │               │
   ┌────▼────┐  ┌─────▼─────┐   ┌─────▼──────────┐
   │ RDS     │  │ SendGrid  │   │ Payment        │
   │ Postgres│  │ (email)   │   │ Processor      │
   │ Multi-AZ│  │ external  │   │ external       │
   └─────────┘  └───────────┘   └────────────────┘
```

## Files

| File                  | Contents                                              |
|-----------------------|-------------------------------------------------------|
| `versions.tf`         | Terraform/provider requirements, AWS provider         |
| `variables.tf`        | Input variables (region, images, secrets, etc.)       |
| `vpc.tf`              | VPC, public/private/data subnets, IGW, NAT, routes    |
| `security_groups.tf`  | SGs for ALB, SPA, API, and RDS                         |
| `ecr.tf`              | ECR repositories for the SPA and API images           |
| `secrets.tf`          | Secrets Manager: DB creds, SendGrid, payment key       |
| `rds.tf`              | RDS Postgres (Multi-AZ, encrypted)                     |
| `alb.tf`              | Internal ALB, target groups, listener rules           |
| `iam.tf`              | ECS execution and task roles                           |
| `ecs.tf`              | ECS cluster, task definitions, services, log groups   |
| `apigateway.tf`       | HTTP API, VPC Link, integration, stage                |
| `outputs.tf`          | Endpoints and resource identifiers                     |

## Notes / extrapolated pieces

- **Network tiers:** public (NAT/ALB reach), private (Fargate tasks), and data
  (RDS) subnets across two AZs.
- **Ingress path:** API Gateway → VPC Link → internal ALB. The ALB serves the
  SPA by default and routes `/api/*` to the API service.
- **Secrets:** DB credentials, the SendGrid API key, and the payment processor
  key live in Secrets Manager; the API task reads them at runtime. Variable
  defaults are placeholders — supply real values via `TF_VAR_*`.
- **External dependencies:** SendGrid (email) and the payment processor are
  reached outbound through the NAT gateway; they are not modeled as resources.
