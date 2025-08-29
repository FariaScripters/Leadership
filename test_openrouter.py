#!/usr/bin/env python3
"""
Test script for OpenRouter LLM integration
This script tests the OpenRouter LLM provider with free models
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.infrastructure.external.llm.llm_factory import LLMFactory
from app.core.config import get_settings

async def test_openrouter_integration():
    """Test the OpenRouter LLM integration"""
    print("🚀 Testing OpenRouter LLM Integration")
    print("=" * 50)
    
    # Check configuration
    settings = get_settings()
    print(f"✅ Configuration loaded")
    print(f"   Base URL: {settings.openrouter_base_url}")
    print(f"   Default Model: {settings.openrouter_default_model}")
    print(f"   Fallback Models: {len(settings.openrouter_fallback_models)}")
    
    if not settings.openrouter_api_key:
        print("❌ OpenRouter API key not found!")
        print("   Please set OPENROUTER_API_KEY in your .env file")
        print("   Get your free API key from: https://openrouter.ai/keys")
        return False
    
    print(f"✅ API key found: {settings.openrouter_api_key[:10]}...")
    
    # Test LLM factory
    print("\n🔧 Testing LLM Factory...")
    provider_info = LLMFactory.get_provider_info()
    print(f"   Provider: {provider_info['provider']}")
    print(f"   Has API Key: {provider_info['has_api_key']}")
    
    # Get free models
    print("\n📋 Available Free Models:")
    free_models = LLMFactory.get_free_models()
    for i, model in enumerate(free_models, 1):
        print(f"   {i}. {model}")
    
    # Test actual LLM call
    print("\n🤖 Testing LLM Response...")
    llm = LLMFactory.create_llm()
    
    test_messages = [
        {"role": "user", "content": "Hello! Can you briefly explain what leadership means to you?"}
    ]
    
    try:
        response = await llm.ask(test_messages, temperature=0.7)
        
        if "Error:" in response.get("content", ""):
            print(f"❌ LLM Error: {response['content']}")
            return False
        
        print("✅ LLM Response received successfully!")
        print(f"   Model used: {response.get('model_used', 'unknown')}")
        print(f"   Response preview: {response['content'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM Test failed: {str(e)}")
        return False

async def test_model_fallback():
    """Test the model fallback mechanism"""
    print("\n🔄 Testing Model Fallback...")
    
    llm = LLMFactory.create_llm()
    
    # Test with a non-existent model to trigger fallback
    original_models = llm.fallback_models
    llm.fallback_models = ["non-existent-model-123"] + original_models
    
    test_messages = [
        {"role": "user", "content": "Say 'fallback test successful' if you can read this."}
    ]
    
    try:
        response = await llm.ask(test_messages)
        
        if "Error:" in response.get("content", ""):
            print("❌ Fallback test failed - all models failed")
            return False
        
        print("✅ Fallback mechanism working!")
        print(f"   Successfully used: {response.get('model_used', 'unknown')}")
        
        # Restore original models
        llm.fallback_models = original_models
        return True
        
    except Exception as e:
        print(f"❌ Fallback test failed: {str(e)}")
        return False

async def main():
    """Main test runner"""
    print("OpenRouter LLM Integration Test")
    print("=" * 50)
    
    # Run tests
    basic_test = await test_openrouter_integration()
    if basic_test:
        fallback_test = await test_model_fallback()
        
        if fallback_test:
            print("\n🎉 All tests passed! OpenRouter integration is working correctly.")
            print("\nNext steps:")
            print("1. Copy .env.template to .env and add your OpenRouter API key")
            print("2. Run your application - it will use free models by default")
            print("3. Monitor logs for any issues with model availability")
        else:
            print("\n⚠️  Basic integration works but fallback mechanism has issues")
    else:
        print("\n❌ Integration test failed. Please check your configuration.")

if __name__ == "__main__":
    asyncio.run(main())
