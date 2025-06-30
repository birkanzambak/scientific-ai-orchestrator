# Scientific AI Orchestrator - Deployment Guide

## Quick Wins Implemented ✅

### 1. Secrets Management
- ✅ Environment variables loaded from `.env` file
- ✅ Docker Compose uses `env_file` directive
- ✅ No hardcoded secrets in code

### 2. Timeouts & Retry Logic
- ✅ Tenacity retry decorators on all OpenAI/arXiv calls
- ✅ 30-60 second timeouts per agent
- ✅ Exponential backoff for failed requests

### 3. CORS Configuration
- ✅ FastAPI CORS middleware configured
- ✅ Configurable origins via `CORS_ORIGINS` env var
- ✅ Ready for frontend integration

### 4. OpenAPI Documentation
- ✅ Interactive Swagger docs at `/docs`
- ✅ ReDoc at `/redoc`
- ✅ Proper API documentation for stakeholders

### 5. Cost Guard-rails
- ✅ Token estimation in Lyra agent
- ✅ Automatic downgrade to `gpt-4o-mini` if cost > $0.05
- ✅ Configurable cost threshold

## Local Development Setup

### Prerequisites
- Python 3.8+
- Redis (via Docker or local install)
- OpenAI API key

### 1. Environment Setup
```bash
# Copy environment template
cp env.example .env

# Edit .env with your OpenAI API key
OPENAI_API_KEY=your_actual_api_key_here
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start Services
```bash
# Start Redis (Docker)
docker run -d -p 6379:6379 redis:7-alpine

# Or start Redis locally if installed
redis-server

# Start API server
uvicorn app.main:app --reload

# Start Celery worker (in new terminal)
celery -A app.workers worker --loglevel=info
```

### 4. Run Smoke Test
```bash
python smoke_test.py
```

## Production Deployment

### Option 1: Render.com (Recommended)

#### Backend API
1. Create new Web Service
2. Connect GitHub repository
3. Set environment variables:
   ```
   OPENAI_API_KEY=your_key
   REDIS_URL=your_redis_url
   CORS_ORIGINS=["https://your-frontend.vercel.app"]
   ```
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

#### Celery Worker
1. Create new Background Worker
2. Same repository and env vars
3. Start command: `celery -A app.workers worker --loglevel=info`

#### Redis
1. Create Redis instance
2. Use provided connection URL

### Option 2: Railway

#### All-in-one deployment
1. Connect GitHub repository
2. Railway auto-detects Docker Compose
3. Set environment variables in dashboard
4. Deploy automatically

### Option 3: DigitalOcean App Platform

#### Backend
1. Create App from GitHub
2. Select Python runtime
3. Set environment variables
4. Configure health check: `/health`

#### Worker
1. Create separate App for worker
2. Same repository, different start command

## Frontend Integration

### React Setup
```javascript
// Example API integration
const submitQuestion = async (question) => {
  const response = await fetch('https://your-api.render.com/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question })
  });
  
  const { task_id } = await response.json();
  
  // Poll for results
  const pollResult = async () => {
    const result = await fetch(`https://your-api.render.com/result/${task_id}`);
    const data = await result.json();
    
    if (data.status === 'completed') {
      return data;
    }
    
    setTimeout(pollResult, 3000);
  };
  
  return pollResult();
};
```

### SSE Streaming (Real-time)
```javascript
const streamProgress = (taskId) => {
  const eventSource = new EventSource(`https://your-api.render.com/stream/${taskId}`);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Progress:', data);
  };
};
```

## Monitoring & Observability

### Health Checks
- Endpoint: `GET /health`
- Returns: `{"status": "healthy"}`
- Use for load balancer health checks

### Logging
- Celery worker logs with `--loglevel=info`
- FastAPI access logs enabled
- Error tracking recommended (Sentry)

### Metrics
- Request/response times
- Task completion rates
- Error rates per agent
- Cost tracking per request

## Security Considerations

### API Security
- ✅ CORS properly configured
- ✅ No secrets in code
- ✅ Input validation via Pydantic
- 🔄 Rate limiting (implement per-user)
- 🔄 Authentication (implement for SaaS)

### Data Security
- ✅ No sensitive data logged
- ✅ Temporary task storage (in-memory for demo)
- 🔄 Persistent storage with encryption
- 🔄 Data retention policies

## Cost Optimization

### Current Guard-rails
- ✅ Automatic model downgrade
- ✅ Token estimation
- ✅ Configurable cost thresholds

### Additional Optimizations
- 🔄 Vector caching (pgvector/Chroma)
- 🔄 Multi-source retrieval
- 🔄 Async OpenAI client
- 🔄 Request batching

## Beta Testing Plan

### Week 1: Infrastructure
- [ ] Deploy to production
- [ ] Set up monitoring
- [ ] Test with 10-20 queries

### Week 2: User Testing
- [ ] Invite 3 PhD/post-doc users
- [ ] Give each 50 queries
- [ ] Collect feedback

### Week 3: Iteration
- [ ] Fix biggest UX issues
- [ ] Optimize performance
- [ ] Add missing features

### Week 4: Launch
- [ ] Publish walk-through video
- [ ] Blog post on implementation
- [ ] Share on r/MachineLearning & X

## Expected Costs

### Development Phase
- OpenAI tokens: ~$5-10
- Hosting: Free tier (Render/Railway)
- Total: < $15

### Production Phase
- OpenAI tokens: ~$50-100/month (1000 queries)
- Hosting: $7-15/month
- Monitoring: Free tier
- Total: ~$60-120/month

## Troubleshooting

### Common Issues

#### Redis Connection
```bash
# Check Redis is running
redis-cli ping

# Should return: PONG
```

#### Celery Worker
```bash
# Check worker status
celery -A app.workers inspect active

# Restart worker
celery -A app.workers control shutdown
```

#### OpenAI API
```bash
# Test API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

#### CORS Issues
```bash
# Check CORS headers
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS https://your-api.com/ask
```

## Next Steps

### Immediate (Week 1)
1. Deploy to production
2. Connect frontend
3. Run beta tests

### Short-term (Month 1)
1. Vector memory implementation
2. Multi-source retrieval
3. Authentication layer
4. Scheduled refresh

### Long-term (Quarter 1)
1. Advanced analytics
2. User management
3. Enterprise features
4. API marketplace 