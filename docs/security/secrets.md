# RETRACE Secret Management & Credential Policy

## 1. Zero-Secret Invariant

Production credentials, encryption keys, tokens, and database passwords must **NEVER** be committed to Git, baked into Docker images, or written to disk in production.

## 2. Secrets Storage & Injection

In production environments:
1. **AWS Secrets Manager / SSM Parameter Store**: Master database passwords, master application `SECRET_KEY`, and external tokens are stored as encrypted JSON secrets.
2. **ECS Task Secret Injection**: Secrets are injected directly into container environment variables at task launch time via ECS Task Definition secret references:
   ```json
   {
     "name": "DATABASE_URL",
     "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:retrace/prod/database:url::"
   }
   ```
3. **Local Development**: Developers use `.env` created from `.env.example`. `.env` is strictly ignored by `.gitignore` and `.dockerignore`.

## 3. Automated Secret Scanning

The repository includes a static secret scanner (`python -m packages.security.audit`) integrated into CI/CD that scans for:
- AWS Access Key IDs (`AKIA...`)
- OpenAI / Anthropic API keys (`sk-...`)
- RSA/SSH/EC Private Key headers
- Hardcoded password strings
