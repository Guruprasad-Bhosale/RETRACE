# RETRACE — Multi-Tenant Architecture & Workspace Isolation

## 1. Domain Hierarchy

```text
Organization
 └── Workspace
      ├── Members (Users with Roles: OWNER | ADMIN | ANALYST | VIEWER)
      ├── API Keys (rt_live_... with SHA-256 hashed storage)
      ├── Projects (Version A vs Version B endpoints)
      ├── Analyses & Workflows
      ├── Investigations & Generated Playwright Tests
      └── Artifacts (DOM, HAR, Diff snapshots)
```

---

## 2. Strict Server-Side Isolation Guarantee

Multi-tenancy in RETRACE is enforced strictly on the server-side, not in UI rendering:

1. **Workspace Boundary Checks**:
   - Every read, write, execution, and deletion operation must supply a valid `workspace_id`.
   - If `caller.workspace_id != resource.workspace_id`, the centralized `authorize()` function immediately returns `False` and logs an `authorization.denied` event.

2. **Zero Cross-Tenant Leakage**:
   - Database queries filter by `workspace_id` in relational mappings.
   - S3 artifact storage keys include the workspace prefix: `artifacts/{workspace_id}/{analysis_id}/...`.

---

## 3. Role-Based Access Control (RBAC) Matrix

| Action | `OWNER` | `ADMIN` | `ANALYST` | `VIEWER` |
|:---|:---:|:---:|:---:|:---:|
| `workspace:manage` | ✅ | ❌ | ❌ | ❌ |
| `members:manage` | ✅ | ✅ | ❌ | ❌ |
| `api_keys:manage` | ✅ | ❌ | ❌ | ❌ |
| `project:create` | ✅ | ✅ | ✅ | ❌ |
| `project:delete` | ✅ | ✅ | ❌ | ❌ |
| `analysis:execute` | ✅ | ✅ | ✅ | ❌ |
| `investigation:view` | ✅ | ✅ | ✅ | ✅ |
| `artifact:view` | ✅ | ✅ | ✅ | ✅ |
