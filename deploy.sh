#!/bin/bash

# Scientific AI Orchestrator - Deployment Script
# This script helps you deploy to Render.com

echo "🚀 Scientific AI Orchestrator - Deployment Script"
echo "================================================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: Scientific AI Orchestrator"
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Check if remote exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo ""
    echo "🔗 Please add your GitHub repository as remote:"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/scientific-ai-orchestrator.git"
    echo ""
    echo "Then run: git push -u origin main"
    echo ""
else
    echo "✅ Remote origin already configured"
    echo ""
    echo "📤 Pushing to GitHub..."
    git add .
    git commit -m "Update: Ready for Render deployment"
    git push origin main
    echo "✅ Code pushed to GitHub"
fi

echo ""
echo "🎯 Next Steps:"
echo "=============="
echo ""
echo "1. Go to https://render.com"
echo "2. Click 'New Blueprint Instance'"
echo "3. Connect your GitHub repository"
echo "4. Render will auto-detect render.yaml"
echo "5. Set environment variables:"
echo "   - OPENAI_API_KEY: Your actual OpenAI API key"
echo "   - CORS_ORIGINS: Update with your Vercel domain"
echo ""
echo "6. Deploy and test:"
echo "   curl https://orchestrator-api.onrender.com/health"
echo ""
echo "7. Deploy frontend to Vercel:"
echo "   - Upload frontend-example.html as index.html"
echo "   - Set VITE_API_URL environment variable"
echo ""
echo "🎉 Your Scientific AI Orchestrator will be live!"
echo ""
echo "📊 Monitor your deployment:"
echo "   - API: https://orchestrator-api.onrender.com/docs"
echo "   - Health: https://orchestrator-api.onrender.com/health"
echo "" 