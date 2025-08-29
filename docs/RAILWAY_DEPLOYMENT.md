# Railway Deployment Guide

This guide provides step-by-step instructions for deploying the Leadership Assistant with OpenRouter integration to Railway.

## Prerequisites

1. Railway account (https://railway.app)
2. GitHub repository with your code
3. OpenRouter API key (get free at https://openrouter.ai/keys)

## Quick Deploy

### 1. Connect to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link your project
railway link
```

### 2. Environment Variables

Set these in Railway dashboard (Services > Settings > Variables):

```bash
# Required
OPENROUTER_API_KEY=sk-or-your-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_DEFAULT_MODEL=google/gemini-flash-1.5-8b

# Optional - Free fallback models
OPENROUTER_FALLBACK_MODELS=["meta-llama/llama-3.1-8b-instruct:free","mistralai/mistral-7b-instruct:free","microsoft/phi-3-medium-128k-instruct:free","qwen/qwen-2-7b-instruct:free","nousresearch/hermes-3-llama-3.1-8b:free"]

# Application settings
PORT=8000
ENVIRONMENT=production
```

### 3. Deploy

```bash
# Deploy from CLI
railway up

# Or use GitHub integration in Railway dashboard
```

## Manual Configuration

### Using Railway Dashboard

1. **Create New Project**
   - Go to https://railway.app/new
   - Select "Deploy from GitHub repo"
   - Choose your repository

2. **Configure Service**
   - **Root Directory**: `/` (leave empty for root)
   - **Builder**: Nixpacks (auto-detected)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Environment Variables**
   - Add all variables from the Quick Deploy section above

4. **Deploy**
   - Click "Deploy" to start the deployment

## Configuration Files

### railway.toml
The project includes a pre-configured `railway.toml` file with:
- Nixpacks builder configuration
- Health check endpoint
- Automatic restart on failure
- Environment-specific configurations

### Health Check
The application exposes a `/health` endpoint for Railway health checks.

## Troubleshooting

### Common Issues

1. **Build Fails**
   ```bash
   # Check logs
   railway logs
   
   # Ensure requirements.txt exists
   pip freeze > requirements.txt
   ```

2. **OpenRouter API Issues**
   - Verify API key is set correctly
   - Check OpenRouter status at https://status.openrouter.ai
   - Try different models in fallback list

3. **Memory Issues**
   - Railway free tier has 512MB RAM
   - Consider upgrading plan for larger models
   - Use smaller models in fallback list

### Monitoring

1. **Railway Dashboard**
   - View logs, metrics, and deployment status
   - Set up alerts for failures

2. **Health Checks**
   - Automatic health checks every 30 seconds
   - Failed checks trigger restart

## Scaling

### Horizontal Scaling
```toml
[deploy.multiRegionConfig]
us-west1 = { numReplicas = 2 }
us-east1 = { numReplicas = 2 }
```

### Vertical Scaling
- Upgrade Railway plan for more RAM/CPU
- Adjust model selection based on available resources

## Environment-Specific Configurations

### Production
- Uses optimized settings
- No debug mode
- Full model list

### Staging
- Includes `--reload` for development
- Uses same models as production

### PR Environments
- Isolated deployments for pull requests
- Uses production configuration

## Security Best Practices

1. **API Keys**
   - Never commit API keys to repository
   - Use Railway environment variables
   - Rotate keys regularly

2. **Network Security**
   - Railway provides automatic HTTPS
   - Consider Railway private networking for sensitive data

3. **Access Control**
   - Use Railway team features for collaboration
   - Set up proper GitHub repository permissions

## Cost Optimization

### Free Tier Usage
- Railway free tier includes 500 hours/month
- OpenRouter free models have generous rate limits
- Monitor usage in Railway dashboard

### Cost-Saving Tips
- Use smaller models when possible
- Implement caching for repeated queries
- Set up auto-scaling based on demand

## Support

- Railway Docs: https://docs.railway.com
- OpenRouter Docs: https://openrouter.ai/docs
- Issues: Create GitHub issue in your repository
