# Flash Loan LangChain AutoGen MCP Integration System - Operations Guide

This comprehensive operations guide provides detailed procedures for maintaining, monitoring, and troubleshooting the Flash Loan LangChain AutoGen MCP Integration System in production environments.

## Table of Contents

- [Daily Operations](#daily-operations)
- [System Monitoring](#system-monitoring)
- [Incident Response](#incident-response)
- [Maintenance Procedures](#maintenance-procedures)
- [Performance Tuning](#performance-tuning)
- [Security Operations](#security-operations)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Runbooks](#runbooks)
- [Emergency Procedures](#emergency-procedures)

## Daily Operations

### Morning Health Check Routine

**Daily System Health Verification** (15 minutes)

1. **Dashboard Review**

   ```bash
   # Access main dashboard
   curl -s http://localhost:8080/health | jq '.'
   
   # Check component status
   curl -s http://localhost:8080/api/status | jq '.components'
   ```

2. **Service Status Verification**

   ```bash
   # Docker Compose environment
   docker-compose ps
   
   # Kubernetes environment
   kubectl get pods -n flash-loan-system
   kubectl get services -n flash-loan-system
   ```

3. **Resource Utilization Check**

   ```bash
   # System resources
   docker stats --no-stream
   
   # Database connections
   docker-compose exec postgres psql -U postgres -d flash_loan_arbitrage -c "SELECT count(*) FROM pg_stat_activity;"
   
   # Redis memory usage
   docker-compose exec redis redis-cli info memory | grep used_memory_human
   ```

4. **Error Rate Analysis**

   ```bash
   # Check error logs from last 24 hours
   docker-compose logs --since="24h" | grep -i error | wc -l
   
   # Check specific service errors
   docker-compose logs --since="24h" mcp-coordinator | grep -i error
   ```

### Performance Metrics Review

**Key Metrics to Monitor Daily:**

| Metric | Threshold | Action Required |
|--------|-----------|-----------------|
| System Uptime | > 99.9% | Investigate if below |
| Response Time (P95) | < 2s | Optimize if above |
| Error Rate | < 1% | Investigate if above |
| Memory Usage | < 80% | Scale if above |
| CPU Usage | < 70% | Scale if above |
| Disk Usage | < 85% | Clean up if above |

**Daily Metrics Collection:**

```bash
#!/bin/bash
# daily_metrics.sh

DATE=$(date +"%Y-%m-%d")
METRICS_FILE="/tmp/daily_metrics_${DATE}.json"

# Collect system metrics
curl -s http://localhost:8080/api/metrics > $METRICS_FILE

# Generate daily report
python scripts/generate_daily_report.py --metrics-file $METRICS_FILE --date $DATE
```

### Transaction Volume Analysis

**Monitor Trading Activity:**

```sql
-- Daily arbitrage summary
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as total_trades,
    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_trades,
    AVG(profit_eth) as avg_profit,
    SUM(profit_eth) as total_profit,
    AVG(gas_used) as avg_gas
FROM arbitrage_history 
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

## System Monitoring

### Monitoring Stack Overview

```text
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Prometheus  │───►│   Grafana   │───►│ AlertManager│
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Metrics   │    │ Dashboards  │    │   Alerts    │
│ Collection  │    │    & UI     │    │ & Actions   │
└─────────────┘    └─────────────┘    └─────────────┘
```

### Critical Alerts Configuration

**High Priority Alerts:**

- Service downtime > 1 minute
- Error rate > 5%
- Response time > 5 seconds
- Memory usage > 90%
- Disk usage > 95%
- Failed arbitrage executions
- Security incidents

**Alert Channels Configuration:**

```yaml
# alertmanager.yml
routes:
  - match:
      severity: critical
    receiver: 'oncall-pager'
    group_wait: 10s
    group_interval: 5m
    repeat_interval: 12h

  - match:
      severity: warning
    receiver: 'team-email'
    group_wait: 30s
    group_interval: 5m
    repeat_interval: 24h

receivers:
  - name: 'oncall-pager'
    pagerduty_configs:
      - routing_key: 'YOUR_PAGERDUTY_KEY'
        
  - name: 'team-email'
    email_configs:
      - to: 'ops-team@company.com'
```

### Custom Monitoring Scripts

**Health Check Script:**

```python
#!/usr/bin/env python3
# scripts/health_check.py

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

SERVICES = [
    {"name": "MCP Coordinator", "url": "http://localhost:8080/health"},
    {"name": "LangChain Orchestrator", "url": "http://localhost:8002/health"},
    {"name": "AutoGen Coordinator", "url": "http://localhost:8001/health"},
]

async def check_service_health():
    results = []
    
    async with aiohttp.ClientSession() as session:
        for service in SERVICES:
            try:
                async with session.get(service["url"], timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        results.append({
                            "service": service["name"],
                            "status": "healthy",
                            "response_time": data.get("response_time", 0),
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        results.append({
                            "service": service["name"],
                            "status": "unhealthy",
                            "error": f"HTTP {response.status}",
                            "timestamp": datetime.now().isoformat()
                        })
            except Exception as e:
                results.append({
                    "service": service["name"],
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
    
    # Output results
    print(json.dumps(results, indent=2))
    
    # Exit with error if any service is unhealthy
    unhealthy = [r for r in results if r["status"] != "healthy"]
    if unhealthy:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(check_service_health())
```

## Incident Response

### Incident Classification

**Severity Levels:**

### P0 - Critical (Response: Immediate)

- Complete system outage
- Data corruption or loss
- Security breach
- Trading system malfunction causing financial loss

### P1 - High (Response: 15 minutes)

- Partial system outage
- Significant performance degradation
- Failed flash loan executions
- High error rates (>10%)

### P2 - Medium (Response: 2 hours)

- Minor performance issues
- Non-critical component failures
- Configuration issues
- Monitoring alerts

### P3 - Low (Response: Next business day)

- Documentation updates
- Enhancement requests
- Minor bugs with workarounds

### Incident Response Procedures

**P0/P1 Incident Response:**

1. **Immediate Assessment (5 minutes)**

   ```bash
   # Quick system status check
   ./scripts/emergency_status_check.sh
   
   # Check recent deployments
   kubectl rollout history deployment/mcp-coordinator -n flash-loan-system
   
   # Review recent logs
   docker-compose logs --tail=100 --since="10m"
   ```

2. **Containment Actions**

   ```bash
   # Stop trading if necessary
   curl -X POST http://localhost:8080/api/emergency-stop
   
   # Scale down if resource issue
   kubectl scale deployment mcp-coordinator --replicas=1 -n flash-loan-system
   
   # Enable circuit breaker
   curl -X POST http://localhost:8080/api/circuit-breaker/enable
   ```

3. **Communication Protocol**
   - Post in #incidents Slack channel
   - Update status page
   - Notify stakeholders within 15 minutes
   - Create incident ticket

4. **Investigation and Resolution**
   - Gather logs and metrics
   - Identify root cause
   - Implement fix
   - Verify resolution
   - Document lessons learned

### Emergency Contacts

```text
Role                    Primary Contact         Secondary Contact
System Administrator    +1-555-0123            +1-555-0124
DevOps Engineer        +1-555-0125            +1-555-0126
Security Officer       +1-555-0127            +1-555-0128
Product Manager        +1-555-0129            +1-555-0130
```

## Maintenance Procedures

### Scheduled Maintenance Windows

**Weekly Maintenance (Sundays 02:00-04:00 UTC)**

- System updates and patches
- Database maintenance
- Log rotation and cleanup
- Backup verification

**Monthly Maintenance (First Sunday of month)**

- Security updates
- Performance optimization
- Configuration review
- Disaster recovery testing

### System Updates

**Rolling Updates (Zero Downtime):**

```bash
# Kubernetes rolling update
kubectl set image deployment/mcp-coordinator mcp-coordinator=flash-loan/mcp-coordinator:v1.2.0 -n flash-loan-system

# Verify rollout
kubectl rollout status deployment/mcp-coordinator -n flash-loan-system

# Rollback if needed
kubectl rollout undo deployment/mcp-coordinator -n flash-loan-system
```

**Docker Compose Updates:**

```bash
# Pull new images
docker-compose pull

# Update with minimal downtime
docker-compose up -d --no-deps mcp-coordinator
docker-compose up -d --no-deps langchain-orchestrator
docker-compose up -d --no-deps autogen-coordinator
```

### Database Maintenance

**Weekly PostgreSQL Maintenance:**

```sql
-- Analyze database statistics
ANALYZE;

-- Vacuum to reclaim space
VACUUM (ANALYZE, VERBOSE);

-- Reindex if needed
REINDEX DATABASE flash_loan_arbitrage;

-- Check database size
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Redis Maintenance:**

```bash
# Check Redis memory usage
docker-compose exec redis redis-cli info memory

# Clear expired keys
docker-compose exec redis redis-cli --scan --pattern "temp:*" | xargs docker-compose exec redis redis-cli del

# Background save
docker-compose exec redis redis-cli bgsave
```

### Log Management

**Log Rotation Configuration:**

```bash
# /etc/logrotate.d/flash-loan-system
/var/log/flash-loan/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    postrotate
        docker-compose restart rsyslog
    endscript
}
```

**Log Cleanup Script:**

```bash
#!/bin/bash
# scripts/cleanup_logs.sh

# Remove logs older than 30 days
find /var/log/flash-loan -name "*.log" -mtime +30 -delete

# Compress logs older than 7 days
find /var/log/flash-loan -name "*.log" -mtime +7 -exec gzip {} \;

# Clean Docker logs
docker system prune -f --volumes --filter "until=168h"
```

## Performance Tuning

### System Performance Optimization

**CPU Optimization:**

```yaml
# docker-compose.yml CPU limits
services:
  mcp-coordinator:
    deploy:
      resources:
        limits:
          cpus: '2.0'
        reservations:
          cpus: '0.5'
```

**Memory Optimization:**

```yaml
# JVM memory settings for Java services
environment:
  - JAVA_OPTS=-Xms512m -Xmx2g -XX:+UseG1GC
  
# Python memory settings
environment:
  - PYTHONMEMORY=2048
```

**Database Performance Tuning:**

```sql
-- PostgreSQL configuration optimization
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Reload configuration
SELECT pg_reload_conf();
```

**Redis Performance Tuning:**

```bash
# Redis configuration optimization
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET save "900 1 300 10 60 10000"
redis-cli CONFIG SET timeout 300
```

### Network Optimization

**Connection Pooling:**

```python
# Database connection pooling
DATABASE_CONFIG = {
    'host': 'postgres',
    'port': 5432,
    'database': 'flash_loan_arbitrage',
    'min_connections': 5,
    'max_connections': 20,
    'pool_timeout': 30,
    'pool_recycle': 3600
}
```

**HTTP Client Optimization:**

```python
# Optimized HTTP client configuration
HTTP_CLIENT_CONFIG = {
    'connector': aiohttp.TCPConnector(
        limit=100,
        limit_per_host=30,
        ttl_dns_cache=300,
        use_dns_cache=True,
        keepalive_timeout=30,
        enable_cleanup_closed=True
    ),
    'timeout': aiohttp.ClientTimeout(total=30, connect=10),
    'headers': {'Connection': 'keep-alive'}
}
```

## Security Operations

### Security Monitoring

**Daily Security Checks:**

```bash
# Check for failed login attempts
docker-compose logs --since="24h" | grep -i "failed\|unauthorized\|forbidden"

# Monitor unusual API activity
curl -s http://localhost:8080/api/security/audit | jq '.suspicious_activities'

# Check SSL certificate expiry
openssl x509 -in /etc/ssl/certs/flashloan.crt -noout -dates
```

**Weekly Security Review:**
- Review access logs
- Update security patches
- Rotate API keys
- Review firewall rules
- Update dependency vulnerabilities

### Access Control Management

**User Access Audit:**

```bash
# Review active sessions
curl -s http://localhost:8080/api/admin/sessions | jq '.active_sessions'

# Check user permissions
curl -s http://localhost:8080/api/admin/users | jq '.users[] | {username, roles, last_login}'
```

**API Key Rotation:**

```bash
# Generate new API key
NEW_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Update configuration
kubectl create secret generic api-keys --from-literal=primary=$NEW_KEY -n flash-loan-system --dry-run=client -o yaml | kubectl apply -f -

# Restart services to pick up new key
kubectl rollout restart deployment/mcp-coordinator -n flash-loan-system
```

### Security Incident Response

**Immediate Actions for Security Incidents:**
1. Isolate affected systems
2. Preserve evidence
3. Assess scope of breach
4. Notify security team

# Upload to S3 (if configured)
if [ "$AWS_S3_BUCKET" ]; then
    aws s3 sync $BACKUP_DIR s3://$AWS_S3_BUCKET/backups/$DATE/
fi

# Cleanup old backups (keep 30 days)
find /backups -mtime +30 -type d -exec rm -rf {} \;
```

**Recovery Procedures:**

**Database Recovery:**
```bash
# Stop services
docker-compose stop mcp-coordinator langchain-orchestrator autogen-coordinator

# Restore database
gunzip -c /backups/20241222_020000/database.sql.gz | docker-compose exec -T postgres psql -U postgres flash_loan_arbitrage

# Restore Redis
docker cp /backups/20241222_020000/redis.rdb flash-loan-redis:/data/dump.rdb
docker-compose restart redis

# Start services
docker-compose start mcp-coordinator langchain-orchestrator autogen-coordinator
```

**Full System Recovery:**
```bash
# Restore from backup
RESTORE_DATE="20241222_020000"
BACKUP_DIR="/backups/$RESTORE_DATE"

# Restore configuration
cp -r $BACKUP_DIR/config/ ./
cp -r $BACKUP_DIR/monitoring/ ./

# Restore data
./scripts/restore_database.sh $BACKUP_DIR/database.sql.gz
./scripts/restore_redis.sh $BACKUP_DIR/redis.rdb

# Restart entire system
docker-compose down
docker-compose up -d
```

### Disaster Recovery

**RTO/RPO Targets:**
- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 1 hour

**DR Site Setup:**
```bash
# Replicate to DR site
rsync -avz --delete /backups/ dr-site:/backups/
rsync -avz --delete ./config/ dr-site:./config/

# Setup DR environment
ssh dr-site "cd flash-loan-system && docker-compose -f docker-compose.dr.yml up -d"
```

## Troubleshooting Guide

### Common Issues and Resolutions

#### Issue: High Memory Usage

**Symptoms:**
- OOM kills in containers
- Slow response times
- Memory usage > 90%

**Investigation:**
```bash
# Check memory usage by service
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Analyze memory consumption
docker-compose exec mcp-coordinator cat /proc/meminfo
```

**Resolution:**
```bash
# Increase memory limits
docker-compose.yml:
  deploy:
    resources:
      limits:
        memory: 4g

# Restart service
docker-compose restart mcp-coordinator
```

#### Issue: Database Connection Pool Exhaustion

**Symptoms:**
- Connection timeout errors
- "remaining connection slots are reserved" errors

**Investigation:**
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check connection by state
SELECT state, count(*) FROM pg_stat_activity GROUP BY state;
```

**Resolution:**
```sql
-- Increase max connections
ALTER SYSTEM SET max_connections = 200;
SELECT pg_reload_conf();

-- Kill idle connections
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE state = 'idle' AND query_start < now() - interval '1 hour';
```

#### Issue: MCP Server Timeouts

**Symptoms:**
- MCP server communication failures
- Timeout errors in logs

**Investigation:**
```bash
# Check MCP server health
curl -m 5 http://localhost:3023/health
curl -m 5 http://localhost:3022/health
curl -m 5 http://localhost:3021/health

# Check network connectivity
docker network ls
docker network inspect flash-loan-system_default
```

**Resolution:**
```bash
# Restart MCP servers
docker-compose restart mcp-filesystem mcp-context7 mcp-supermemory

# Increase timeouts in configuration
config/langchain_config.yaml:
  mcp_servers:
    critical:
      filesystem:
        timeout: 60  # Increased from 30
```

## Runbooks

### Runbook: Service Restart

**When to Use:**
- Service health checks failing
- Memory leaks detected
- Configuration changes applied

**Procedure:**
```bash
#!/bin/bash
# runbooks/restart_service.sh
SERVICE_NAME=$1

if [ -z "$SERVICE_NAME" ]; then
    echo "Usage: $0 <service_name>"
    exit 1
fi

# Pre-restart health check
echo "Checking service health before restart..."
docker-compose exec $SERVICE_NAME curl -f http://localhost:8080/health || echo "Service unhealthy"

# Graceful restart
echo "Performing graceful restart of $SERVICE_NAME..."
docker-compose restart $SERVICE_NAME

# Wait for service to start
echo "Waiting for service to start..."
sleep 30

# Post-restart health check
echo "Checking service health after restart..."
for i in {1..10}; do
    if docker-compose exec $SERVICE_NAME curl -f http://localhost:8080/health; then
        echo "Service restart successful"
        exit 0
    fi
    echo "Attempt $i failed, retrying in 10 seconds..."
    sleep 10
done

echo "Service restart failed"
exit 1
```

### Runbook: Emergency Trading Stop

**When to Use:**
- Suspicious trading activity
- System compromise detected
- Major system issues

**Procedure:**
```bash
#!/bin/bash
# runbooks/emergency_stop.sh

echo "EMERGENCY STOP INITIATED"
date

# Stop all trading activities
curl -X POST http://localhost:8080/api/emergency-stop

# Enable circuit breakers
curl -X POST http://localhost:8080/api/circuit-breaker/enable-all

# Scale down trading services
docker-compose stop autogen-coordinator
docker-compose stop langchain-orchestrator

# Notify team
echo "Emergency stop completed. Trading activities halted."
echo "Manual intervention required to resume operations."

# Log the incident
echo "$(date): Emergency stop initiated by operator" >> /var/log/flash-loan/emergency.log
```

### Runbook: Performance Degradation Response

**When to Use:**
- Response times > 5 seconds
- High CPU usage > 80%
- High error rates > 5%

**Procedure:**
```bash
#!/bin/bash
# runbooks/performance_degradation.sh

echo "Performance degradation response initiated"

# Collect performance metrics
docker stats --no-stream > /tmp/performance_stats.txt
curl -s http://localhost:8080/api/metrics > /tmp/system_metrics.json

# Check for resource constraints
FREE_MEM=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2}')
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')

echo "Memory usage: $FREE_MEM"
echo "CPU usage: $CPU_USAGE%"

# Scale up if resources allow
if (( $(echo "$CPU_USAGE > 70" | bc -l) )); then
    echo "High CPU detected, scaling up services..."
    kubectl scale deployment mcp-coordinator --replicas=3 -n flash-loan-system
    kubectl scale deployment langchain-orchestrator --replicas=2 -n flash-loan-system
fi

# Enable performance mode
curl -X POST http://localhost:8080/api/performance/high-performance-mode

echo "Performance optimization actions completed"
```

## Emergency Procedures

### Complete System Failure

**Immediate Actions (0-5 minutes):**
1. Assess scope of failure
2. Activate incident response team
3. Implement emergency stop
4. Preserve system state

**Recovery Actions (5-60 minutes):**
```bash
# Check system resources
df -h
free -m
docker system df

# Attempt service restart
docker-compose down
docker-compose up -d

# If restart fails, restore from backup
./scripts/emergency_restore.sh
```

### Data Corruption Detection

**Immediate Actions:**
1. Stop all write operations
2. Isolate affected databases
3. Assess corruption scope
4. Activate data recovery procedures

```bash
# Stop services immediately
docker-compose stop

# Check database integrity
docker-compose up -d postgres
docker-compose exec postgres pg_dump --data-only flash_loan_arbitrage > /tmp/data_check.sql

# Restore from latest backup if corruption confirmed
./scripts/restore_from_backup.sh --latest --verify
```

### Security Breach Response

**Immediate Actions (0-15 minutes):**
1. Isolate compromised systems
2. Preserve evidence
3. Assess breach scope
4. Notify security team

```bash
# Immediate lockdown
iptables -A INPUT -j DROP
iptables -A OUTPUT -j DROP

# Preserve evidence
tar -czf /tmp/evidence_$(date +%s).tar.gz /var/log/flash-loan/ /var/lib/docker/containers/

# Change all passwords and keys
./scripts/rotate_all_credentials.sh

# Notify authorities if required
./scripts/breach_notification.sh
```

---

## Escalation Procedures

### Level 1: Operations Team
- Initial response and basic troubleshooting
- Service restarts and basic maintenance
- Monitoring and alerting

### Level 2: Engineering Team
- Complex troubleshooting and debugging
- Code fixes and deployments
- Architecture modifications

### Level 3: Senior Engineering/Architects
- Critical system failures
- Major security incidents
- Disaster recovery scenarios

### External Escalation
- Legal/Compliance issues
- Regulatory notifications
- Vendor support

---

This operations guide should be reviewed and updated quarterly to ensure it remains current with system changes and operational requirements.