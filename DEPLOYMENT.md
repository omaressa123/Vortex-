# AutoInsight - Production Deployment Guide

## 🏗️ Production Architecture Overview

```
User → Nginx (SSL/Ratelimit) → FastAPI (Gunicorn/Uvicorn) → PostgreSQL + Qdrant + Redis
                                      ↓
                              S3 Storage + Langfuse + Prometheus/Grafana
```

## 🚀 Quick Start (Production)

### 1. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit with your production values
nano .env
```

### 2. Deploy with Docker Compose
```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f fastapi
```

### 3. Initialize Database
```bash
# Run database migrations
docker-compose exec postgres psql -U postgres -d autoinsight -f /docker-entrypoint-initdb.d/init.sql
```

### 4. Verify Deployment
```bash
# Health check
curl http://localhost/health

# API documentation
curl http://localhost/docs
```

## 📋 Production Requirements

### Infrastructure
- **CPU**: 4+ cores (MVP), 8+ cores (Growth), 16+ cores (Enterprise)
- **RAM**: 8GB+ (MVP), 16GB+ (Growth), 32GB+ (Enterprise)
- **Storage**: 100GB+ SSD, scalable
- **Network**: 1Gbps+, low latency

### Services
- **Nginx**: Reverse proxy, SSL termination, rate limiting
- **FastAPI**: Application server with Gunicorn/Uvicorn workers
- **PostgreSQL**: Primary database for user data and metadata
- **Qdrant**: Vector database for embeddings
- **Redis**: Caching and session storage
- **S3/MinIO**: File storage for uploads
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboards

## 🔧 Configuration

### Security
```bash
# Generate secure secrets
openssl rand -base64 32  # JWT secret
openssl rand -base64 32  # Database password
```

### SSL Certificates
```bash
# Let's Encrypt (recommended)
certbot --nginx -d your-domain.com

# Or place custom certificates in nginx/ssl/
```

### Environment Variables
```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379
OPENAI_API_KEY=sk-...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET=autoinsight-prod

# Optional
LANGFUSE_SECRET_KEY=...
LANGFUSE_PUBLIC_KEY=...
GRAFANA_PASSWORD=...
```

## 📊 Monitoring & Observability

### Prometheus Metrics
- HTTP requests, response times, error rates
- Database connections, query performance
- File upload sizes, processing times
- API usage, token consumption

### Grafana Dashboards
- System performance (CPU, RAM, disk)
- Application metrics (requests, errors)
- Business metrics (users, uploads, dashboards)
- Cost tracking (OpenAI tokens, AWS costs)

### Logging
```bash
# View application logs
docker-compose logs -f fastapi

# View Nginx logs
docker-compose logs -f nginx

# View database logs
docker-compose logs -f postgres
```

## 🔄 CI/CD Pipeline

### Automated Workflows
1. **On Push**: Tests → Security scan → Build Docker image
2. **Develop Branch**: Deploy to staging
3. **Main Branch**: Deploy to production
4. **Pull Requests**: Tests and validation only

### Manual Rollback
```bash
# View deployment history
docker-compose images

# Rollback to previous version
docker-compose down
docker-compose up -d --force-recreate fastapi:previous-tag
```

## 📈 Scaling Strategy

### Stage 1: MVP (Single VM)
- 1x Docker Compose deployment
- Manual scaling
- Basic monitoring
- Estimated cost: $50-100/month

### Stage 2: Growth (Load Balancer)
- Application load balancer
- Multiple FastAPI instances
- Redis cache cluster
- Auto-scaling based on CPU/memory
- Estimated cost: $200-500/month

### Stage 3: Enterprise (Kubernetes)
- Kubernetes cluster
- Horizontal pod autoscaling
- Multi-region deployment
- Advanced monitoring and alerting
- Estimated cost: $1000+/month

## 🔒 Security Best Practices

### Network Security
- HTTPS only (redirect HTTP to HTTPS)
- API rate limiting (10 req/s general, 2 req/s uploads)
- Firewall rules (only necessary ports)
- VPC/private networks

### Application Security
- JWT authentication + API keys
- Input validation and sanitization
- SQL injection prevention
- File upload restrictions
- Environment variable encryption

### Data Protection
- Database encryption at rest
- S3 encryption (SSE-S3 or SSE-KMS)
- Regular backups
- GDPR compliance (data deletion)
- Audit logging

## 🚨 Troubleshooting

### Common Issues

#### High Memory Usage
```bash
# Check memory usage
docker stats

# Restart services
docker-compose restart fastapi

# Scale workers
docker-compose up -d --scale fastapi=4
```

#### Database Connection Issues
```bash
# Check database status
docker-compose exec postgres pg_isready

# View connections
docker-compose exec postgres psql -U postgres -c "SELECT * FROM pg_stat_activity;"
```

#### Slow API Responses
```bash
# Check response times
curl -w "@curl-format.txt" http://localhost/api/health

# View application logs
docker-compose logs fastapi | grep "slow"
```

### Health Checks
```bash
# Service health
curl http://localhost/health

# Database health
docker-compose exec postgres pg_isready

# Redis health
docker-compose exec redis redis-cli ping
```

## 📋 Maintenance

### Daily
- Monitor system metrics
- Check error logs
- Verify backups

### Weekly
- Update dependencies
- Security patches
- Performance tuning

### Monthly
- Database maintenance
- Log rotation
- Cost optimization review

## 🆘 Support

### Emergency Contacts
- DevOps team: devops@company.com
- Security team: security@company.com
- Product team: product@company.com

### Runbooks
- [Service Outage Response](docs/runbooks/outage.md)
- [Security Incident Response](docs/runbooks/security.md)
- [Performance Degradation](docs/runbooks/performance.md)

### Escalation Matrix
1. **Tier 1**: Basic troubleshooting (1-2 hours)
2. **Tier 2**: Complex issues (2-4 hours)
3. **Tier 3**: Critical incidents (immediate)
