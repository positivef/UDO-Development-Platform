# UDO Platform - Security Audit Checklist

**Version**: 1.0
**Last Updated**: 2025-12-23
**Audit Frequency**: Before each production deployment + Quarterly review

---

## 🔒 Pre-Deployment Security Validation

**Requirement**: ALL items must be checked ✅ before deploying to production

---

## 1. Authentication & Authorization

### User Authentication
- [ ] JWT tokens use HS256 or RS256 algorithm (not HS512)
- [ ] JWT secret is 64+ characters, cryptographically random
- [ ] JWT expiration set (24 hours recommended)
- [ ] Refresh tokens implemented with rotation
- [ ] Password hashing uses bcrypt/argon2 (min 12 rounds)
- [ ] Failed login attempts rate-limited (5 attempts/15 min)
- [ ] Session timeout configured (30 min inactivity)

**Verify**:
```bash
# Check JWT configuration
grep -r "JWT_SECRET\|JWT_ALGORITHM\|JWT_EXPIRATION" .env

# Verify hash rounds in code
grep -r "bcrypt.hash\|argon2" backend/
```

---

### Authorization
- [ ] RBAC (Role-Based Access Control) implemented
- [ ] Least privilege principle enforced
- [ ] API endpoints require authentication (except public routes)
- [ ] Authorization checks on every sensitive operation
- [ ] No hardcoded admin credentials

**Test**:
```bash
# Try accessing admin endpoint without token
curl http://localhost:8000/api/admin/users
# Expected: 401 Unauthorized

# Try accessing with user token (should fail)
curl -H "Authorization: Bearer $USER_TOKEN" http://localhost:8000/api/admin/users
# Expected: 403 Forbidden
```

---

## 2. Input Validation & Sanitization

### SQL Injection Prevention
- [ ] ORM used (SQLAlchemy/Prisma) - no raw SQL
- [ ] If raw SQL needed: parameterized queries only
- [ ] User input never concatenated into SQL strings
- [ ] Database user has minimal permissions (no DROP/ALTER)

**Scan**:
```bash
# Check for SQL injection patterns
grep -r "execute.*%\|execute.*f\"" backend/ || echo "OK"
grep -r "\.format(.*)" backend/app/db/ || echo "OK"
```

---

### XSS (Cross-Site Scripting) Prevention
- [ ] React/Next.js auto-escaping used (default behavior)
- [ ] No dangerouslySetInnerHTML without sanitization
- [ ] User input sanitized before rendering
- [ ] Content-Security-Policy header configured

**Scan**:
```bash
# Check for dangerous patterns
grep -r "dangerouslySetInnerHTML" web-dashboard/ || echo "OK"
grep -r "eval(" web-dashboard/ || echo "OK"

# Verify CSP header
curl -I http://localhost:3000 | grep "Content-Security-Policy"
```

---

### CSRF (Cross-Site Request Forgery) Prevention
- [ ] CSRF tokens implemented for state-changing operations
- [ ] SameSite cookie attribute set (Strict or Lax)
- [ ] Origin/Referer header validation
- [ ] Double-submit cookie pattern used

**Verify**:
```bash
# Check CSRF middleware
grep -r "csrf\|CSRF" backend/app/core/ || echo "Not found - verify!"
```

---

## 3. Network Security

### HTTPS/TLS
- [ ] SSL certificate valid (not self-signed in production)
- [ ] TLS 1.2+ enforced (TLS 1.0/1.1 disabled)
- [ ] HSTS header configured (max-age=31536000)
- [ ] Redirect HTTP → HTTPS (301 permanent)
- [ ] Certificate auto-renewal configured (Certbot cron)

**Test**:
```bash
# SSL Labs test
curl https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com

# Check HSTS header
curl -I https://yourdomain.com | grep "Strict-Transport-Security"

# Verify TLS version
openssl s_client -connect yourdomain.com:443 -tls1_2
```

---

### CORS (Cross-Origin Resource Sharing)
- [ ] CORS_ORIGINS limited to production domains only
- [ ] No wildcard (*) in production
- [ ] Credentials allowed only for trusted origins
- [ ] Preflight requests handled correctly

**Verify**:
```bash
# Check CORS configuration
grep "CORS_ORIGINS" .env
# Should NOT see: CORS_ORIGINS=*

# Test CORS
curl -H "Origin: https://malicious.com" \
     -I http://localhost:8000/api/status
# Should NOT see Access-Control-Allow-Origin: *
```

---

### Firewall Rules
- [ ] Only necessary ports open (80, 443)
- [ ] Database port (5432) accessible only from backend IP
- [ ] SSH restricted to specific IPs (bastion host)
- [ ] Redis port (6379) not publicly accessible
- [ ] Admin panels (Grafana, pgAdmin) behind VPN or IP whitelist

**Check**:
```bash
# Verify firewall status
sudo ufw status verbose

# Expected rules:
# 22/tcp (SSH) - from specific IPs only
# 80/tcp (HTTP) - from anywhere
# 443/tcp (HTTPS) - from anywhere
# 5432/tcp (PostgreSQL) - DENY from anywhere
```

---

## 4. Data Protection

### Encryption
- [ ] Database credentials encrypted at rest
- [ ] API keys stored in secret manager (not .env in Git)
- [ ] Sensitive data encrypted in database (PII fields)
- [ ] SSL/TLS for database connections
- [ ] Redis password set (not empty)

**Verify**:
```bash
# Check if .env is in .gitignore
git check-ignore .env || echo "ERROR: .env not ignored!"

# Verify Redis password
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
# Should ask for password

# Test database SSL
docker-compose -f docker-compose.prod.yml exec backend python -c \
  "import asyncpg; print(asyncpg.connect(ssl='require'))"
```

---

### Data Retention
- [ ] GDPR compliance (data deletion on request)
- [ ] Backup retention policy defined (30 days)
- [ ] Logs retention policy (90 days max)
- [ ] PII anonymization in logs
- [ ] Soft delete implemented (no hard deletes)

---

## 5. Dependency Security

### Vulnerable Dependencies
- [ ] No critical/high vulnerabilities in npm packages
- [ ] No critical/high vulnerabilities in pip packages
- [ ] Automated dependency scanning (Dependabot/Snyk)
- [ ] Dependencies pinned to specific versions (not ^/~)
- [ ] Regular security updates (monthly)

**Scan**:
```bash
# Backend dependencies
pip-audit || echo "Install: pip install pip-audit"

# Frontend dependencies
cd web-dashboard && npm audit --production
# Fix: npm audit fix --production

# Docker images
docker scan udo-backend:production
docker scan udo-frontend:production
```

---

### Supply Chain Security
- [ ] Package lock files committed (package-lock.json, requirements.txt)
- [ ] No packages from untrusted registries
- [ ] Docker base images from official sources
- [ ] Image signatures verified (Docker Content Trust)

**Verify**:
```bash
# Check for suspicious packages
grep -E "git\+|http://|ftp://" backend/requirements.txt || echo "OK"

# Verify Docker images
docker images --digests | grep udo
```

---

## 6. API Security

### Rate Limiting
- [ ] Rate limiting enabled (60 req/min per IP)
- [ ] Burst protection configured
- [ ] Different limits for authenticated/unauthenticated
- [ ] API key rotation policy (90 days)

**Test**:
```bash
# Test rate limit
for i in {1..65}; do
  curl -w "%{http_code}\n" -o /dev/null http://localhost:8000/api/status
done
# Should see 429 (Too Many Requests) after 60
```

---

### API Versioning
- [ ] API versioned (v1, v2) in URL or header
- [ ] Deprecated versions documented
- [ ] Sunset header for deprecated endpoints

---

## 7. Error Handling & Logging

### Secure Error Messages
- [ ] No stack traces exposed to users (DEBUG=False)
- [ ] Generic error messages ("An error occurred" not "SQL syntax error")
- [ ] Detailed errors logged server-side only
- [ ] No sensitive data in error messages (passwords, tokens)

**Test**:
```bash
# Trigger error, verify no stack trace
curl http://localhost:8000/api/nonexistent
# Should NOT see: File "...", line ..., in ...
```

---

### Logging
- [ ] Security events logged (failed logins, permission denials)
- [ ] Logs centralized (Sentry, Datadog)
- [ ] No PII in logs (emails, IPs anonymized)
- [ ] Log injection prevented (no user input in log messages)
- [ ] Log rotation configured (daily, max 100MB)

**Verify**:
```bash
# Check log rotation
cat /etc/logrotate.d/udo || echo "Not configured - setup needed"

# Verify no passwords in logs
docker-compose -f docker-compose.prod.yml logs backend | grep -i "password" || echo "OK"
```

---

## 8. Infrastructure Security

### Docker Security
- [ ] Services run as non-root user (USER directive)
- [ ] Read-only root filesystem where possible
- [ ] No privileged containers
- [ ] Minimal base images (alpine)
- [ ] Health checks configured

**Scan**:
```bash
# Check Dockerfiles for USER directive
grep -r "^USER " backend/Dockerfile web-dashboard/Dockerfile

# Verify no privileged containers
docker-compose -f docker-compose.prod.yml config | grep "privileged: true" && echo "FAIL" || echo "OK"

# Scan for vulnerabilities
docker scout cves udo-backend:production
docker scout cves udo-frontend:production
```

---

### Secrets Management
- [ ] No secrets hardcoded in source code
- [ ] Secrets in environment variables or secret manager
- [ ] .env file not committed to Git
- [ ] Secret rotation process documented
- [ ] Separate secrets for dev/staging/production

**Audit**:
```bash
# Check for hardcoded secrets
grep -r "password\|secret\|key\|token" backend/ web-dashboard/ \
  --include="*.py" --include="*.js" --include="*.ts" \
  | grep -v "os.environ\|process.env" || echo "OK"

# Verify .env in .gitignore
cat .gitignore | grep "^\.env$" || echo "ERROR: Add .env to .gitignore!"
```

---

## 9. Monitoring & Incident Response

### Security Monitoring
- [ ] Failed login attempts monitored (alert if >10/min)
- [ ] Unusual traffic patterns detected (DDoS protection)
- [ ] File integrity monitoring (AIDE/Tripwire)
- [ ] Security logs forwarded to SIEM
- [ ] Automated vulnerability scanning (weekly)

---

### Incident Response
- [ ] Incident response plan documented
- [ ] Security contact list maintained
- [ ] Backup restoration tested (monthly)
- [ ] Communication plan for breaches
- [ ] Post-incident review process

---

## 10. Compliance & Privacy

### GDPR Compliance (if applicable)
- [ ] Privacy policy published
- [ ] Data subject access request (DSAR) process
- [ ] Right to deletion implemented
- [ ] Data breach notification plan (<72 hours)
- [ ] Consent management for data collection

---

### Audit Trail
- [ ] All sensitive operations logged (who, what, when)
- [ ] Audit logs immutable (append-only)
- [ ] Log retention 1+ year
- [ ] Audit log access restricted

---

## 📊 Security Scoring

| Category | Total Items | Checked | Score |
|----------|-------------|---------|-------|
| Authentication & Authorization | 13 | ___ | ___% |
| Input Validation | 13 | ___ | ___% |
| Network Security | 15 | ___ | ___% |
| Data Protection | 10 | ___ | ___% |
| Dependency Security | 9 | ___ | ___% |
| API Security | 5 | ___ | ___% |
| Error Handling | 9 | ___ | ___% |
| Infrastructure | 11 | ___ | ___% |
| Monitoring | 9 | ___ | ___% |
| Compliance | 9 | ___ | ___% |
| **TOTAL** | **103** | ___ | ___% |

**Minimum Score for Production**: 95% (98/103 items)

---

## 🚫 Deployment Blockers

**DO NOT deploy if ANY of these are unchecked**:

- [ ] DEBUG=False in production
- [ ] JWT_SECRET is not default/example value
- [ ] Database password is strong (32+ chars)
- [ ] CORS_ORIGINS does not contain "*"
- [ ] No critical vulnerabilities in dependencies
- [ ] HTTPS/TLS configured and working
- [ ] Rate limiting enabled
- [ ] Secrets not hardcoded in source
- [ ] .env file not in Git
- [ ] User authentication required for sensitive endpoints

---

## 🔍 Automated Security Scan

```bash
#!/bin/bash
# automated-security-scan.sh

echo "=== UDO Security Audit ==="

# 1. Dependency vulnerabilities
echo "\n[1/6] Scanning dependencies..."
pip-audit
cd web-dashboard && npm audit --production

# 2. Docker image vulnerabilities
echo "\n[2/6] Scanning Docker images..."
docker scan udo-backend:production
docker scan udo-frontend:production

# 3. Hardcoded secrets
echo "\n[3/6] Checking for hardcoded secrets..."
docker run --rm -v $(pwd):/src trufflesecurity/trufflehog filesystem /src

# 4. OWASP ZAP scan
echo "\n[4/6] Running OWASP ZAP..."
docker run --rm -t owasp/zap2docker-stable zap-baseline.py -t http://localhost:8000

# 5. SSL/TLS test
echo "\n[5/6] Testing SSL/TLS..."
testssl.sh yourdomain.com

# 6. Security headers
echo "\n[6/6] Checking security headers..."
curl -I https://yourdomain.com | grep -E "Strict-Transport-Security|Content-Security-Policy|X-Frame-Options"

echo "\n=== Audit Complete ==="
```

---

## 📞 Security Contacts

- **Security Team**: security@yourdomain.com
- **Bug Bounty**: [HackerOne/Bugcrowd link]
- **Incident Response**: oncall@yourdomain.com
- **Data Protection Officer**: dpo@yourdomain.com

---

## 🔗 Related Documentation

- `PRODUCTION_DEPLOYMENT_GUIDE.md` - Deployment procedures
- `ROLLBACK_PROCEDURES.md` - Rollback strategies
- `docs/SECURITY_AUDIT_2025-12-21.md` - Previous audit
- `docs/PRODUCTION_SECURITY_REVIEW.md` - Detailed security review

---

**Last Audit**: ________________
**Auditor**: ________________
**Score**: ____/103 (___%)
**Production Ready**: ☐ Yes  ☐ No  ☐ With caveats

**Caveats/Notes**:
_________________________________________________
_________________________________________________
_________________________________________________
