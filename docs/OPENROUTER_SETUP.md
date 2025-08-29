# OpenRouter LLM Integration Setup Guide

This guide explains how to set up and use the OpenRouter LLM integration for free AI model access in the Leadership Assistant.

## Overview

The Leadership Assistant now supports OpenRouter as an alternative to direct Gemini API access. OpenRouter provides access to various free AI models including Google's Gemini Flash, Meta's Llama models, and others.

## Quick Start

### 1. Get Your Free API Key

1. Visit [OpenRouter](https://openrouter.ai/)
2. Sign up for a free account
3. Go to [API Keys](https://openrouter.ai/keys)
4. Create a new API key
5. Copy the key (starts with `sk-or-`)

### 2. Configure Environment

```bash
# Copy the template
cp .env.template .env

# Edit .env and add your OpenRouter API key
nano .env
```

Add your API key to the `.env` file:
```bash
OPENROUTER_API_KEY=sk-or-your-actual-key-here
```

### 3. Test the Integration

Run the test script to verify everything works:

```bash
python test_openrouter.py
```

## Available Free Models

The system is pre-configured with these free models:

1. **google/gemini-flash-1.5-8b** - Google's Gemini Flash (fast, good quality)
2. **meta-llama/llama-3.1-8b-instruct:free** - Meta's Llama 3.1 (open source)
3. **mistralai/mistral-7b-instruct:free** - Mistral's 7B model
4. **microsoft/phi-3-medium-128k-instruct:free** - Microsoft's Phi-3
5. **qwen/qwen-2-7b-instruct:free** - Alibaba's Qwen 2
6. **nousresearch/hermes-3-llama-3.1-8b:free** - Fine-tuned Llama variant

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key | Required |
| `OPENROUTER_BASE_URL` | OpenRouter API endpoint | `https://openrouter.ai/api/v1` |
| `OPENROUTER_DEFAULT_MODEL` | Primary model to use | `google/gemini-flash-1.5-8b` |

### Fallback Mechanism

The system automatically tries models in this order:
1. Default model (google/gemini-flash-1.5-8b)
2. Fallback models (all other free models)
3. Returns error if all models fail

## Usage in Code

### Basic Usage

```python
from app.infrastructure.external.llm.llm_factory import LLMFactory

# Create LLM instance
llm = LLMFactory.create_llm()

# Use it
messages = [{"role": "user", "content": "Hello!"}]
response = await llm.ask(messages)
print(response["content"])
```

### Check Provider Info

```python
from app.infrastructure.external.llm.llm_factory import LLMFactory

info = LLMFactory.get_provider_info()
print(f"Provider: {info['provider']}")
print(f"Default Model: {info['default_model']}")
print(f"Has API Key: {info['has_api_key']}")
```

### Get Available Models

```python
from app.infrastructure.external.llm.llm_factory import LLMFactory

free_models = LLMFactory.get_free_models()
print("Available free models:", free_models)
```

## Troubleshooting

### Common Issues

#### 1. "OpenRouter API key not found"
- Ensure `OPENROUTER_API_KEY` is set in your `.env` file
- Check that the key starts with `sk-or-`

#### 2. "All OpenRouter models failed"
- Check your internet connection
- Verify your API key is valid
- Try running the test script: `python test_openrouter.py`

#### 3. Rate Limiting
- Free models have rate limits
- The system automatically handles fallback between models
- Consider upgrading to paid models for higher usage

#### 4. Model Unavailability
- Free models may be temporarily unavailable
- The system tries all configured models automatically
- Check OpenRouter status page for outages

### Debug Mode

Enable debug logging to see detailed information:

```bash
export LOG_LEVEL=DEBUG
python test_openrouter.py
```

## Advanced Configuration

### Custom Model Selection

You can modify the default and fallback models in `app/core/config.py`:

```python
openrouter_default_model: str = "your-preferred-model"
openrouter_fallback_models: List[str] = ["model1", "model2", ...]
```

### Adding New Models

To add new free models, update the `get_free_models()` method in `OpenRouterLLM`:

```python
def get_free_models(self) -> List[str]:
    return [
        "google/gemini-flash-1.5-8b",
        "your-new-model:free",
        # ... other models
    ]
```

## Migration from Gemini

If you were previously using direct Gemini API:

1. **Replace Gemini API calls** with OpenRouter calls
2. **Update environment variables** from `GEMINI_API_KEY` to `OPENROUTER_API_KEY`
3. **Test thoroughly** with the provided test script

## Monitoring

### Check Model Usage

The system logs which model was used for each request:

```
INFO: Successfully used model: google/gemini-flash-1.5-8b
```

### Monitor API Limits

OpenRouter provides usage information in your dashboard:
- Visit https://openrouter.ai/usage
- Monitor your free tier usage
- Check rate limits for each model

## Support

- **OpenRouter Documentation**: https://openrouter.ai/docs
- **Model List**: https://openrouter.ai/models
- **API Reference**: https://openrouter.ai/docs#quick-start
- **Issues**: Create an issue in this repository for integration-specific problems

## Security Notes

- Never commit your API key to version control
- Use environment variables for sensitive configuration
- Rotate your API keys regularly
- Monitor your API usage for unexpected activity
