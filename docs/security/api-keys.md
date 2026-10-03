# RETRACE — API Key Management & Security Architecture

## 1. Key Generation & Format

- **Prefix**: `rt_live_`
- **Entropy**: 256-bit cryptographically secure random token (`secrets.token_urlsafe(32)`).
- **Format**: `rt_live_AbCdEf123456...`

---

## 2. Storage & Zero Plaintext Rule

1. **Hashed Storage**:
   - Plaintext keys are shown to the user **exactly once** upon creation.
   - The database stores only the SHA-256 digest: `hashlib.sha256(plaintext.encode()).hexdigest()`.

2. **Display Masking**:
   - For all UI displays and logs, keys are masked: `rt_live_••••••••`.

3. **Constant-Time Verification**:
   - Verification uses `hmac.compare_digest(computed_hash, stored_hash)` to protect against timing attacks.

---

## 3. Revocation & Expiration

- **Revocation**: Instant revocation by setting `revoked_at` timestamp.
- **Expiration**: Optional `expires_at` timestamp checked on every request.
- Inactive keys are immediately rejected with HTTP 401/403.
