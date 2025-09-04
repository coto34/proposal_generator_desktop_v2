#!/usr/bin/env python3
"""
Script to detect which Claude models you have access to.
Run this to find your exact model name.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_claude_model(api_key, model_name):
    """Test if a specific Claude model is accessible"""
    try:
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        
        data = {
            "model": model_name,
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "Hello"}],
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return True, "Success"
        elif response.status_code == 404:
            return False, "Model not found"
        elif response.status_code == 401:
            return False, "Authentication failed"
        elif response.status_code == 403:
            return False, "No access to this model"
        else:
            return False, f"Error {response.status_code}: {response.text[:100]}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def main():
    api_key = os.getenv("SONNET_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("❌ Neither SONNET_API_KEY nor ANTHROPIC_API_KEY found in environment variables")
        print("Make sure your .env file contains either:")
        print("  SONNET_API_KEY=your_key_here")
        print("  OR")
        print("  ANTHROPIC_API_KEY=your_key_here")
        return
    
    print("🔍 Testing Claude model access...")
    print(f"API Key: {api_key[:8]}...{api_key[-8:] if len(api_key) > 16 else 'short'}")
    print("-" * 60)
    
    # List of possible Claude model names
    models_to_test = [
        # Claude 4 variants (Sonnet 4)
        "claude-sonnet-4-20250514",
        "claude-4-sonnet-20250514",
        "claude-sonnet-4",
        "claude-4-sonnet",
        
        # Claude 3.5 Sonnet variants
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-20240620",
        "claude-3.5-sonnet-20241022",
        "claude-3.5-sonnet-20240620",
        
        # Claude 3 variants
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-3-opus-20240229",
        
        # Generic names
        "claude-sonnet",
        "claude-haiku",
        "claude-opus"
    ]
    
    working_models = []
    
    for model in models_to_test:
        print(f"Testing {model}...", end=" ")
        success, message = test_claude_model(api_key, model)
        
        if success:
            print(f"✅ WORKS")
            working_models.append(model)
        else:
            print(f"❌ {message}")
    
    print("-" * 60)
    
    if working_models:
        print(f"🎉 Found {len(working_models)} working model(s):")
        for model in working_models:
            print(f"   • {model}")
        
        print(f"\n💡 Use this model in your code: '{working_models[0]}'")
        
        # Generate the code snippet
        print("\n📝 Add this to your SonnetClient __init__:")
        print(f'    model: str = "{working_models[0]}",')
        
    else:
        print("❌ No working models found!")
        print("\nPossible issues:")
        print("   • Invalid API key")
        print("   • No Claude access on your account") 
        print("   • Network connectivity issues")
        print("   • Account billing issues")

if __name__ == "__main__":
    main()