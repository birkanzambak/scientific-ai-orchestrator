# 🚀 Deployment Checklist - 7-Day Beta Plan

## Day 1-2: Backend + Worker on Render

### ✅ Pre-deployment Setup
- [x] `render.yaml` blueprint created
- [x] Dockerfile optimized for Render
- [x] Health check endpoint enhanced
- [x] Environment variables configured
- [x] CORS origins set for Vercel

### 🔄 Deployment Steps

#### 1. Push to GitHub
```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit: Scientific AI Orchestrator"

# Add remote and push
git remote add origin https://github.com/yourusername/scientific-ai-orchestrator.git
git push -u origin main
```

#### 2. Deploy on Render
1. Go to [render.com](https://render.com)
2. Click "New Blueprint Instance"
3. Connect your GitHub repository
4. Render will auto-detect `render.yaml`
5. Set environment variables:
   - `OPENAI_API_KEY`: Your actual OpenAI API key
   - `CORS_ORIGINS`: Update with your actual Vercel domain

#### 3. Verify Deployment
- [ ] API health check: `https://orchestrator-api.onrender.com/health`
- [ ] OpenAPI docs: `https://orchestrator-api.onrender.com/docs`
- [ ] Worker logs show no errors
- [ ] Redis connection working

#### 4. Test End-to-End
```bash
# Test question submission
curl -X POST https://orchestrator-api.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Why do stars explode?"}'

# Should return: {"task_id": "uuid-here"}
```

## Day 3: React Frontend on Vercel

### Frontend Setup
1. Create React app (if not exists):
```bash
npx create-react-app frontend
cd frontend
```

2. Add environment variable:
```bash
# .env
VITE_API_URL=https://orchestrator-api.onrender.com
```

3. Update API integration:
```javascript
// src/api.js
const API_URL = import.meta.env.VITE_API_URL;

export const submitQuestion = async (question) => {
  const response = await fetch(`${API_URL}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question })
  });
  
  return response.json();
};

export const getResult = async (taskId) => {
  const response = await fetch(`${API_URL}/result/${taskId}`);
  return response.json();
};

export const streamProgress = (taskId, onUpdate) => {
  const eventSource = new EventSource(`${API_URL}/stream/${taskId}`);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onUpdate(data);
  };
  
  return eventSource;
};
```

### Deploy to Vercel
1. Push frontend to GitHub
2. Connect to Vercel
3. Set environment variable: `VITE_API_URL`
4. Deploy

### Test CORS
- [ ] Frontend can submit questions
- [ ] SSE streaming works
- [ ] No CORS errors in browser console

## Day 4-5: Beta Cohort

### Invite Template
```
Hi [Name],

You're invited to test the Scientific AI Orchestrator (alpha).

What you get: 50 free queries that return evidence-linked answers + research roadmaps.

How:
1. Go to https://your-app.vercel.app
2. Ask a deep question (e.g., "How could room-temperature superconductivity be verified?")
3. When the result appears, click 👍/👎 and leave a note

What we track: anonymous usage metrics, no personal data.

Thank you!
—[Your Name]
```

### Feedback System
Add to API:
```python
@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Submit user feedback."""
    # Store in database or Google Form
    return {"status": "submitted"}
```

## Day 6-7: Launch Polish & Publicity

### Monitoring Setup
1. **Sentry** (Error tracking):
```bash
pip install sentry-sdk
```

```python
# main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()]
)
```

2. **Analytics** (Vercel Analytics or PostHog)

### Launch Content
1. **Medium/Hashnode Post**:
   - Title: "Building a Scientific AI Orchestrator: From Concept to Production"
   - Include: GIF of live SSE stream + JSON output
   - Call-to-action: "Try free (50 queries)"

2. **Tweet Thread**:
   ```
   1️⃣ Pain: Literature review overload
   2️⃣ Demo: [GIF of live stream]
   3️⃣ Solution: Evidence-grounded answers with roadmaps
   4️⃣ Try free: https://your-app.vercel.app
   ```

3. **Hacker News**:
   - Title: "Show HN: Scientific AI Orchestrator – evidence-grounded answers with roadmaps"
   - Include demo link and technical details

## 📊 Success Metrics Tracking

### Week 1 Targets
- [ ] **Signup → first answer**: >80%
- [ ] **Median answer time**: <40s
- [ ] **Citations per answer**: ≥3 average
- [ ] **Positive feedback rate**: >70% 👍
- [ ] **Cost per answer**: ≤$0.03

### Tracking Setup
Create Notion page or simple dashboard:
```
Date | Users | Queries | Avg Time | Avg Citations | Feedback Score | Cost/Query
-----|-------|---------|----------|---------------|----------------|-----------
```

## 🛠️ Fast-Follow Features

### 1. Vector Cache (Week 2)
```python
# Add to requirements.txt
pgvector==0.2.3
psycopg2-binary==2.9.7

# Cache arXiv embeddings
def cache_embedding(paper_id, embedding):
    # Store in pgvector
    pass
```

### 2. Weekly Digest (Week 3)
```python
# Celery beat task
@app.task
def weekly_digest():
    """Send weekly "What's new?" emails."""
    # Query new papers for saved keywords
    # Email bullet list to users
    pass
```

## 🔧 Troubleshooting

### Common Issues
1. **CORS errors**: Update `CORS_ORIGINS` in Render env vars
2. **Worker not starting**: Check Redis connection URL
3. **High costs**: Verify `COST_THRESHOLD` is set
4. **Slow responses**: Check worker concurrency settings

### Debug Commands
```bash
# Check API health
curl https://orchestrator-api.onrender.com/health

# Test question submission
curl -X POST https://orchestrator-api.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Test question"}'

# Check worker logs in Render dashboard
```

## 💰 Cost Monitoring

### Free Tier Limits
- **Render**: 750 run-hours/month per service
- **Vercel**: 100 GB-hours, 100 GB bandwidth
- **OpenAI**: Pay-as-you-go (set budget alerts)

### Budget Alerts
Set up alerts for:
- OpenAI spending > $50/month
- Render usage > 700 hours/month
- Vercel bandwidth > 90 GB/month

---

**Ready to deploy!** 🚀

Follow this checklist step-by-step for a smooth 7-day launch to beta users. 