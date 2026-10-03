# RETRACE Browser Sandbox & Playwright Execution Security Audit

## 1. Threat Model & Sandbox Controls

Because RETRACE executes autonomous browser sessions against arbitrary web applications under investigation, strict sandboxing is mandatory to prevent Server-Side Request Forgery (SSRF), local filesystem exfiltration, and privilege escalation.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        PLAYWRIGHT BROWSER SANDBOX                      │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Non-Root Execution: Container runs under UID 10001 (appuser)        │
│ 2. IMDS / Metadata Block: Navigation to 169.254.169.254 blocked        │
│ 3. Filesystem Isolation: File downloads disabled or routed to temp dir │
│ 4. No Local Secrets: Environment variables scrubbed before page launch │
│ 5. Resource Constraints: max_browser_pages (50), timeout (600s)        │
│ 6. Navigation Policy: Navigation constrained to target origin domains  │
└────────────────────────────────────────────────────────────────────────┘
```

## 2. Blocked Network Endpoints

The worker actively blocks browser navigation and network fetch calls to:
- `169.254.169.254` (AWS Instance Metadata Service v1/v2)
- `metadata.google.internal` (GCP Metadata)
- `100.100.100.200` (Alibaba Cloud Metadata)
- Internal private VPC CIDRs (`10.0.0.0/16`) unless explicitly allowlisted as the target test application.
