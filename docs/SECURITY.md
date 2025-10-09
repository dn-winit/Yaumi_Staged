# = Security Guidelines

##   IMPORTANT: Before Deploying to Production

### 1. **NEVER Commit Secrets to Git**
- L Database credentials
- L API keys (GROQ_API_KEY, etc.)
- L Secret keys
- L `.env` files

### 2. **Environment Variables Checklist**

All sensitive data must be stored as environment variables:

#### Required Backend Variables:
```bash
# Database
DB_SERVER=<your-sql-server>
DB_NAME=<database-name>
DB_USER=<username>
DB_PASSWORD=<secure-password>

# API Keys
GROQ_API_KEY=<your-groq-api-key>

# Security
SECRET_KEY=<generate-random-key>
ENVIRONMENT=production

# CORS
CORS_ORIGINS=https://your-frontend-domain.com
```

#### Generate Secure Secret Key:
```python
import secrets
print(secrets.token_urlsafe(32))
```

### 3. **Security Features Implemented**

 **No Hardcoded Credentials** - All sensitive data from environment variables
 **HTTPS Only** - Enforced in production (cookies, headers)
 **Security Headers** - XSS, CSRF, clickjacking protection
 **CORS Restrictions** - Only allow trusted domains
 **Trusted Host Middleware** - Prevent host header attacks
 **GZip Compression** - Reduce bandwidth, improve performance
 **API Docs Disabled** - No Swagger/ReDoc in production
 **Content Security Policy** - Prevent XSS attacks

### 4. **Data Protection**

#### Files Excluded from Git:
- `.env` - All environment variables
- `backend/output/recommendations/*.csv` - Customer data
- `backend/output/supervision/*.json` - Sales data
- `backend/data/cache/*` - Cached database queries

### 5. **Database Security**

  **Critical**: Your SQL Server credentials were exposed in the code!

**Immediate Actions:**
1.  **DONE**: Removed hardcoded credentials from `backend/config/settings.py`
2.   **TODO**: Change database password immediately
3.   **TODO**: Review database access logs for unauthorized access
4.  **DONE**: Update code to use environment variables

**Best Practices:**
- Use strong passwords (minimum 16 characters, mixed case, numbers, symbols)
- Enable SQL Server authentication logging
- Restrict database access to specific IPs (production server only)
- Use separate database users for different environments (dev/prod)

### 6. **API Security**

**GROQ API Key Protection:**
- Never log API keys
- Rotate keys periodically
- Monitor API usage for anomalies

**Rate Limiting** (Recommended for production):
```python
# Add to main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/v1/dashboard/summary")
@limiter.limit("60/minute")
async def get_summary():
    ...
```

### 7. **Frontend Security**

**Vercel Environment Variables:**
```bash
# Set in Vercel Dashboard > Settings > Environment Variables
VITE_API_URL=https://yaumi-backend.onrender.com/api/v1
```

**Security Headers** (already configured in `vercel.json`):
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin

### 8. **Deployment Checklist**

Before pushing to production:

- [ ] All `.env` files listed in `.gitignore`
- [ ] Database password changed from exposed version
- [ ] `ENVIRONMENT=production` set on server
- [ ] `SECRET_KEY` generated using cryptographically secure method
- [ ] CORS origins updated to production domains only
- [ ] API documentation disabled in production
- [ ] HTTPS enforced (check hosting platform settings)
- [ ] Database access restricted to production server IP
- [ ] All team members informed about security protocols

### 9. **Incident Response**

If credentials are compromised:

1. **Immediate Actions:**
   - Rotate all affected credentials
   - Check access logs for unauthorized activity
   - Notify team and stakeholders

2. **Investigation:**
   - Identify scope of exposure
   - Review git history for credential leaks
   - Check for data exfiltration

3. **Prevention:**
   - Update security procedures
   - Use secret scanning tools (GitHub, GitGuardian)
   - Implement 2FA on all critical services

### 10. **Monitoring & Logging**

**What to Monitor:**
- Failed authentication attempts
- Unusual API usage patterns
- Database access from unknown IPs
- Error rates and exceptions

**Logging Best Practices:**
- Never log sensitive data (passwords, API keys)
- Use structured logging (JSON format)
- Set appropriate log levels (INFO in prod, DEBUG in dev)
- Implement log rotation to manage disk space

---

## =Þ Security Contact

For security concerns or to report vulnerabilities:
- Email: security@yaumi.com (update with actual contact)
- Escalate to: IT Security Team

**Remember: Security is everyone's responsibility!** =
