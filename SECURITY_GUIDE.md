# UDO Platform - Security Configuration Guide

## Overview

This guide explains the security hardening measures implemented in `docker-compose.secure.yml` and how to deploy the UDO platform securely in production.

## Security Features

### 1. Docker Secrets Management

**What**: Sensitive data stored as Docker secrets instead of environment variables

**Implementation**:
```yaml
secrets:
  db_password:
    file: ./secrets/db_password.txt
  openai_api_key:
    file: ./secrets/openai_api_key.txt
```

**Setup**:
```bash
# Create secrets directory
mkdir -p secrets

# Generate strong passwords
openssl rand -base64 32 > secrets/db_password.txt
openssl rand -base64 32 > secrets/redis_password.txt

# Add API keys (replace with your actual keys)
echo "sk-YOUR_OPENAI_KEY" > secrets/openai_api_key.txt
echo "sk-ant-YOUR_ANTHROPIC_KEY" > secrets/anthropic_api_key.txt
echo "YOUR_GEMINI_KEY" > secrets/gemini_api_key.txt

# Secure permissions (read-only for owner)
chmod 600 secrets/*.txt
```

**Why**:
- Secrets are not exposed in environment variables
- Not stored in Docker images or logs
- Mounted as read-only files at `/run/secrets/`

---

### 2. Network Isolation

**What**: Separate internal and external networks to limit service exposure

**Implementation**:
```yaml
networks:
  internal:
    driver: bridge
    internal: true  # No external access
  external:
    driver: bridge  # Can access internet
```

**Service Assignment**:
- **Internal Only**: Database, Redis, Worker
- **Both Networks**: API, Prometheus, Grafana, pgAdmin
- **External Only**: Frontend

**Why**:
- Database and Redis are never directly accessible from internet
- Limits attack surface
- Prevents lateral movement in case of compromise

---

### 3. Non-Root Users

**What**: Services run as non-privileged users instead of root

**Implementation**:
```yaml
db:
  user: postgres
redis:
  user: redis
prometheus:
  user: nobody
grafana:
  user: "472:472"
frontend:
  user: node
```

**Why**:
- Limits damage if container is compromised
- Follows principle of least privilege
- Industry best practice

---

### 4. Resource Limits

**What**: CPU and memory limits to prevent resource exhaustion

**Implementation**:
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2g
    reservations:
      cpus: '1.0'
      memory: 1g
```

**Configured Limits**:
| Service | CPU Limit | Memory Limit |
|---------|-----------|--------------|
| API | 2.0 cores | 2GB |
| Database | 1.0 core | 1GB |
| Worker | 1.0 core | 1GB |
| Redis | 0.5 core | 512MB |
| Prometheus | 0.5 core | 512MB |
| Grafana | 0.5 core | 512MB |
| Frontend | 1.0 core | 1GB |

**Why**:
- Prevents DoS through resource exhaustion
- Ensures fair resource allocation
- Predictable performance

---

### 5. Security Options

**What**: Additional kernel-level security features

**Implementation**:
```yaml
security_opt:
  - no-new-privileges:true
```

**Features**:
- `no-new-privileges`: Prevents privilege escalation
- AppArmor/SELinux profiles (optional, OS-dependent)

**Why**:
- Blocks container escape attempts
- Prevents privilege escalation exploits
- Defense in depth

---

### 6. Read-Only Filesystems

**What**: Application code mounted as read-only

**Implementation**:
```yaml
volumes:
  - ./backend:/app:ro  # Read-only
  - ./logs:/app/logs   # Write for logs only
```

**Why**:
- Prevents malware from modifying code
- Immutable infrastructure pattern
- Easier to detect tampering

---

### 7. Healthchecks

**What**: Automated health monitoring for all services

**Implementation**:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U udo_dev -d udo_v3"]
  interval: 5s
  timeout: 5s
  retries: 5
```

**Why**:
- Early detection of service failures
- Automatic container restart on unhealthy state
- Better observability

---

## Deployment Guide

### Development Environment

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit .env with your values**:
   ```bash
   # Generate strong passwords
   openssl rand -hex 32  # For DB_PASSWORD
   openssl rand -hex 32  # For JWT_SECRET_KEY
   ```

3. **Use standard docker-compose**:
   ```bash
   docker-compose up -d
   ```

### Production Environment

1. **Setup secrets** (see section 1 above)

2. **Use secure docker-compose**:
   ```bash
   docker-compose -f docker-compose.secure.yml up -d
   ```

3. **Verify security**:
   ```bash
   # Check all containers running as non-root
   docker-compose -f docker-compose.secure.yml exec api whoami
   # Should output: app (or non-root user)

   # Check network isolation
   docker network inspect udo-development-platform_internal
   # Should show "internal": true

   # Check resource limits
   docker stats
   # Should show limits applied
   ```

---

## Security Checklist

### Pre-Deployment

- [ ] Change all default passwords in `.env`
- [ ] Generate strong secrets (32+ characters)
- [ ] Setup Docker secrets directory with correct permissions
- [ ] Review and customize resource limits for your hardware
- [ ] Enable firewall rules (only expose necessary ports)

### Production Only

- [ ] Use HTTPS/TLS for all external endpoints
- [ ] Setup reverse proxy (nginx/Traefik) with SSL termination
- [ ] Enable rate limiting on API endpoints
- [ ] Configure log aggregation and monitoring
- [ ] Setup automated backups for databases
- [ ] Enable audit logging
- [ ] Regular security updates (docker images, dependencies)

### Ongoing

- [ ] Monitor resource usage and adjust limits
- [ ] Review logs for suspicious activity
- [ ] Test disaster recovery procedures
- [ ] Update secrets rotation policy
- [ ] Penetration testing (if applicable)

---

## Troubleshooting

### Permission Denied Errors

**Issue**: Service fails to start with "permission denied"

**Solution**:
```bash
# Fix secrets permissions
chmod 600 secrets/*.txt

# Fix volume permissions
sudo chown -R $USER:$USER ./logs ./data
```

### Network Connectivity Issues

**Issue**: Services can't communicate

**Solution**:
```bash
# Check network configuration
docker network ls
docker network inspect udo-development-platform_internal

# Ensure services are on correct networks
docker-compose -f docker-compose.secure.yml ps
```

### Resource Limit Warnings

**Issue**: Container killed due to OOM (Out of Memory)

**Solution**:
```bash
# Increase memory limit in docker-compose.secure.yml
deploy:
  resources:
    limits:
      memory: 4g  # Increase as needed

# Monitor actual usage
docker stats --no-stream
```

---

## Security Incident Response

### If Breach Suspected

1. **Immediate Actions**:
   ```bash
   # Stop all services
   docker-compose -f docker-compose.secure.yml down

   # Preserve logs for forensics
   docker-compose -f docker-compose.secure.yml logs > incident_logs.txt
   ```

2. **Investigation**:
   - Review logs for suspicious activity
   - Check for unauthorized file modifications
   - Analyze network traffic logs

3. **Recovery**:
   - Rotate all secrets and passwords
   - Rebuild containers from clean images
   - Restore from last known good backup
   - Apply security patches
   - Re-deploy with enhanced monitoring

---

## Additional Security Measures

### Recommended (Not Implemented)

1. **Container Image Scanning**:
   ```bash
   # Use Trivy for vulnerability scanning
   trivy image pgvector/pgvector:pg16
   ```

2. **Runtime Security**:
   - Falco for runtime threat detection
   - Sysdig for container monitoring

3. **Network Security**:
   - WAF (Web Application Firewall)
   - DDoS protection
   - VPN for remote access

4. **Compliance**:
   - CIS Docker Benchmark
   - OWASP Top 10 mitigation
   - SOC 2 controls (if applicable)

---

## References

- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)

---

## Support

For security issues or questions:
- **Email**: security@udo-platform.dev (if applicable)
- **GitHub Issues**: https://github.com/your-org/udo-platform/issues (mark as security)
- **Internal**: Contact DevSecOps team

---

**Last Updated**: 2025-12-01
**Version**: 1.0
**Author**: UDO Development Team
