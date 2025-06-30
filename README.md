# Scientific AI Orchestrator 🧬

A production-ready multi-agent AI system for comprehensive scientific question answering, featuring three specialized agents working in concert to provide evidence-based answers with research roadmaps.

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Clone and setup
git clone <your-repo>
cd orchestrator
cp env.example .env

# Edit .env with your OpenAI API key
OPENAI_API_KEY=your_actual_api_key_here
```

### 2. Install & Run
```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis (Docker)
docker run -d -p 6379:6379 redis:7-alpine

# Start API server
uvicorn app.main:app --reload

# Start worker (new terminal)
celery -A app.workers worker --loglevel=info
```

### 3. Test the System
```bash
# Run smoke test
python smoke_test.py

# Or test manually
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Why do stars explode?"}'
```

## 🏗️ Architecture

### Three-Agent Pipeline

1. **Sophia** 🧠 - Question Classification & Routing
   - Analyzes question type (factual, hypothesis, methodology)
   - Extracts keywords and domain
   - Routes to appropriate processing path

2. **Nova** 🔍 - Evidence Retrieval & Synthesis
   - Searches arXiv for relevant papers
   - Extracts key findings and evidence
   - Synthesizes multiple sources

3. **Lyra** ⚖️ - Reasoning & Analysis
   - Performs evidence-based reasoning
   - Identifies knowledge gaps
   - Generates research roadmap
   - Provides confidence scores

4. **Critic** 🔬 - Verification (Optional)
   - Reviews Lyra's analysis
   - Identifies missing points
   - Triggers re-analysis if needed

### Technology Stack

- **Backend**: FastAPI + Celery + Redis
- **AI**: OpenAI GPT-4o (with cost guard-rails)
- **Data**: arXiv API for scientific papers
- **Deployment**: Docker + Render/Railway ready
- **Documentation**: OpenAPI/Swagger

## ✨ Quick Wins Implemented

### ✅ Production-Ready Features

1. **Secrets Management**
   - Environment variables via `.env` file
   - Docker Compose `env_file` directive
   - No hardcoded secrets

2. **Robust Error Handling**
   - Tenacity retry logic (3 attempts, exponential backoff)
   - 30-60 second timeouts per agent
   - Graceful failure handling

3. **CORS & Frontend Ready**
   - FastAPI CORS middleware
   - Configurable origins
   - Ready for React/Vue integration

4. **Interactive Documentation**
   - Swagger UI at `/docs`
   - ReDoc at `/redoc`
   - Stakeholder-friendly API docs

5. **Cost Optimization**
   - Token estimation and cost tracking
   - Automatic downgrade to `gpt-4o-mini` if cost > $0.05
   - Configurable cost thresholds

## 📊 API Endpoints

### Core Endpoints
- `POST /ask` - Submit scientific question
- `GET /result/{task_id}` - Get analysis results
- `GET /stream/{task_id}` - Real-time progress (SSE)
- `GET /health` - Health check

### Interactive Docs
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc documentation

## 🔧 Configuration

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional
OPENAI_MODEL=gpt-4o-mini
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=["http://localhost:3000"]
COST_THRESHOLD=0.05
```

### Cost Guard-rails
- Automatic model downgrade based on estimated cost
- Token estimation for input/output
- Configurable cost thresholds per request

## 🚀 Deployment

### Local Development
```bash
# Quick test
python quick_test.py

# Full smoke test
python smoke_test.py
```

### Production (Render.com)
1. Connect GitHub repository
2. Set environment variables
3. Deploy API and worker services
4. Connect frontend

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## 📈 Performance & Monitoring

### Health Checks
- Endpoint: `GET /health`
- Returns: `{"status": "healthy"}`
- Ready for load balancer integration

### Logging
- Celery worker logs with `--loglevel=info`
- FastAPI access logs
- Error tracking ready for Sentry

### Metrics
- Request/response times
- Task completion rates
- Cost tracking per request
- Error rates per agent

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app
```

### Integration Tests
```bash
# Smoke test
python smoke_test.py

# Quick dependency test
python quick_test.py
```

## 📋 Example Usage

### Submit Question
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What causes Alzheimer disease?"}'
```

### Poll Results
```bash
# Get task ID from response
task_id="your-task-id"

# Poll for results
curl http://localhost:8000/result/$task_id
```

### Stream Progress
```bash
# Real-time updates
curl http://localhost:8000/stream/$task_id
```

## 🎯 Beta Testing Plan

### Week 1: Infrastructure
- [x] Deploy to production
- [x] Set up monitoring
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

## 💰 Cost Estimates

### Development Phase
- OpenAI tokens: ~$5-10
- Hosting: Free tier (Render/Railway)
- **Total: < $15**

### Production Phase (1000 queries/month)
- OpenAI tokens: ~$50-100/month
- Hosting: $7-15/month
- **Total: ~$60-120/month**

## 🔮 Roadmap

### Immediate (Week 1)
- [x] Production deployment
- [ ] Frontend integration
- [ ] Beta user testing

### Short-term (Month 1)
- [ ] Vector memory (pgvector/Chroma)
- [ ] Multi-source retrieval (PubMed + arXiv)
- [ ] Authentication layer
- [ ] Scheduled refresh

### Long-term (Quarter 1)
- [ ] Advanced analytics
- [ ] User management
- [ ] Enterprise features
- [ ] API marketplace

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Documentation**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

**Ready for production deployment!** 🚀

The system is production-ready with all quick wins implemented, comprehensive testing, and deployment guides. Perfect for beta testing with academic users. 