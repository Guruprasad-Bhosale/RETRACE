# RETRACE Backup, Durability & Disaster Recovery Runbook

## 1. Data Classification & Durability Matrix

| Component | Storage Layer | Backup Frequency | Retention | RPO | RTO |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Investigation Metadata & Checkpoints** | Amazon RDS PostgreSQL | Daily Snapshot + Point-in-time Recovery (WAL) | 7 to 30 Days | < 5 Minutes | < 30 Minutes |
| **Multi-Modal Artifacts (Screenshots, DOM, Traces)** | Amazon S3 | S3 99.999999999% Durability + Versioning | 90 Days | 0 (Immediate) | < 10 Minutes |
| **Worker Queue (In-Flight Messages)** | Amazon ElastiCache Redis | In-Memory AOF Append | Ephemeral Queue | Transient | Immediate restart |

## 2. PostgreSQL Backup & Restore

### Automated Snapshots
RDS performs automated daily backups and archives transaction logs continuously.

### Manual On-Demand Backup
```bash
aws rds create-db-snapshot \
  --db-instance-identifier retrace-production-postgres \
  --db-snapshot-identifier retrace-manual-backup-$(date +%Y%m%d%H%M%S)
```

### Point-in-Time Restore (PITR)
```bash
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier retrace-production-postgres \
  --target-db-instance-identifier retrace-restored-postgres \
  --restore-time 2026-09-30T10:00:00.000Z
```

## 3. S3 Artifact Recovery

- **Accidental Deletion**: Versioning is enabled on `retrace-prod-artifacts`. Deleted objects can be recovered by removing the delete marker.
- **Cross-Region Replication (Optional)**: Can be enabled for disaster recovery compliance.
