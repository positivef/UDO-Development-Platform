# Security Audit Checklist

**Target**: 95%+ items passing before production deployment

## 1. Authentication & Authorization (10 items)

- [ ] JWT tokens signed with strong secret (256-bit+)
- [ ] Token expiration configured (max 24h)
- [ ] Token blacklist on logout implemented
- [ ] RBAC roles enforced on all endpoints
- [ ] Password hashing uses bcrypt/argon2
- [ ] Rate limiting on auth endpoints (10/min)
- [ ] Account lockout after 5 failed attempts
- [ ] Session invalidation on password change
- [ ] No credentials in URL parameters
- [ ] Auth bypass in dev mode disabled in production

## 2. API Security (10 items)

- [ ] CORS configured to specific domains only
- [ ] All inputs validated with Pydantic models
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] CSRF protection enabled
- [ ] Rate limiting on all API endpoints
- [ ] Request size limits configured
- [ ] API versioning in place
- [ ] Error messages don't leak internal details
- [ ] Swagger UI disabled or auth-protected in production

## 3. Data Protection (10 items)

- [ ] Database credentials not hardcoded
- [ ] Secrets stored in environment variables
- [ ] `.env` files in `.gitignore`
- [ ] No secrets in git history
- [ ] Database connections use SSL
- [ ] Sensitive data encrypted at rest
- [ ] PII handling compliant with regulations
- [ ] Backup files encrypted
- [ ] Log files don't contain secrets
- [ ] API keys rotatable without downtime

## 4. Infrastructure Security (10 items)

- [ ] Docker images use non-root user
- [ ] Docker images pinned to specific versions
- [ ] Network isolation between services
- [ ] Only ports 80/443 exposed externally
- [ ] SSH access restricted to key-based auth
- [ ] Firewall rules configured
- [ ] OS and packages updated
- [ ] Docker socket not exposed
- [ ] Resource limits set on containers
- [ ] Health checks on all services

## 5. Transport Security (10 items)

- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] TLS 1.2+ required
- [ ] HSTS header enabled
- [ ] Certificate auto-renewal configured
- [ ] WebSocket connections use WSS
- [ ] Internal service communication encrypted
- [ ] No mixed content
- [ ] Certificate transparency monitoring
- [ ] Strong cipher suites only
- [ ] OCSP stapling enabled

## 6. Monitoring & Logging (10 items)

- [ ] Auth events logged (login, logout, failures)
- [ ] API errors logged with context
- [ ] Logs don't contain sensitive data
- [ ] Log rotation configured
- [ ] Centralized logging (Prometheus/Grafana)
- [ ] Alerting for anomalous patterns
- [ ] Security event monitoring
- [ ] Uptime monitoring configured
- [ ] Performance metrics collected
- [ ] Error rate alerting (>5% threshold)

## 7. Dependency Security (10 items)

- [ ] Python dependencies pinned to versions
- [ ] Node.js dependencies pinned (package-lock.json)
- [ ] No known vulnerabilities (`pip-audit`, `npm audit`)
- [ ] Dependency update schedule defined
- [ ] Docker base images from trusted sources
- [ ] No unnecessary packages installed
- [ ] License compliance verified
- [ ] Supply chain security (checksum verification)
- [ ] Dev dependencies excluded from production
- [ ] Automated vulnerability scanning in CI

## 8. Database Security (10 items)

- [ ] Database not exposed to public network
- [ ] Dedicated database user (not postgres/root)
- [ ] Minimal privileges per service
- [ ] Connection pooling configured
- [ ] Query timeout limits set
- [ ] Automated backups verified
- [ ] Backup restoration tested
- [ ] Schema migrations audited
- [ ] No raw SQL from user input
- [ ] Database access logging enabled

## 9. Frontend Security (10 items)

- [ ] Content Security Policy header
- [ ] X-Frame-Options header
- [ ] X-Content-Type-Options header
- [ ] Referrer-Policy header
- [ ] No inline scripts (CSP violation)
- [ ] Subresource Integrity for CDN resources
- [ ] No sensitive data in localStorage
- [ ] Input sanitization on all forms
- [ ] File upload validation (type, size)
- [ ] No source maps in production

## 10. Operational Security (13 items)

- [ ] Rollback procedures documented and tested
- [ ] Incident response plan documented
- [ ] Contact list for security incidents
- [ ] Regular security review schedule
- [ ] Penetration testing scheduled
- [ ] Security training for team
- [ ] Change management process defined
- [ ] Access control for deployment pipeline
- [ ] Secrets rotation schedule defined
- [ ] Disaster recovery plan documented
- [ ] Business continuity plan
- [ ] Compliance requirements identified
- [ ] Third-party security assessments scheduled

## Summary

| Category | Items | Target |
|----------|-------|--------|
| Authentication | 10 | 10/10 |
| API Security | 10 | 10/10 |
| Data Protection | 10 | 9/10 |
| Infrastructure | 10 | 10/10 |
| Transport | 10 | 9/10 |
| Monitoring | 10 | 9/10 |
| Dependencies | 10 | 9/10 |
| Database | 10 | 10/10 |
| Frontend | 10 | 9/10 |
| Operational | 13 | 12/13 |
| **Total** | **103** | **97/103 (94%+)** |
